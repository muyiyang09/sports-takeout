"""eval 包：Agent 评估（Eval）—— 数据集 + 指标 + 运行器 + LLM-as-Judge。

与单元测试的区别（#06 文档 §2.1）：单测断言「代码对不对」，Eval 量化「AI 表现好不好」，
给 baseline 分数、每次改 prompt/模型后对比趋势，而非精确对错。
"""
