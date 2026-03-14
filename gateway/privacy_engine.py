"""
SRPG (Semantic Reconstruction Privacy Gateway) 引擎
负责：LDP噪声注入 + 隐空间重构 + 隐私预算管理
"""
import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Any, Tuple
from opacus.accountants import RDPAccountant
from protocols.messages import LearnerData, ProtectedFeatures


class LatentReconstructionHead(nn.Module):
    """轻量级重构头：将隐私特征映射到可用语义空间"""

    def __init__(self, input_dim: int = 64, hidden_dim: int = 128, output_dim: int = 32):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, output_dim)
        )
        self.decoder = nn.Sequential(
            nn.Linear(output_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """前向传播：编码-解码重构"""
        encoded = self.encoder(x)
        reconstructed = self.decoder(encoded)
        return reconstructed

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """仅编码（用于输出保护特征）"""
        return self.encoder(x)


class SRPGEngine:
    """
    语义重构隐私网关引擎
    核心功能：
    1. 原始特征 → 隐空间编码
    2. 注入LDP噪声（本地差分隐私）
    3. 重构为可用语义特征
    4. 追踪隐私预算消耗
    """

    def __init__(
        self,
        input_dim: int = 64,
        hidden_dim: int = 128,
        output_dim: int = 32,
        epsilon: float = 1.0,  # LDP隐私参数
        delta: float = 1e-5,
        max_budget: float = 2.0  # 总隐私预算上限
    ):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.reconstruction_head = LatentReconstructionHead(
            input_dim, hidden_dim, output_dim
        ).to(self.device)

        # LDP参数
        self.epsilon = epsilon
        self.delta = delta

        # 隐私预算记账器
        self.accountant = RDPAccountant()
        self.max_budget = max_budget
        self.used_budget = 0.0

        # 学生ID匿名化映射
        self.pseudonym_map: Dict[str, str] = {}

    def _generate_pseudonym(self, student_id: str) -> str:
        """生成匿名化标识符"""
        if student_id not in self.pseudonym_map:
            import hashlib
            hash_obj = hashlib.sha256(student_id.encode())
            self.pseudonym_map[student_id] = f"pseudo_{hash_obj.hexdigest()[:12]}"
        return self.pseudonym_map[student_id]

    def _add_laplace_noise(self, data: torch.Tensor, sensitivity: float = 1.0) -> torch.Tensor:
        """
        注入拉普拉斯噪声（本地差分隐私）
        noise ~ Laplace(0, sensitivity / epsilon)
        """
        scale = sensitivity / self.epsilon
        noise = torch.distributions.Laplace(0, scale).sample(data.shape).to(self.device)
        return data + noise

    def _normalize_features(self, raw_features: Dict[str, float]) -> torch.Tensor:
        """将字典特征归一化为张量"""
        # 简化版：直接转换并归一化
        values = torch.tensor(list(raw_features.values()), dtype=torch.float32)
        # L2归一化
        return values / (torch.norm(values) + 1e-8)

    def protect(
        self,
        learner_data: LearnerData
    ) -> Tuple[ProtectedFeatures, float]:
        """
        对学习者数据进行隐私保护处理
        返回：(保护后的特征, 消耗的隐私预算)
        """
        # 1. 检查隐私预算
        if self.used_budget >= self.max_budget:
            raise ValueError("隐私预算已耗尽！拒绝处理新请求。")

        # 2. 特征归一化
        feature_tensor = self._normalize_features(learner_data.raw_features).to(self.device)

        # 3. 隐空间编码
        with torch.no_grad():
            encoded = self.reconstruction_head.encode(feature_tensor)

        # 4. 注入LDP噪声
        noisy_encoded = self._add_laplace_noise(encoded)

        # 5. 转回字典格式（简化版）
        protected_dict = {
            f"latent_{i}": noisy_encoded[i].item()
            for i in range(noisy_encoded.shape[0])
        }

        # 6. 计算消耗的隐私预算（RDP accountant）
        # 简化版：每次消耗 epsilon / 10
        cost = self.epsilon / 10.0
        try:
            self.accountant.step(
                noise_multiplier=1.0 / self.epsilon,
                sample_rate=1.0
            )
        except:
            pass  # 如果accountant失败，继续执行
        self.used_budget += cost

        # 7. 生成匿名化ID
        pseudonym = self._generate_pseudonym(learner_data.student_id)

        protected_features = ProtectedFeatures(
            student_pseudonym=pseudonym,
            reconstructed_features=protected_dict,
            privacy_budget_used=self.used_budget,
            dp_epsilon=self.epsilon
        )

        return protected_features, cost

    def get_remaining_budget(self) -> float:
        """获取剩余隐私预算"""
        return max(0, self.max_budget - self.used_budget)

    def reset_budget(self):
        """重置隐私预算（仅用于测试）"""
        self.used_budget = 0.0
        self.accountant = RDPAccountant()


# 单例模式
_engine_instance: SRPGEngine = None


def get_privacy_engine() -> SRPGEngine:
    """获取隐私引擎单例"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = SRPGEngine()
    return _engine_instance
