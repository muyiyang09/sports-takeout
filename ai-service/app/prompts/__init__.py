"""prompts 包：Prompt 模板（YAML）+ 版本化加载器。

把 prompt 从代码常量抽到独立 YAML，实现「改 prompt 不动业务代码」，
并带 changelog 支撑版本管理 / 回归对比（#06 Harness 工程）。
"""
