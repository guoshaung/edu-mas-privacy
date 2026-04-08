"""Gateway package exports.

The legacy gateway modules depend on several optional services. We keep imports
best-effort here so new standalone flows such as the learning-planning gateway
can be imported without requiring every historical dependency to be installed.
"""

__all__ = []

try:
    from .privacy_engine import SRPGEngine, get_privacy_engine
    __all__ += ["SRPGEngine", "get_privacy_engine"]
except Exception:
    pass

try:
    from .rbac_manager import DynamicRBACManager, get_rbac_manager
    __all__ += ["DynamicRBACManager", "get_rbac_manager"]
except Exception:
    pass

try:
    from .gnn_guard import GNNGuard, get_gnn_guard
    __all__ += ["GNNGuard", "get_gnn_guard"]
except Exception:
    pass

try:
    from .router import PrivacyGateway, get_gateway
    __all__ += ["PrivacyGateway", "get_gateway"]
except Exception:
    pass
