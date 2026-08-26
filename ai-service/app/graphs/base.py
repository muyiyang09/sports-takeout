"""BaseGraph：所有工作流图的公共基类与工具函数。

这里故意只引入「langgraph StateGraph + START/END」与消息 reducer，
不引入任何 LangChain Core 的链式组件，把 LangChain 当零件超市用、只取有用的。
"""
from __future__ import annotations

from typing import Any, TypedDict, TypeVar

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import Annotated

T = TypeVar("T")


# =============================================================================
# 公共消息 reducer：推荐 Graph 目前不做多轮对话，但保留消息字段方便以后扩展。
# 用法：在自定义 State 中声明 messages: Annotated[list[BaseMessage], add_messages]
#       节点返回 {"messages": [AIMessage(...)]} 即可完成增量追加，无需自己 merge。
# =============================================================================
MessagesState = Annotated[list[BaseMessage], add_messages]


# =============================================================================
# 节点路由辅助：把「节点写一个分支字段 → 路由函数只返回分支 key → add_conditional_edges
# 配 key -> node 映射」的固定模式抽出来，避免拓扑歧义（经验 1635788）。
# =============================================================================
class ConditionalRouter:
    """用法：

    class MyState(TypedDict):
        branch: str

    router = ConditionalRouter(
        state_field="branch",
        mapping={
            "A": "node_a",
            "B": "node_b",
            "stop": END,
        },
        default=END,
    )

    builder.add_conditional_edges("root", router.route, router.edges())
    """

    def __init__(self, state_field: str, mapping: dict[str, str], default: Any = END) -> None:
        self.state_field = state_field
        self.mapping = mapping
        self.default = default

    def route(self, state: dict[str, Any]) -> Any:
        key = state.get(self.state_field)
        return self.mapping.get(key, self.default)

    def edges(self) -> dict[str, Any]:
        return dict(self.mapping)


# =============================================================================
# 消息辅助：统一把用户输入包成 HumanMessage。
# 对外的 State 一般只存 user_query 字符串，节点内部再转消息对象。
# =============================================================================
def to_human(query: str) -> list[BaseMessage]:
    return [HumanMessage(content=query)]


__all__ = [
    "MessagesState",
    "StateGraph",
    "START",
    "END",
    "Annotated",
    "TypedDict",
    "ConditionalRouter",
    "to_human",
]
