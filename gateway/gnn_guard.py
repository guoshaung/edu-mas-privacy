"""
G-safeguard: GNN拓扑防御模块
职责：实时监控多智能体交互图，检测和隔离异常行为
核心功能：
1. 构建智能体交互拓扑图
2. GNN节点嵌入学习
3. 异常流量检测（Prompt攻击、数据窃取尝试）
4. 动态链路剪枝（隔离污染源）
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, GATConv
from torch_geometric.data import Data, HeteroData
from typing import Dict, List, Tuple, Optional, Set
import numpy as np
from collections import defaultdict, deque
import time

from protocols.messages import AgentType, DomainType, CrossDomainMessage


class InteractionGraph:
    """
    智能体交互图（动态拓扑）
    节点：智能体、网关、数据资源
    边：通信、数据访问、权限授予
    """

    def __init__(self):
        # 节点集合
        self.nodes: Dict[str, Dict] = {}  # node_id -> {type, domain, metadata}
        self.edges: List[Tuple[str, str, str, float]] = []  # (src, dst, edge_type, weight)

        # 节点特征（用于GNN）
        self.node_features: Dict[str, np.ndarray] = {}

        # 交互历史（用于时序分析）
        self.interaction_history: deque = deque(maxlen=1000)

    def add_node(self, node_id: str, node_type: str, domain: str, metadata: Dict = None):
        """添加节点"""
        self.nodes[node_id] = {
            "type": node_type,
            "domain": domain,
            "metadata": metadata or {},
            "created_at": time.time()
        }

        # 初始化节点特征（简化版：one-hot编码）
        feature = self._encode_node_feature(node_type, domain)
        self.node_features[node_id] = feature

    def add_edge(self, src: str, dst: str, edge_type: str, weight: float = 1.0):
        """添加边（记录交互）"""
        self.edges.append((src, dst, edge_type, weight))
        self.interaction_history.append({
            "timestamp": time.time(),
            "src": src,
            "dst": dst,
            "type": edge_type,
            "weight": weight
        })

    def _encode_node_feature(self, node_type: str, domain: str) -> np.ndarray:
        """编码节点特征（简化版）"""
        # 实际应用中应使用更丰富的特征
        type_map = {"agent": 0, "gateway": 1, "resource": 2}
        domain_map = {"learner": 0, "gateway": 1, "education": 2}

        feature = np.zeros(10)
        feature[type_map.get(node_type.lower(), 0)] = 1.0
        feature[3 + domain_map.get(domain.lower(), 0)] = 1.0

        return feature

    def get_graph_snapshot(self) -> Data:
        """获取当前图的快照（PyTorch Geometric格式）"""
        if not self.nodes or not self.edges:
            # 返回空图
            return Data(
                x=torch.zeros((1, 10)),
                edge_index=torch.zeros((2, 1), dtype=torch.long)
            )

        # 构建节点索引映射
        node_list = list(self.nodes.keys())
        node_to_idx = {node: i for i, node in enumerate(node_list)}

        # 构建边索引
        edge_index = []
        edge_attr = []

        for src, dst, edge_type, weight in self.edges:
            if src in node_to_idx and dst in node_to_idx:
                edge_index.append([node_to_idx[src], node_to_idx[dst]])
                edge_attr.append([weight])

        if not edge_index:
            edge_index = [[0, 0]]
            edge_attr = [0.0]

        # 构建特征矩阵
        x = np.array([self.node_features[node] for node in node_list])

        return Data(
            x=torch.tensor(x, dtype=torch.float),
            edge_index=torch.tensor(edge_index, dtype=torch.long).t().contiguous(),
            edge_attr=torch.tensor(edge_attr, dtype=torch.float)
        )


class AnomalyDetector(nn.Module):
    """
    GNN异常检测器
    使用图注意力网络检测异常交互模式
    """

    def __init__(
        self,
        input_dim: int = 10,
        hidden_dim: int = 64,
        num_layers: int = 2,
        num_heads: int = 4
    ):
        super().__init__()

        self.convs = nn.ModuleList()
        self.convs.append(GATConv(input_dim, hidden_dim, heads=num_heads, concat=False))

        for _ in range(num_layers - 1):
            self.convs.append(GATConv(hidden_dim, hidden_dim, heads=num_heads, concat=False))

        # 异常分数输出层
        self.anomaly_head = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(32, 1),
            nn.Sigmoid()  # 输出0-1的异常概率
        )

    def forward(self, data: Data) -> torch.Tensor:
        """
        前向传播
        返回：每个节点的异常分数
        """
        x, edge_index = data.x, data.edge_index

        # GNN层
        for conv in self.convs:
            x = conv(x, edge_index)
            x = F.relu(x)

        # 异常分数
        anomaly_scores = self.anomaly_head(x)

        return anomaly_scores.squeeze()


class GNNGuard:
    """
    G-safeguard：GNN拓扑防御模块
    核心功能：
    1. 实时监控交互拓扑
    2. 检测异常模式（Prompt攻击、数据窃取）
    3. 动态剪枝（隔离污染源）
    4. 审计日志
    """

    def __init__(
        self,
        anomaly_threshold: float = 0.7,  # 异常阈值
        pruning_window: int = 10,  # 剪枝时间窗口（秒）
        device: str = "cpu"
    ):
        self.interaction_graph = InteractionGraph()

        # 初始化节点
        self._init_nodes()

        # GNN模型
        self.device = torch.device(device)
        self.anomaly_detector = AnomalyDetector().to(self.device)

        # 防御参数
        self.anomaly_threshold = anomaly_threshold
        self.pruning_window = pruning_window

        # 被隔离的节点
        self.quarantined_nodes: Set[str] = set()

        # 异常事件日志
        self.anomaly_log: List[Dict] = []

        # 基线模式（正常行为模板）
        self.baseline_stats: Dict[str, float] = {
            "avg_msg_freq": 1.0,  # 平均消息频率
            "avg_data_size": 1024,  # 平均数据大小
            "lateral_connection_rate": 0.0  # 横向连接率
        }

    def _init_nodes(self):
        """初始化系统节点"""
        # 网关节点
        self.interaction_graph.add_node(
            "privacy_gateway",
            "gateway",
            "gateway",
            {"role": "control_plane"}
        )

        # 智能体节点
        self.interaction_graph.add_node("A1", "agent", "learner")
        self.interaction_graph.add_node("AG2", "agent", "education")
        self.interaction_graph.add_node("AG3", "agent", "education")
        self.interaction_graph.add_node("AG4", "agent", "education")
        self.interaction_graph.add_node("AG5", "agent", "education")

    def monitor_interaction(
        self,
        src: str,
        dst: str,
        interaction_type: str,
        metadata: Dict = None
    ) -> Tuple[bool, str]:
        """
        监控单次交互
        返回：(是否允许, 原因)
        """
        # 检查源节点是否被隔离
        if src in self.quarantined_nodes:
            return False, f"源节点{src}已被隔离"

        if dst in self.quarantined_nodes:
            return False, f"目标节点{dst}已被隔离"

        # 检查是否为非法横向连接
        if self._is_lateral_connection(src, dst):
            self._handle_lateral_connection(src, dst)
            return False, f"检测到非法横向连接: {src} → {dst}"

        # 更新交互图
        self.interaction_graph.add_edge(
            src, dst, interaction_type,
            weight=metadata.get("data_size", 1.0) if metadata else 1.0
        )

        # 定期运行GNN检测
        if len(self.interaction_graph.edges) % 10 == 0:  # 每10次交互检测一次
            self._run_gnn_detection()

        return True, "OK"

    def _is_lateral_connection(self, src: str, dst: str) -> bool:
        """检测是否为横向连接"""
        src_info = self.interaction_graph.nodes.get(src, {})
        dst_info = self.interaction_graph.nodes.get(dst, {})

        # 业务智能体之间的直接连接
        if (src_info.get("type") == "agent" and
            dst_info.get("type") == "agent" and
            src_info.get("domain") == dst_info.get("domain") and
            src_info.get("domain") == "education"):
            return True

        return False

    def _handle_lateral_connection(self, src: str, dst: str):
        """处理横向连接"""
        # 记录异常
        self.anomaly_log.append({
            "timestamp": time.time(),
            "type": "lateral_connection",
            "src": src,
            "dst": dst,
            "severity": "critical"
        })

        # 隔离源节点
        self.quarantined_nodes.add(src)

        print(f"[G-safeguard] 🚨 检测到横向连接！已隔离节点: {src}")

    def _run_gnn_detection(self):
        """运行GNN异常检测"""
        try:
            # 获取图快照
            graph_data = self.interaction_graph.get_graph_snapshot()
            graph_data = graph_data.to(self.device)

            # 前向传播
            with torch.no_grad():
                anomaly_scores = self.anomaly_detector(graph_data)

            # 检查异常节点
            node_list = list(self.interaction_graph.nodes.keys())
            for i, score in enumerate(anomaly_scores):
                if score > self.anomaly_threshold:
                    node_id = node_list[i]
                    self._handle_anomalous_node(node_id, score.item())

        except Exception as e:
            print(f"[G-safeguard] ⚠️ GNN检测失败: {e}")

    def _handle_anomalous_node(self, node_id: str, score: float):
        """处理异常节点"""
        if node_id in self.quarantined_nodes:
            return  # 已经隔离

        # 记录异常
        self.anomaly_log.append({
            "timestamp": time.time(),
            "type": "anomalous_behavior",
            "node_id": node_id,
            "score": score,
            "severity": "high" if score > 0.8 else "medium"
        })

        # 高异常分数：立即隔离
        if score > 0.8:
            self.quarantined_nodes.add(node_id)
            print(f"[G-safeguard] 🚨 检测到高异常节点！已隔离: {node_id} (score: {score:.3f})")

    def get_topology_snapshot(self) -> Dict:
        """获取拓扑快照（用于可视化）"""
        return {
            "nodes": self.interaction_graph.nodes,
            "edges": self.interaction_graph.edges[-50:],  # 最近50条边
            "quarantined_nodes": list(self.quarantined_nodes),
            "anomaly_count": len(self.anomaly_log)
        }

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            "total_nodes": len(self.interaction_graph.nodes),
            "total_edges": len(self.interaction_graph.edges),
            "quarantined_nodes": len(self.quarantined_nodes),
            "anomaly_events": len(self.anomaly_log),
            "anomaly_rate": len(self.anomaly_log) / max(len(self.interaction_graph.edges), 1)
        }

    def reset_quarantine(self):
        """重置隔离（仅用于测试）"""
        self.quarantined_nodes.clear()
        self.anomaly_log.clear()


# 单例模式
_gnn_guard_instance: GNNGuard = None


def get_gnn_guard() -> GNNGuard:
    """获取GNN防御模块单例"""
    global _gnn_guard_instance
    if _gnn_guard_instance is None:
        _gnn_guard_instance = GNNGuard()
    return _gnn_guard_instance


# ============================================================
# 集成到网关
# ============================================================
def monitor_cross_domain_message(message: CrossDomainMessage) -> Tuple[bool, str]:
    """
    监控跨域消息（网关调用）
    返回：(是否允许, 原因)
    """
    guard = get_gnn_guard()

    src = message.source_agent.value if message.source_agent else message.source_domain.value
    dst = message.target_agent.value if message.target_agent else message.target_domain.value

    allowed, reason = guard.monitor_interaction(
        src=src,
        dst=dst,
        interaction_type="cross_domain_message",
        metadata={"data_size": len(str(message.payload))}
    )

    return allowed, reason


# ============================================================
# 使用示例
# ============================================================
def demo_gnn_guard():
    """演示G-safeguard功能"""
    guard = get_gnn_guard()

    print("\n" + "="*60)
    print("G-safeguard GNN拓扑防御演示")
    print("="*60)

    # 场景1：正常交互
    print("\n场景1：正常交互（A1 → Gateway → AG2）")
    print("-" * 40)

    allowed, reason = guard.monitor_interaction("A1", "privacy_gateway", "data_transfer")
    print(f"A1 → Gateway: {'✅ 允许' if allowed else '❌ 拒绝'} ({reason})")

    allowed, reason = guard.monitor_interaction("privacy_gateway", "AG2", "forward_data")
    print(f"Gateway → AG2: {'✅ 允许' if allowed else '❌ 拒绝'} ({reason})")

    # 场景2：非法横向连接
    print("\n场景2：非法横向连接（AG2 → AG3）")
    print("-" * 40)

    allowed, reason = guard.monitor_interaction("AG2", "AG3", "lateral_attempt")
    print(f"AG2 → AG3: {'✅ 允许' if allowed else '❌ 拒绝'} ({reason})")

    # 场景3：被隔离节点尝试通信
    print("\n场景3：被隔离节点尝试通信")
    print("-" * 40)

    allowed, reason = guard.monitor_interaction("AG2", "AG4", "retry_after_quarantine")
    print(f"AG2 → AG4: {'✅ 允许' if allowed else '❌ 拒绝'} ({reason})")

    # 统计信息
    print("\n" + "="*60)
    print("统计信息")
    print("="*60)
    stats = guard.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")

    print(f"\n被隔离节点: {guard.quarantined_nodes}")
    print(f"异常事件数: {len(guard.anomaly_log)}")


if __name__ == "__main__":
    demo_gnn_guard()
