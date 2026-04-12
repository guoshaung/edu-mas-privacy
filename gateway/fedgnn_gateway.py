from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import math
from statistics import mean
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field


router = APIRouter(prefix="/fedgnn", tags=["fedgnn"])


SEMANTIC_BUCKETS = [
    "planning",
    "tutoring",
    "assessment",
    "diagnosis",
    "resource_request",
    "other",
]


class CommunicationStats(BaseModel):
    duration_seconds: float = Field(..., ge=1.0)
    message_count: int = Field(..., ge=1)
    avg_interval_seconds: float = Field(..., ge=0.0)
    interval_std_seconds: float = Field(default=0.0, ge=0.0)
    avg_payload_bytes: float = Field(..., ge=0.0)
    payload_std_bytes: float = Field(default=0.0, ge=0.0)


class SemanticDistribution(BaseModel):
    planning: float = 0.0
    tutoring: float = 0.0
    assessment: float = 0.0
    diagnosis: float = 0.0
    resource_request: float = 0.0
    other: float = 0.0


class FedGNNClientPayload(BaseModel):
    session_id: str
    student_id: str
    student_alias: str = "匿名学生"
    current_phase: str = "Tutoring"
    current_topic: str = "General Topic"
    communication_stats: CommunicationStats
    semantic_distribution: SemanticDistribution
    local_gradient: List[float] = Field(default_factory=list)
    client_timestamp: int


class FedGNNReportResponse(BaseModel):
    session_id: str
    student_id: str
    risk_score: float
    reconstruction_error: float
    behavior_summary: str
    feature_snapshot: Dict[str, float]
    normal_pattern_center: Dict[str, float]
    updated_at: str


class FedGNNProfileResponse(BaseModel):
    student_id: str
    student_alias: str
    report_count: int
    risk_score: float
    reconstruction_error: float
    center_features: Dict[str, float]
    gradient_center: List[float]
    updated_at: str


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _normalize_semantics(distribution: SemanticDistribution) -> Dict[str, float]:
    raw = {bucket: float(getattr(distribution, bucket, 0.0)) for bucket in SEMANTIC_BUCKETS}
    total = sum(raw.values())
    if total <= 0:
        return {bucket: (1.0 if bucket == "other" else 0.0) for bucket in SEMANTIC_BUCKETS}
    return {bucket: raw[bucket] / total for bucket in SEMANTIC_BUCKETS}


def _extract_feature_vector(payload: FedGNNClientPayload) -> Dict[str, float]:
    stats = payload.communication_stats
    semantics = _normalize_semantics(payload.semantic_distribution)

    freq = _safe_div(stats.message_count, stats.duration_seconds)
    burstiness = _safe_div(stats.interval_std_seconds, stats.avg_interval_seconds + 1e-6)
    payload_cv = _safe_div(stats.payload_std_bytes, stats.avg_payload_bytes + 1.0)
    payload_density = _safe_div(stats.avg_payload_bytes * stats.message_count, stats.duration_seconds)

    features = {
        "msg_frequency": round(freq, 6),
        "burstiness": round(burstiness, 6),
        "avg_payload_kb": round(stats.avg_payload_bytes / 1024.0, 6),
        "payload_cv": round(payload_cv, 6),
        "payload_density": round(payload_density / 1024.0, 6),
    }
    for bucket, value in semantics.items():
        features[f"semantic_{bucket}"] = round(value, 6)
    return features


def _align_gradient(vector: List[float], target_length: int = 8) -> List[float]:
    if not vector:
        return [0.0] * target_length
    trimmed = [float(item) for item in vector[:target_length]]
    if len(trimmed) < target_length:
        trimmed.extend([0.0] * (target_length - len(trimmed)))
    return trimmed


def _weighted_mean(old: float, new: float, momentum: float) -> float:
    return momentum * old + (1.0 - momentum) * new


@dataclass
class FederatedBehaviorProfile:
    student_id: str
    student_alias: str
    count: int = 0
    center_features: Dict[str, float] = field(default_factory=dict)
    gradient_center: List[float] = field(default_factory=list)
    latest_risk_score: float = 0.0
    latest_reconstruction_error: float = 0.0
    updated_at: str = field(default_factory=_now_text)

    def update(self, feature_vector: Dict[str, float], gradient: List[float], momentum: float = 0.75) -> None:
        if not self.center_features:
            self.center_features = dict(feature_vector)
        else:
            self.center_features = {
                key: _weighted_mean(self.center_features.get(key, 0.0), value, momentum)
                for key, value in feature_vector.items()
            }

        if not self.gradient_center:
            self.gradient_center = list(gradient)
        else:
            self.gradient_center = [
                _weighted_mean(old, new, momentum)
                for old, new in zip(self.gradient_center, gradient)
            ]

        self.count += 1
        self.updated_at = _now_text()


