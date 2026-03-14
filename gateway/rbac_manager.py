"""
动态RBAC管理器
基于业务状态机的临时数据降维授权
"""
import time
from enum import Enum
import redis
import json
from typing import Optional, Dict, List, Set
from protocols.messages import DataPermission, AgentType, PrivacyLevel


class BusinessState(str, Enum):
    """业务状态机"""
    IDLE = "idle"
    DIAGNOSING = "diagnosing"       # AG2诊断中
    TUTORING = "tutoring"           # AG3辅导中
    CONTENT_RETRIEVAL = "content"   # AG4检索中
    ASSESSING = "assessing"         # AG5评估中
    FINISHED = "finished"           # 会话结束


class DynamicRBACManager:
    """
    动态基于角色的访问控制管理器
    核心功能：
    1. 基于当前业务状态颁发临时权限令牌
    2. 授权时进行数据降维（只授予必需的最小数据集）
    3. 状态切换时自动吊销旧权限
    4. 记录所有访问行为审计日志
    """

    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        # Redis存储活跃权限令牌
        try:
            self.redis_client = redis.Redis(
                host=redis_host, port=redis_port, decode_responses=True
            )
            self.redis_client.ping()
        except Exception as e:
            print(f"Redis连接失败，使用内存存储: {e}")
            self.redis_client = None
            self.memory_store: Dict[str, DataPermission] = {}

        self.current_state = BusinessState.IDLE
        self.audit_log: List[Dict] = []

        # 状态-智能体映射（哪些智能体在哪些状态下活跃）
        self.state_agent_map: Dict[BusinessState, Set[AgentType]] = {
            BusinessState.DIAGNOSING: {AgentType.AG2_STYLE},
            BusinessState.TUTORING: {AgentType.AG3_TUTOR},
            BusinessState.CONTENT_RETRIEVAL: {AgentType.AG4_CONTENT},
            BusinessState.ASSESSING: {AgentType.AG5_ASSESS},
        }

        # 数据降维规则（每个智能体只能访问特定字段）
        self.data_view_rules: Dict[AgentType, List[str]] = {
            AgentType.AG2_STYLE: ["learning_style", "cognitive_level"],  # 学习风格识别
            AgentType.AG3_TUTOR: ["recent_errors", "style_tag", "weak_kcs"],  # 辅导
            AgentType.AG4_CONTENT: ["knowledge_points", "difficulty_level"],  # 内容检索
            AgentType.AG5_ASSESS: ["assessment_config"],  # 评估（不能读对话！）
        }

    def _store_permission(self, permission: DataPermission):
        """存储权限令牌"""
        if self.redis_client:
            key = f"perm:{permission.agent_id}:{permission.resource_id}"
            self.redis_client.setex(
                key,
                int(permission.expires_at - time.time()),
                permission.model_dump_json()
            )
        else:
            self.memory_store[f"{permission.agent_id}:{permission.resource_id}"] = permission

    def _get_permission(self, agent_id: AgentType, resource_id: str) -> Optional[DataPermission]:
        """获取权限令牌"""
        if self.redis_client:
            key = f"perm:{agent_id}:{resource_id}"
            data = self.redis_client.get(key)
            return DataPermission.model_validate_json(data) if data else None
        else:
            return self.memory_store.get(f"{agent_id}:{resource_id}")

    def _revoke_agent_permissions(self, agent_id: AgentType):
        """吊销某智能体的所有权限"""
        if self.redis_client:
            for key in self.redis_client.scan_iter(f"perm:{agent_id}:*"):
                self.redis_client.delete(key)
        else:
            keys_to_delete = [
                k for k in self.memory_store.keys()
                if k.startswith(f"{agent_id}:")
            ]
            for k in keys_to_delete:
                del self.memory_store[k]

        self._log_audit("revoke", agent_id, "all_permissions")

    def _log_audit(self, action: str, agent_id: AgentType, resource: str, details: Dict = None):
        """记录审计日志"""
        self.audit_log.append({
            "timestamp": time.time(),
            "action": action,
            "agent_id": agent_id,
            "resource": resource,
            "state": self.current_state,
            "details": details or {}
        })

    def transition_state(self, new_state: BusinessState) -> bool:
        """
        状态机切换
        - 吊销旧状态智能体的权限
        - 为新状态智能体预授权（可选）
        """
        old_state = self.current_state

        # 吊销旧状态智能体的权限
        if old_state in self.state_agent_map:
            for agent in self.state_agent_map[old_state]:
                self._revoke_agent_permissions(agent)

        self.current_state = new_state
        self._log_audit("state_transition", "system", f"{old_state}→{new_state}")

        return True

    def grant_permission(
        self,
        agent_id: AgentType,
        resource_id: str,
        privacy_level: PrivacyLevel,
        ttl_seconds: float = 300.0,  # 默认5分钟
        max_access: int = 10
    ) -> Optional[DataPermission]:
        """
        颁发临时权限令牌
        检查：
        1. 智能体是否在当前状态允许列表中
        2. 请求数据是否符合数据降维规则
        """
        # 1. 检查智能体是否在当前状态活跃
        if self.current_state not in self.state_agent_map:
            return None
        if agent_id not in self.state_agent_map[self.current_state]:
            self._log_audit(
                "deny", agent_id, resource_id,
                {"reason": "agent_not_active_in_current_state"}
            )
            return None

        # 2. 检查数据降维规则（简化版：检查资源ID前缀）
        allowed_prefixes = self.data_view_rules.get(agent_id, [])
        # 实际实现应根据资源ID解析具体字段，这里简化处理

        # 3. 颁发令牌
        permission = DataPermission(
            agent_id=agent_id,
            resource_id=resource_id,
            privacy_level=privacy_level,
            granted_at=time.time(),
            expires_at=time.time() + ttl_seconds,
            max_access=max_access
        )

        self._store_permission(permission)
        self._log_audit("grant", agent_id, resource_id)

        return permission

    def check_permission(
        self,
        agent_id: AgentType,
        resource_id: str,
        required_level: PrivacyLevel = PrivacyLevel.RECONSTRUCTED
    ) -> bool:
        """检查智能体是否有权限访问资源"""
        permission = self._get_permission(agent_id, resource_id)

        if not permission:
            return False

        # 检查令牌有效性
        if not permission.is_valid():
            return False

        # 检查隐私级别
        level_hierarchy = {
            PrivacyLevel.RAW: 4,
            PrivacyLevel.NOISY: 3,
            PrivacyLevel.RECONSTRUCTED: 2,
            PrivacyLevel.AGGREGATED: 1
        }
        return level_hierarchy[permission.privacy_level] >= level_hierarchy[required_level]

    def consume_access(self, agent_id: AgentType, resource_id: str) -> bool:
        """消费一次访问次数"""
        permission = self._get_permission(agent_id, resource_id)
        if permission and permission.is_valid():
            permission.access_count += 1
            self._store_permission(permission)
            self._log_audit("consume", agent_id, resource_id)
            return True
        return False

    def get_active_permissions(self, agent_id: Optional[AgentType] = None) -> List[DataPermission]:
        """获取当前活跃的权限列表"""
        # 简化版实现，实际应从Redis扫描
        return []

    def emergency_revoke_all(self):
        """紧急情况：吊销所有权限"""
        if self.redis_client:
            for key in self.redis_client.scan_iter("perm:*"):
                self.redis_client.delete(key)
        else:
            self.memory_store.clear()

        self.current_state = BusinessState.IDLE
        self._log_audit("emergency_revoke", "system", "all_permissions")


# 单例模式
_rbac_instance: DynamicRBACManager = None


def get_rbac_manager() -> DynamicRBACManager:
    """获取RBAC管理器单例"""
    global _rbac_instance
    if _rbac_instance is None:
        _rbac_instance = DynamicRBACManager()
    return _rbac_instance
