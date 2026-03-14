"""
跨域通信协议定义
所有域间消息必须经过网关验证和转换
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from enum import Enum


class DomainType(str, Enum):
    """三域标识"""
    LEARNER = "learner"      # 高信域
    GATEWAY = "gateway"      # 控制平面
    EDUCATION = "education"  # 低信域


class AgentType(str, Enum):
    """智能体类型"""
    A1_PROFILE = "a1_profile"          # 学生档案
    AG2_STYLE = "ag2_style"            # 学习风格识别
    AG3_TUTOR = "ag3_tutor"            # 自适应辅导
    AG4_CONTENT = "ag4_content"        # 内容挖掘
    AG5_ASSESS = "ag5_assess"          # 自适应评估


class PrivacyLevel(str, Enum):
    """隐私保护等级"""
    RAW = "raw"                    # 明文数据（仅学习者域）
    NOISY = "noisy"                # LDP噪声注入
    RECONSTRUCTED = "reconstructed"  # SRPG重构特征
    AGGREGATED = "aggregated"      # 聚合统计


class DataPermission(BaseModel):
    """动态RBAC权限令牌"""
    agent_id: AgentType
    resource_id: str
    privacy_level: PrivacyLevel
    granted_at: float  # Unix时间戳
    expires_at: float  # 过期时间
    access_count: int = 0
    max_access: int = 1  # 临时访问次数限制

    def is_valid(self) -> bool:
        """检查令牌是否有效"""
        import time
        now = time.time()
        return (now < self.expires_at and
                self.access_count < self.max_access)


class CrossDomainMessage(BaseModel):
    """跨域消息基类"""
    msg_id: str = Field(default_factory=lambda: f"msg_{id(object())}")
    source_domain: DomainType
    target_domain: DomainType
    source_agent: Optional[AgentType] = None
    target_agent: Optional[AgentType] = None
    payload: Dict[str, Any]
    permission: Optional[DataPermission] = None
    timestamp: float = Field(default_factory=lambda: __import__('time').time())

    class Config:
        json_schema_extra = {
            "example": {
                "source_domain": "learner",
                "target_domain": "education",
                "source_agent": "a1_profile",
                "target_agent": "ag2_style",
                "payload": {"features": [0.5, 0.3, ...]},
                "permission": {
                    "agent_id": "ag2_style",
                    "resource_id": "student_123_features",
                    "privacy_level": "reconstructed"
                }
            }
        }


class LearnerData(BaseModel):
    """学习者原始数据（仅A1接触）"""
    student_id: str
    demographic: Dict[str, Any] = {}  # 人口统计信息
    interaction_history: list = []    # 交互历史
    performance_records: list = []    # 学习表现
    raw_features: Dict[str, float] = {}

    class Config:
        json_schema_extra = {
            "example": {
                "student_id": "stu_20240313",
                "demographic": {"age": 15, "grade": 9},
                "raw_features": {"visual_score": 0.8, "auditory_score": 0.6}
            }
        }


class ProtectedFeatures(BaseModel):
    """SRPG保护后的特征（跨域传输）"""
    student_pseudonym: str  # 匿名化ID
    reconstructed_features: Dict[str, float]
    privacy_budget_used: float  # 已消耗隐私预算
    dp_epsilon: float = 1.0  # LDP参数

    class Config:
        json_schema_extra = {
            "example": {
                "student_pseudonym": "pseudo_abc123",
                "reconstructed_features": {"learning_style": 0.75, "difficulty": 0.5},
                "privacy_budget_used": 0.3
            }
        }


class AgentRequest(BaseModel):
    """智能体请求封装"""
    request_id: str
    agent_type: AgentType
    task_type: str  # 'diagnose', 'tutor', 'retrieve', 'assess'
    data: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """智能体响应封装"""
    request_id: str
    agent_type: AgentType
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}