class FederatedBehaviorStore:
    def __init__(self) -> None:
        self._profiles: Dict[str, FederatedBehaviorProfile] = {}
        self._session_to_student: Dict[str, str] = {}

    def ingest(self, payload: FedGNNClientPayload) -> FedGNNReportResponse:
        feature_vector = _extract_feature_vector(payload)
        gradient = _align_gradient(payload.local_gradient)

        profile = self._profiles.get(payload.student_id)
        if profile is None:
            profile = FederatedBehaviorProfile(
                student_id=payload.student_id,
                student_alias=payload.student_alias,
            )
            self._profiles[payload.student_id] = profile

        reconstruction_error = self._compute_reconstruction_error(profile.center_features, feature_vector)
        gradient_drift = self._compute_gradient_drift(profile.gradient_center, gradient)
        semantic_skew = feature_vector.get("semantic_resource_request", 0.0)
        payload_spike = feature_vector.get("avg_payload_kb", 0.0)
        burstiness = feature_vector.get("burstiness", 0.0)

        risk_score = self._compute_risk_score(
            reconstruction_error=reconstruction_error,
            gradient_drift=gradient_drift,
            semantic_skew=semantic_skew,
            payload_spike=payload_spike,
            burstiness=burstiness,
            count=profile.count,
        )

        profile.update(feature_vector, gradient)
        profile.latest_risk_score = risk_score
        profile.latest_reconstruction_error = reconstruction_error
        self._session_to_student[payload.session_id] = payload.student_id

        return FedGNNReportResponse(
            session_id=payload.session_id,
            student_id=payload.student_id,
            risk_score=risk_score,
            reconstruction_error=round(reconstruction_error, 4),
            behavior_summary=self._build_behavior_summary(
                payload.current_phase,
                payload.current_topic,
                risk_score,
                reconstruction_error,
            ),
            feature_snapshot=feature_vector,
            normal_pattern_center={key: round(value, 4) for key, value in profile.center_features.items()},
            updated_at=profile.updated_at,
        )

    def get_profile(self, student_id: str) -> Optional[FederatedBehaviorProfile]:
        return self._profiles.get(student_id)

    def get_profile_by_session(self, session_id: str) -> Optional[FederatedBehaviorProfile]:
        student_id = self._session_to_student.get(session_id)
        if not student_id:
            return None
        return self._profiles.get(student_id)

    def list_profiles(self) -> List[FedGNNProfileResponse]:
        profiles = []
        for profile in self._profiles.values():
            profiles.append(
                FedGNNProfileResponse(
                    student_id=profile.student_id,
                    student_alias=profile.student_alias,
                    report_count=profile.count,
                    risk_score=round(profile.latest_risk_score, 4),
                    reconstruction_error=round(profile.latest_reconstruction_error, 4),
                    center_features={k: round(v, 4) for k, v in profile.center_features.items()},
                    gradient_center=[round(value, 4) for value in profile.gradient_center],
                    updated_at=profile.updated_at,
                )
            )
        profiles.sort(key=lambda item: item.updated_at, reverse=True)
        return profiles

    @staticmethod
    def _compute_reconstruction_error(center: Dict[str, float], current: Dict[str, float]) -> float:
        if not center:
            return 0.08
        keys = sorted(current.keys())
        return mean(abs(current[key] - center.get(key, 0.0)) for key in keys)

    @staticmethod
    def _compute_gradient_drift(center: List[float], current: List[float]) -> float:
        if not center:
            return 0.1
        sq = [(cur - old) ** 2 for old, cur in zip(center, current)]
        return math.sqrt(sum(sq) / len(sq))

    @staticmethod
    def _compute_risk_score(
        reconstruction_error: float,
        gradient_drift: float,
        semantic_skew: float,
        payload_spike: float,
        burstiness: float,
        count: int,
    ) -> float:
        warmup_discount = 0.08 if count < 3 else 0.0
        score = (
            0.42 * _clamp(reconstruction_error * 2.8)
            + 0.23 * _clamp(gradient_drift * 2.2)
            + 0.15 * _clamp(semantic_skew * 1.6)
            + 0.10 * _clamp(payload_spike / 12.0)
            + 0.10 * _clamp(burstiness / 2.5)
            - warmup_discount
        )
        return round(_clamp(score), 4)

    @staticmethod
    def _build_behavior_summary(
        current_phase: str,
        current_topic: str,
        risk_score: float,
        reconstruction_error: float,
    ) -> str:
        level = "低风险"
        if risk_score >= 0.75:
            level = "高风险"
        elif risk_score >= 0.45:
            level = "中风险"
        return (
            f"当前阶段为 {current_phase}，主题为 {current_topic}。"
            f"云端根据本地上传的联邦行为摘要重构正常模式后，"
            f"得到重构误差 {reconstruction_error:.3f}，判定为 {level}。"
        )


fedgnn_store = FederatedBehaviorStore()


def get_fedgnn_risk_score_for_session(session_id: str, fallback: float = 0.2) -> float:
    profile = fedgnn_store.get_profile_by_session(session_id)
    if profile is None:
        return fallback
    return profile.latest_risk_score


@router.post("/report", response_model=FedGNNReportResponse)
async def report_federated_behavior(payload: FedGNNClientPayload) -> FedGNNReportResponse:
    return fedgnn_store.ingest(payload)


@router.get("/profiles")
async def list_federated_profiles() -> dict[str, Any]:
    return {
        "count": len(fedgnn_store.list_profiles()),
        "items": [item.model_dump() for item in fedgnn_store.list_profiles()],
        "updated_at": _now_text(),
    }


@router.get("/profiles/{student_id}", response_model=FedGNNProfileResponse)
async def get_federated_profile(student_id: str) -> FedGNNProfileResponse:
    profile = fedgnn_store.get_profile(student_id)
    if profile is None:
        return FedGNNProfileResponse(
            student_id=student_id,
            student_alias="匿名学生",
            report_count=0,
            risk_score=0.0,
            reconstruction_error=0.0,
            center_features={},
            gradient_center=[],
            updated_at=_now_text(),
        )
    return FedGNNProfileResponse(
        student_id=profile.student_id,
        student_alias=profile.student_alias,
        report_count=profile.count,
        risk_score=round(profile.latest_risk_score, 4),
        reconstruction_error=round(profile.latest_reconstruction_error, 4),
        center_features={k: round(v, 4) for k, v in profile.center_features.items()},
        gradient_center=[round(value, 4) for value in profile.gradient_center],
        updated_at=profile.updated_at,
    )
