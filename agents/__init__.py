"""智能体模块初始化。

这里尽量做容错导入，避免某个旧实验模块缺少可选依赖时把整个网关启动链路阻断。
"""

from .ag2_style import LearningStyleAgent, get_ag2_agent
from .ag3_tutor import AdaptiveTutorAgent, get_ag3_agent
from .ag5_assess import AssessmentAgent, get_ag5_agent

ContentMiningAgent = None
get_ag4_agent = None

try:
    from .ag4_content import ContentMiningAgent, get_ag4_agent
except Exception:
    # AG4 旧实现依赖可选向量库；当前原型允许缺席，不影响新网关和演示链路启动。
    ContentMiningAgent = None
    get_ag4_agent = None

__all__ = [
    "LearningStyleAgent",
    "AdaptiveTutorAgent",
    "AssessmentAgent",
    "get_ag2_agent",
    "get_ag3_agent",
    "get_ag5_agent",
]

if ContentMiningAgent is not None:
    __all__.extend(["ContentMiningAgent", "get_ag4_agent"])
