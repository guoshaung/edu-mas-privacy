"""
信息熵暴露量模块 (Information-Theoretic Exposure Tracker)

用香农熵替代模糊的"字段暴露量"，将 E_t 定义为：
    E_t = Σ_τ Σ_{f ∈ F_τ} w_f · e^{-λ(t-τ)}

其中：
    w_f  = 字段 f 的香农熵权重（归一化到 [0,1]）
    λ    = 时间衰减系数（默认 0.01，单位：秒）
    F_τ  = 第 τ 次交互中被读取的字段集合
"""
import math
import time
from typing import Dict, List


# ─────────────────────────────────────────────
# 字段信息熵权重表
# 计算方式：H(f) = -Σ p(v) log2 p(v)
# 均匀分布假设：H = log2(|domain|)
# 连续值字段用估算熵（基于实际分布区间数）
# ─────────────────────────────────────────────
_RAW_ENTROPY: Dict[str, float] = {
    # ── 身份类（高熵，直接标识符）──────────────────
    "student_id":        16.0,   # 全局唯一ID，熵最高
    "student_name":      12.0,   # 姓名空间大
    "gender":             1.0,   # log2(2) = 1 bit
    "class_name":         6.0,   # 班级数量约 64

    # ── 心理 / 行为类（中高熵，敏感属性）──────────
    "stress_level":       2.0,   # 4档：低/中/高/极高 → log2(4)
    "personality":        2.58,  # 约6种人格类型 → log2(6)
    "cognitive_level":    1.58,  # 3档 → log2(3)

    # ── 学习风格类（中熵）──────────────────────────
    "learning_style":     2.0,   # 4种风格 → log2(4)
    "style_tag":          1.58,  # 3类标签 → log2(3)

    # ── 学习表现类（中熵）──────────────────────────
    "recent_errors":      3.32,  # 连续值，约10个区间 → log2(10)
    "weak_kcs":           4.0,   # 知识点集合，约16个 → log2(16)
    "knowledge_points":   4.0,   # 同上
    "difficulty_level":   1.58,  # 3档 → log2(3)

    # ── 评估配置类（低熵，非个人敏感）──────────────
    "assessment_config":  1.0,   # 配置项有限
}

# 归一化：除以最大熵值，映射到 [0, 1]
_MAX_ENTROPY = max(_RAW_ENTROPY.values())
FIELD_ENTROPY_WEIGHT: Dict[str, float] = {
    f: round(h / _MAX_ENTROPY, 4)
    for f, h in _RAW_ENTROPY.items()
}

# 时间衰减系数（λ），单位：秒
# λ=0.01 → 约 70 秒后影响衰减到 50%
DECAY_LAMBDA: float = 0.01

# E_t 归一化上界（所有字段全部暴露时的理论最大值，不含衰减）
E_MAX: float = sum(FIELD_ENTROPY_WEIGHT.values())


class ExposureTracker:
    """
    累计信息暴露量追踪器

    每次 Agent 读取字段时调用 record_access()，
    调用 get_Et() 获取当前归一化暴露量 E_t ∈ [0, 1]。
    """

    def __init__(self, decay_lambda: float = DECAY_LAMBDA):
        self.decay_lambda = decay_lambda
        # 访问记录：[(timestamp, fields_accessed), ...]
        self._access_log: List[tuple] = []

    def record_access(self, fields: List[str]) -> float:
        """
        记录一次字段访问，返回本次新增的信息暴露量（未衰减）。
        fields: 本次被读取的字段名列表
        """
        ts = time.time()
        delta = sum(FIELD_ENTROPY_WEIGHT.get(f, 0.0) for f in fields)
        self._access_log.append((ts, fields))
        return delta

    def get_Et(self) -> float:
        """
        计算当前时刻的累计暴露量 E_t（归一化到 [0, 1]）

        E_t = (1 / E_MAX) · Σ_τ Σ_{f ∈ F_τ} w_f · e^{-λ(t-τ)}
        """
        if not self._access_log:
            return 0.0

        now = time.time()
        total = 0.0
        for ts, fields in self._access_log:
            elapsed = now - ts
            decay = math.exp(-self.decay_lambda * elapsed)
            total += sum(FIELD_ENTROPY_WEIGHT.get(f, 0.0) for f in fields) * decay

        return min(total / E_MAX, 1.0)

    def reset(self):
        """会话结束时重置"""
        self._access_log.clear()

    def summary(self) -> Dict:
        """返回当前暴露状态摘要（用于调试/展示）"""
        now = time.time()
        field_counts: Dict[str, int] = {}
        for _, fields in self._access_log:
            for f in fields:
                field_counts[f] = field_counts.get(f, 0) + 1

        return {
            "E_t": round(self.get_Et(), 4),
            "access_count": len(self._access_log),
            "field_exposure": {
                f: {
                    "count": cnt,
                    "entropy_weight": FIELD_ENTROPY_WEIGHT.get(f, 0.0),
                }
                for f, cnt in field_counts.items()
            },
        }
