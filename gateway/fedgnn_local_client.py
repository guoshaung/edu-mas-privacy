from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from math import sqrt
from statistics import mean, pstdev
from typing import Any, Iterable


SEMANTIC_BUCKETS = [
    "planning",
    "tutoring",
    "assessment",
    "diagnosis",
    "resource_request",
    "other",
]


@dataclass
class LocalEvent:
    timestamp: float
    payload_bytes: int
    semantic_bucket: str


@dataclass
class LocalFedGNNMonitor:
    student_id: str
    student_alias: str = "匿名学生"
    session_id: str = "default_session"
    current_phase: str = "Tutoring"
    current_topic: str = "General Topic"
    events: list[LocalEvent] = field(default_factory=list)

    def record_event(self, timestamp: float, payload_bytes: int, semantic_bucket: str) -> None:
        bucket = semantic_bucket if semantic_bucket in SEMANTIC_BUCKETS else "other"
        self.events.append(
            LocalEvent(
                timestamp=float(timestamp),
                payload_bytes=max(0, int(payload_bytes)),
                semantic_bucket=bucket,
            )
        )

    def extend_events(self, events: Iterable[dict[str, Any]]) -> None:
        for item in events:
            self.record_event(
                timestamp=float(item.get("timestamp", 0.0)),
                payload_bytes=int(item.get("payload_bytes", 0)),
                semantic_bucket=str(item.get("semantic_bucket", "other")),
            )

    def build_report(self, client_timestamp: int) -> dict[str, Any]:
        if not self.events:
            raise ValueError("No local events recorded for FedGNN report.")

        timestamps = sorted(event.timestamp for event in self.events)
        payloads = [event.payload_bytes for event in self.events]
        interval_list = [
            max(0.0, timestamps[index] - timestamps[index - 1])
            for index in range(1, len(timestamps))
        ]
        duration_seconds = max(1.0, timestamps[-1] - timestamps[0] if len(timestamps) > 1 else 1.0)
        semantic_counter = Counter(event.semantic_bucket for event in self.events)
        semantic_distribution = {
            bucket: semantic_counter.get(bucket, 0) / len(self.events)
            for bucket in SEMANTIC_BUCKETS
        }

        avg_interval = mean(interval_list) if interval_list else duration_seconds
        interval_std = pstdev(interval_list) if len(interval_list) > 1 else 0.0
        avg_payload = mean(payloads)
        payload_std = pstdev(payloads) if len(payloads) > 1 else 0.0

        gradient = self._estimate_local_gradient(
            duration_seconds=duration_seconds,
            message_count=len(self.events),
            avg_interval=avg_interval,
            interval_std=interval_std,
            avg_payload=avg_payload,
            payload_std=payload_std,
            semantic_distribution=semantic_distribution,
        )

        return {
            "session_id": self.session_id,
            "student_id": self.student_id,
            "student_alias": self.student_alias,
            "current_phase": self.current_phase,
            "current_topic": self.current_topic,
            "communication_stats": {
                "duration_seconds": round(duration_seconds, 4),
                "message_count": len(self.events),
                "avg_interval_seconds": round(avg_interval, 4),
                "interval_std_seconds": round(interval_std, 4),
                "avg_payload_bytes": round(avg_payload, 4),
                "payload_std_bytes": round(payload_std, 4),
            },
            "semantic_distribution": semantic_distribution,
            "local_gradient": gradient,
            "client_timestamp": int(client_timestamp),
        }

    @staticmethod
    def _estimate_local_gradient(
        duration_seconds: float,
        message_count: int,
        avg_interval: float,
        interval_std: float,
        avg_payload: float,
        payload_std: float,
        semantic_distribution: dict[str, float],
    ) -> list[float]:
        frequency = message_count / duration_seconds
        burstiness = interval_std / (avg_interval + 1e-6)
        magnitude = sqrt(avg_payload**2 + payload_std**2) / 1024.0

        gradient = [
            round(frequency, 6),
            round(burstiness, 6),
            round(avg_payload / 1024.0, 6),
            round(payload_std / 1024.0, 6),
            round(magnitude, 6),
            round(semantic_distribution.get("planning", 0.0), 6),
            round(semantic_distribution.get("tutoring", 0.0), 6),
            round(semantic_distribution.get("resource_request", 0.0), 6),
        ]
        return gradient
