"""
SRPG / Privacy Engine

这个模块负责在零信任架构下对学生原始输入做双流处理：
1. 传统 protect 接口：兼容当前项目里已有的 SRPGEngine.protect 调用。
2. 新增 process_dual_stream_vector：将文本输入映射为“逻辑流图谱向量 + 隐私流向量”。

这里的实现偏工程 Demo：
- 逻辑流用高维向量模拟“图谱/语义编码”
- 隐私流用局部差分隐私（LDP）方式加噪
- 输出结构可直接被网关、AG3、AG5 后续模块消费
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from opacus.accountants import RDPAccountant

from gateway.exposure_entropy import ExposureTracker
from gateway.governance import PrivacyTrustConfig, compute_privacy_trust
from protocols.messages import LearnerData, ProtectedFeatures


class LatentReconstructionHead(nn.Module):
    """轻量重构头，兼容旧版 protect 流程。"""

    def __init__(self, input_dim: int = 64, hidden_dim: int = 128, output_dim: int = 32):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, output_dim),
        )
        self.decoder = nn.Sequential(
            nn.Linear(output_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        encoded = self.encoder(x)
        return self.decoder(encoded)

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        return self.encoder(x)


class SRPGEngine:
    """
    SRPG 核心引擎。

    现有职责：
    - 兼容旧版 protected_features 生成
    - 在零信任架构下提供双流向量化接口
    - 跟踪隐私预算与信息暴露强度
    """

    def __init__(
        self,
        input_dim: int = 64,
        hidden_dim: int = 128,
        output_dim: int = 32,
        epsilon: float = 1.0,
        delta: float = 1e-5,
        max_budget: float = 2.0,
    ):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.reconstruction_head = LatentReconstructionHead(input_dim, hidden_dim, output_dim).to(self.device)
        self.epsilon = float(epsilon)
        self.delta = float(delta)
        self.max_budget = float(max_budget)
        self.used_budget = 0.0
        self.accountant = RDPAccountant()
        self.pseudonym_map: Dict[str, str] = {}
        self.exposure_tracker = ExposureTracker()
        self.privacy_trust_config = PrivacyTrustConfig(t_base=1.0)

    def _generate_pseudonym(self, student_id: str) -> str:
        if student_id not in self.pseudonym_map:
            digest = hashlib.sha256(student_id.encode("utf-8")).hexdigest()
            self.pseudonym_map[student_id] = f"pseudo_{digest[:12]}"
        return self.pseudonym_map[student_id]

    def _normalize_features(self, raw_features: Dict[str, float]) -> torch.Tensor:
        if not raw_features:
            return torch.zeros(64, dtype=torch.float32)

        values = torch.tensor(list(raw_features.values()), dtype=torch.float32)
        if values.numel() < 64:
            values = torch.nn.functional.pad(values, (0, 64 - values.numel()))
        elif values.numel() > 64:
            values = values[:64]
        return values / (torch.norm(values) + 1e-8)

    def _add_laplace_noise_tensor(self, data: torch.Tensor, epsilon: Optional[float] = None, sensitivity: float = 1.0) -> torch.Tensor:
        current_epsilon = float(epsilon if epsilon is not None else self.epsilon)
        safe_epsilon = max(current_epsilon, 1e-4)
        scale = sensitivity / safe_epsilon
        noise = torch.distributions.Laplace(0.0, scale).sample(data.shape).to(data.device)
        return data + noise

    def _add_laplace_noise_numpy(self, vector: np.ndarray, epsilon: Optional[float] = None, sensitivity: float = 1.0) -> np.ndarray:
        current_epsilon = float(epsilon if epsilon is not None else self.epsilon)
        safe_epsilon = max(current_epsilon, 1e-4)
        scale = sensitivity / safe_epsilon
        noise = np.random.laplace(loc=0.0, scale=scale, size=vector.shape)
        return vector + noise

    def _seed_from_text(self, text_input: str, namespace: str) -> int:
        """让同一段输入在 Demo 里得到稳定向量，便于重复演示。"""
        digest = hashlib.sha256(f"{namespace}:{text_input}".encode("utf-8")).hexdigest()
        return int(digest[:16], 16) % (2**32)

    def process_dual_stream_vector(self, text_input: str, epsilon: Optional[float] = None) -> Dict[str, List[float]]:
        """
        对文本输入做“双流向量化处理”。

        处理流程：
        1. 模拟 GCN/图编码：将文本映射为 128 维逻辑流向量。
        2. 模拟 LDP 隐私流：生成 64 维隐私流向量，并注入拉普拉斯噪声。
        3. 返回可直接传输的列表结构。

        这里代表的是“零信任架构下的隐空间特征提取与 LDP 加噪”：
        - 逻辑流保留任务语义，服务后续规划/辅导/检索
        - 隐私流保留个体特征摘要，但在本地先做差分隐私扰动
        """
        used_epsilon = float(epsilon if epsilon is not None else self.epsilon)

        # 第一步：模拟高维逻辑流图谱编码
        logic_rng = np.random.default_rng(self._seed_from_text(text_input, "logic"))
        logic_graph_vector = logic_rng.normal(loc=0.0, scale=1.0, size=128).astype(np.float32)

        # 第二步：模拟 64 维隐私流，并注入拉普拉斯噪声
        privacy_rng = np.random.default_rng(self._seed_from_text(text_input, "privacy"))
        privacy_vector = privacy_rng.normal(loc=0.0, scale=1.0, size=64).astype(np.float32)
        noisy_privacy_vector = self._add_laplace_noise_numpy(privacy_vector, epsilon=used_epsilon).astype(np.float32)

        return {
            "noisy_privacy_vector": noisy_privacy_vector.tolist(),
            "logic_graph_vector": logic_graph_vector.tolist(),
        }

    def protect(self, learner_data: LearnerData, accessed_fields: Optional[List[str]] = None) -> Tuple[ProtectedFeatures, float]:
        """
        兼容旧接口：把 learner_data.raw_features 压到重构特征空间里。
        """
        if self.used_budget >= self.max_budget:
            raise ValueError("隐私预算已耗尽，拒绝处理新的请求。")

        feature_tensor = self._normalize_features(learner_data.raw_features).to(self.device)

        with torch.no_grad():
            encoded = self.reconstruction_head.encode(feature_tensor)

        noisy_encoded = self._add_laplace_noise_tensor(encoded, epsilon=self.epsilon)
        protected_dict = {f"latent_{idx}": float(noisy_encoded[idx].item()) for idx in range(noisy_encoded.shape[0])}

        cost = self.epsilon / 10.0
        try:
            self.accountant.step(noise_multiplier=1.0 / max(self.epsilon, 1e-4), sample_rate=1.0)
        except Exception:
            pass
        self.used_budget += cost

        pseudonym = self._generate_pseudonym(learner_data.student_id)
        fields = accessed_fields if accessed_fields is not None else list(learner_data.raw_features.keys())
        self.exposure_tracker.record_access(fields)

        protected_features = ProtectedFeatures(
            student_pseudonym=pseudonym,
            reconstructed_features=protected_dict,
            privacy_budget_used=self.used_budget,
            dp_epsilon=self.epsilon,
        )
        return protected_features, cost

    def get_Et(self) -> float:
        return self.exposure_tracker.get_Et()

    def compute_privacy_trust(
        self,
        duration_ratio: float,
        gnn_risk_score: float,
    ) -> Dict[str, Any]:
        """
        真正落地的动态隐私信任计算入口。

        - T_base 由 self.privacy_trust_config.t_base 提供
        - D_t 由外部传入 duration_ratio
        - R_gnn 由外部传入 gnn_risk_score
        - E_t 由 exposure_tracker 动态给出
        """
        return compute_privacy_trust(
            duration_ratio=duration_ratio,
            gnn_risk_score=gnn_risk_score,
            exposure_strength=self.get_Et(),
            config=self.privacy_trust_config,
        )

    def get_privacy_trust_snapshot(
        self,
        duration_ratio: float,
        gnn_risk_score: float,
    ) -> Dict[str, Any]:
        snapshot = self.compute_privacy_trust(duration_ratio=duration_ratio, gnn_risk_score=gnn_risk_score)
        snapshot["used_budget"] = round(self.used_budget, 4)
        snapshot["remaining_budget"] = round(self.get_remaining_budget(), 4)
        return snapshot

    def get_exposure_summary(self) -> Dict[str, Any]:
        return self.exposure_tracker.summary()

    def get_remaining_budget(self) -> float:
        return max(0.0, self.max_budget - self.used_budget)

    def reset_budget(self) -> None:
        self.used_budget = 0.0
        self.accountant = RDPAccountant()
        self.exposure_tracker.reset()


# 给用户请求中的命名一个兼容别名，避免外部按 PrivacyEngine 寻址时报错
PrivacyEngine = SRPGEngine

_engine_instance: Optional[SRPGEngine] = None


def get_privacy_engine() -> SRPGEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = SRPGEngine()
    return _engine_instance
