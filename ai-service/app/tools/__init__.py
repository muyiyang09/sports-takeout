"""tools 包：工具注册表（#07 MCP 工具层）。

把「节点直接 import db/bm25/vectorstore」抽象成「工具注册表」——统一 name/description/
JSON Schema/实现，供多 Agent 共享、供 MCP Server 对外暴露、供跨语言复用。
"""
