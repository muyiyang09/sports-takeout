# AI 微服务开发文档 · #02 Agent 工程化能力全景与学习路径

> 版本：v1.0 · 2026-08-26
> **文档分类**：工程手册（Handbook） · **强制性**：参考查阅 · **用途**：系统化知识库、技术选型依据、新人学习地图
> 定位：**学习地图**，不是落地清单
> 目的：让团队（含二次开发者、商用买家）系统理解一个**生产级 Agent**应当具备哪些能力、每项背后的设计思路与主流做法
> 配套：后续 #03~#08 会针对每个能力在本项目做具体落地（每份文档对应一个能力域的工程实现）

---

## 0. 为什么需要这份文档

#01 已经说清楚"现在做了什么、缺什么"，但**为什么缺这些、为什么这样补、为什么不补另一些**——这背后是 Agent 工程化的能力图谱。如果不先建立这个全景认知，遇到下一步决策（"要不要加长期记忆？""ReAct 还是 Plan-and-Execute？""用不用多 Agent？"）会反复纠结。

这份文档把**生产级 Agent 的 10 大能力域**讲清楚，每项按统一结构展开：

```
是什么 → 为什么需要 → 主流做法（思路 + 选型对比）→ 本项目现状 → 本项目建议
```

读完这份，你能：
- 看懂任何 Agent 框架（LangGraph / OpenAI Agents SDK / AutoGen / CrewAI / Dify / Coze）的设计动机
- 在本项目里做技术选型时，知道每个选择的代价和替代方案
- 跟上 2024~2026 Agent 工程化的主流范式

---

## 1. Agent 工程化能力全景图

| # | 能力域 | 一句话 | 当前项目是否具备 |
|---|---|---|---|
| 1 | **记忆系统** | 让 Agent 记得住短期上下文 + 跨会话积累 | ❌ 仅单次任务状态，无 Checkpointer / 无长期记忆 |
| 2 | **工具系统** | 让 Agent 能调外部能力（DB / API / 模型） | ⚠️ 节点内写死 SQL，未抽象为 Tool |
| 3 | **规划与推理** | 让 Agent 会"想"：ReAct / Plan-Execute / Reflection | ❌ 固定 DAG，无自主决策 |
| 4 | **控制流** | 条件分支 / 循环 / HITL / Subgraph | ❌ 串行 DAG，`ConditionalRouter` 已写未用 |
| 5 | **状态管理** | State Schema + Reducer + Checkpoint + Time Travel | ⚠️ 有 State，无 Checkpoint |
| 6 | **多 Agent 协作** | Supervisor / Handoff / Swarm | ❌ 单 Agent |
| 7 | **可观测性** | Trace / Span / Metrics / Replay | ❌ 仅 logging.basicConfig |
| 8 | **安全与对齐** | Guardrails / 权限 / 预算 / 审计 | ❌ 无 |
| 9 | **评估与迭代** | 离线 Eval / 在线 A/B / LLM-as-Judge | ❌ 仅 1 个 smoke test |
| 10 | **部署与运维** | 容器化 / 弹性 / 灰度 / 熔断 / 限流 | ❌ 本地脚本启动 |

下面 10 节每节展开一个能力域。

---

## 2. 记忆系统（重点）

记忆是 Agent 区别于"一次性 LLM 调用"的核心。一个 Agent 能否商用，很大程度看记忆系统设计。

### 2.1 短期记忆（Working Memory / Short-term）

**是什么**：单次对话/单次任务内的临时状态，任务结束即丢弃。

**三种形态**（理解这三种，比记"短期记忆"四个字重要）：

| 形态 | 作用 | LangGraph 载体 | 本项目对应 |
|---|---|---|---|
| 消息列表 | 多轮对话的历史 message | `messages: Annotated[list, add_messages]` | 未使用（当前单轮） |
| 业务状态 | 节点间传递的中间产物 | State 的其他字段 | `RecommendState.intent / candidates` |
| 工作变量 | 节点内临时计算 | 节点函数局部变量 | `_mock_extract_intent` 里的 `d` |

**存储介质对比**（关键决策点）：

| 介质 | 适用场景 | 是否持久 | 是否多副本共享 | 本项目选型 |
|---|---|---|---|---|
| 进程内 dict | 单进程 demo | ❌ 重启丢 | ❌ | 当前隐式 |
| `MemorySaver`（LangGraph 内置） | 单进程开发 | ❌ 重启丢 | ❌ | 开发期可用 |
| Redis Checkpointer | 生产单/多副本 | ✅ TTL | ✅ | **推荐** |
| PostgreSQL Checkpointer | 需要时间旅行/审计 | ✅ 永久 | ✅ | 二期可选 |

**滑动窗口策略**（消息过多时怎么办）：

- **按数量截断**：保留最近 N 轮（如 N=10），实现简单，丢上下文
- **按 token 截断**：保留最近 4K token，主流做法，需要 tokenizer
- **摘要压缩**：旧消息用 LLM 摘要成 1 条，再追加新消息（参考 memgpt / letta）
- **选择性保留**：保留含工具调用结果的消息 + 最近 N 轮（信息密度高）

**主流框架做法**：

- **LangGraph**：`add_messages` reducer 自动增量追加，配合 `trim_messages` 工具函数做窗口
- **OpenAI Agents SDK**：`context` 参数透传，无内置窗口管理
- **LangChain RunnableWithMessageHistory**：基于 session_id 隔离

**本项目现状与建议**：
- 当前 `RecommendState` 是典型短期记忆，但**无 Checkpointer**——进程崩了无法 resume，多副本无法共享
- **建议**：Phase 1 接 Redis Checkpointer + TTL 1h（教练推荐是单次任务，不需要长记忆，但需要 crash 恢复 + 多副本一致）

### 2.2 长期记忆（Long-term Memory）

**是什么**：跨对话/跨任务持久化的信息，是 Agent "认识用户"的关键。

**四种类型**（参考认知科学分类，业内 2024 后开始统一用这套术语）：

| 类型 | 含义 | 教练推荐场景的例子 | 写入时机 |
|---|---|---|---|
| **语义记忆 Semantic** | 事实知识 | "用户 A 有腰椎间盘突出" | 用户主动告知 → 抽取 |
| **情景记忆 Episodic** | 历史交互片段 | "上次推荐李教练，用户接受了" | 交互结束后异步写入 |
| **程序性记忆 Procedural** | 操作习惯 | "用户偏好周末上午 9-10 点" | 从多次行为中归纳 |
| **用户画像 Profile** | 聚合偏好 | "25-30 岁女性 / 朝阳 / 产后恢复 / 预算 200-300" | 后台周期性聚合 |

**存储介质选型矩阵**：

| 记忆类型 | 推荐介质 | 召回方式 | 理由 |
|---|---|---|---|
| 语义 | 向量库（pgvector / Milvus / Chroma） | 相似度召回 | "腰突"↔"腰椎间盘突出"靠语义而非字面 |
| 情景 | 向量库 + 时间索引 | 相似度 + 时间衰减 | 旧交互权重低 |
| 程序 | Redis Hash / MySQL | 按 user_id 直接查 | 结构化，频繁读 |
| 画像 | MySQL user_profile 表 | SQL 关联查询 | 跨服务共享，运营可读 |

**写入时机**（什么时候往长期记忆里写）：

```
显式写入：
  用户主动告知 → LLM 抽取 → 写入语义记忆
  例：用户说"我有腰突" → Node 末尾抽取 → 写入 user_facts 表

隐式写入：
  交互结束后 → 后台异步任务抽取 → 写入情景/程序记忆
  例：用户下单了李教练 → 异步写入"用户接受了李教练推荐"

周期聚合：
  每天/每周 → 聚合历史 → 更新画像
  例：周一定时跑"用户偏好聚合"任务
```

**召回时机**（什么时候把长期记忆读出来用）：

```
对话开始时：
  按 user_id 查画像 → 注入 system prompt
  例：system: "该用户偏好周末上午、预算 200-300、有腰突史"

工具调用前：
  按当前 query 向量召回 Top K 相关历史片段 → 注入 tool context
  例：用户问"产后恢复" → 召回历史"该用户曾接受过张教练产后恢复服务"
```

**主流做法对比**：

| 框架/产品 | 长期记忆方案 | 优点 | 缺点 |
|---|---|---|---|
| LangGraph Store API | namespace + key + value + index，自带向量索引 | 与 Graph 同栈，无新组件 | 1.x 后才稳定 |
| Mem0 | 第三方记忆框架，自动抽取/合并/召回 | 智能合并 | 多一个依赖 |
| Letta（原 MemGPT） | 把记忆建模成"主存+外部存储+分页" | 学术上优雅 | 工程复杂 |
| Zep | 时序知识图谱 | 关系推理 | 重 |
| OpenAI Memory SDK | ChatGPT 同款，预览版 | 体验好 | 锁定 OpenAI |

**本项目现状与建议**：
- 当前**完全无长期记忆**——同一用户每次推荐都从零开始
- **建议**：
  1. Phase 1 先做"显式语义记忆"：在 recommend_coach 加一个 `extract_user_facts` 节点，抽取用户主动告知的事实（腰突/孕期/伤病史），写入 MySQL `user_facts` 表
  2. Phase 5 评价摘要 Agent 落地时做"情景记忆"：用户历史评价写入向量库，下次推荐时召回
  3. 选型：**Milvus**（分布式+HA+多副本共享同一实例，支撑 AI 服务多副本部署；HNSW+COSINE ms 级召回，运维成熟 Attu/Prometheus/Grafana）

### 2.3 跨会话记忆召回范式

三种主流做法（从简单到复杂）：

```
范式 1：Cold Start（当前项目做法）
  每次新对话从空开始
  优点：简单
  缺点：用户重复输入偏好

范式 2：Profile Injection（推荐先做这个）
  对话开始时按 user_id 查画像 → 注入 system prompt
  优点：实现简单，效果显著
  缺点：画像更新滞后

范式 3：RAG-style Recall（高级）
  对话开始时按当前 query 向量召回相关历史片段
  优点：精准，能召回情景记忆
  缺点：需要向量库 + embedding 模型
```

**学习要点**：不要一上来就上范式 3。先做范式 2（画像注入），80% 场景够用。

---

## 3. 工具系统（Tools）

### 3.1 工具定义范式

| 范式 | 写法 | 优点 | 缺点 |
|---|---|---|---|
| @tool 装饰器（LangChain 风格） | `@tool\n def fetch_coaches(...): ...` | 简洁，自动从 docstring 抽 schema | 装饰器魔法 |
| Pydantic Schema（OpenAI 风格） | 定义 `class FetchCoachesArgs(BaseModel)` + 函数 | 强类型，可控 | 模板代码多 |
| MCP Tool（标准化协议） | JSON Schema + stdio/http transport | 跨语言/跨进程 | 引入协议复杂度 |

### 3.2 工具调用模式

```
模式 1：ReAct Loop（最主流）
  LLM 输出 thought + tool_call → 执行 tool → observation → LLM 再思考
  适合：探索性任务，LLM 自主决定调什么、调几次

模式 2：Function Calling（模型原生）
  模型直接输出结构化 tool_name + args，框架执行后回传 tool_result
  适合：单步或少数几步的工具调用

模式 3：ToolNode + should_continue（LangGraph 标准）
  Graph 节点：ToolNode（执行工具）+ 条件边 should_continue
  if "tool_calls" in last_message: go to ToolNode
  else: go to END
  适合：与 Graph 拓扑结合，可观测

模式 4：Parallel Tool Call
  一次返回多个 tool_call，框架并行执行
  适合：无依赖的多工具调用，降延迟
```

### 3.3 工程化要点

| 要点 | 说明 | 本项目状态 |
|---|---|---|
| 工具权限 RBAC | 不同用户/Agent 不同工具白名单 | ❌ |
| 工具版本化 | schema 升级不破坏在线 Agent | ❌ |
| 工具超时 | 每个工具有独立超时 | ❌ |
| 工具幂等 | 相同参数多次调用结果一致 | ⚠️ DB 查询幂等，但 LLM 调用不幂等 |
| 工具审计 | 所有调用留痕（who/when/args/result） | ❌ |
| 工具缓存 | 同参数结果缓存 | ❌ |
| 工具降级 | 工具失败 → fallback 默认值 | ⚠️ 有 fallback mock 但无统一封装 |

---

## 4. 规划与推理（Planning & Reasoning）

让 Agent 会"想"——不是固定流程，而是自主决策。

### 4.1 主流范式

| 范式 | 思路 | 适用场景 | 复杂度 |
|---|---|---|---|
| **ReAct** | Thought → Action → Observation 循环 | 探索性、短任务（<5 步） | 中 |
| **Plan-and-Execute** | 先 LLM 全局规划步骤 → 分步执行 → 反思修正 | 长任务（>10 步） | 高 |
| **Tree of Thoughts (ToT)** | 多路径探索 + 评估剪枝 | 推理难题、多方案对比 | 高 |
| **Reflection / Self-Critique** | LLM 自评 → 不满意重写 | 质量门控 | 低 |
| **Chain-of-Thought (CoT)** | 显式推理链（让 LLM "think step by step"） | 数学/逻辑 | 低 |

### 4.2 选型决策树

```
任务步数 < 5 ？
  是 → ReAct
  否 → Plan-and-Execute

输出质量敏感？
  是 → 加 Reflection 层（生成后自评，不合格重写）

多方案需要对比？
  是 → ToT

纯逻辑/数学题？
  是 → CoT
```

### 4.3 主流框架实现

- **LangGraph**：用 Graph 拓扑表达任意范式（ReAct = ToolNode + should_continue 循环）
- **OpenAI Agents SDK**：内置 `tool_use` 循环 + Handoff
- **AutoGen**：多 Agent 对话式协作
- **CrewAI**：角色化 + 任务分派

**本项目建议**：
- 当前 recommend_coach 是**固定 DAG**（≈ Plan-and-Execute 的退化版，无规划阶段，硬编码步骤）
- 证书审核 Agent 适合 **ReAct**（让 LLM 自主决定调 OCR / 查库 / 比对哪个工具）
- 评价摘要 Agent 适合 **Plan-and-Execute + Reflection**（先规划 N 条评价如何处理，再分步执行，最后自评摘要质量）

---

## 5. 控制流（Control Flow）

| 拓扑 | 描述 | 本项目状态 |
|---|---|---|
| DAG（有向无环图） | 固定串行/并行节点 | ✅ 当前 |
| State Machine | 条件分支 + 循环 | ❌ 缺 |
| Loop with Exit | 最大轮数 / 质量门控 / 预算耗尽 | ❌ 缺 |
| HITL Interrupt | 关键节点暂停等人工确认 | ❌ 缺 |
| Subgraph | Agent 嵌套 Agent | ❌ 缺 |
| Map-Reduce | 并行处理多输入 | ❌ 缺 |

**HITL 是商业化关键**——很多业务（证书审核、医疗咨询、金融决策）必须人工兜底。LangGraph 提供 `interrupt()` 函数 + Checkpointer 实现：节点遇到 interrupt → Graph 暂停 → 状态持久化 → 等人工输入 → resume。

---

## 6. 状态管理（State Management）

| 概念 | 作用 | 本项目状态 |
|---|---|---|
| State Schema | 定义状态字段类型 | ✅ TypedDict `RecommendState` |
| Reducer | 多节点写同一字段如何 merge | ⚠️ LangGraph 默认 last-write-wins，未显式声明 |
| Checkpointing | 持久化中间状态，支持 resume | ❌ |
| Time Travel | 回到任意 checkpoint 重放 | ❌ |
| Channel | 命名空间隔离状态 | ❌ |

**主流框架做法**：
- LangGraph：`StateGraph` + `add_messages` reducer + `MemorySaver` / `RedisSaver` / `PostgresSaver`
- OpenAI Agents SDK：`context` 对象 + `Handoff` 传递
- AutoGen：对话历史列表

**本项目建议**：Phase 1 引入 `RedisCheckpointer`，所有 Graph 编译时挂上，立得 3 个收益：
1. crash 恢复
2. 多副本共享状态
3. 为 HITL 铺路（interrupt 必须配合 Checkpointer）

---

## 7. 多 Agent 协作（Multi-Agent）

| 模式 | 描述 | 适用 | 复杂度 |
|---|---|---|---|
| **Supervisor-Worker** | 主 Agent 拆任务分派给子 Agent | 任务可分解 | 中 |
| **Hierarchical** | 多层 supervisor | 大型任务 | 高 |
| **Handoff** | Agent 间传递控制权（OpenAI 风格） | 用户意图流转 | 中 |
| **Network / Swarm** | 去中心化协作 | 探索性 | 高 |
| **Debate** | 多 Agent 辩论达成共识 | 需要多元视角 | 高 |

**何时需要多 Agent**：
- 单 Agent 工具太多（>10 个）→ 拆分
- 任务跨度大（用户咨询 → 下单 → 售后）→ 不同 Agent 不同专长
- 需要不同模型（贵模型规划，便宜模型执行）

**本项目建议**：Phase 5 落地第三个 Agent 后，用 **Supervisor 模式**统一调度：
- Supervisor Agent：根据用户意图路由到「推荐」「评价摘要」「证书审核」之一
- 各子 Agent 独立 Graph，Handoff 传递 user_id 和上下文

---

## 8. 可观测性（Observability）

| 层级 | 内容 | 工具 | 本项目状态 |
|---|---|---|---|
| Trace | 一次请求的完整节点链路 | LangSmith / Langfuse / Phoenix | ❌ |
| Span | 节点级耗时 / token / 错误 | 同上 | ❌ |
| Metrics | QPS / p99 / 错误率 / 成本 | Prometheus + Grafana | ❌ |
| Log | 结构化日志 + request_id 贯穿 | structlog / loguru | ⚠️ 仅 logging.basicConfig |
| Replay | 用 trace 重放调试 | LangSmith Replay | ❌ |

**主流选型对比**：

| 工具 | 部署 | 成本 | 优点 | 推荐场景 |
|---|---|---|---|---|
| LangSmith | 云 | 付费 | 体验最好 | 不在乎数据出境 |
| **Langfuse** | 自部署/云 | 免费 | 开源，数据自主 | **本项目推荐** |
| Arize Phoenix | 自部署 | 免费 | 开源，含 Eval | 重 Eval 场景 |
| OpenTelemetry | 标准 | - | 通用 | 已有 APM 体系 |

**本项目建议**：Phase 3 自部署 Langfuse（一个 docker-compose 服务），所有 LangGraph 调用自动埋点。

---

## 9. 安全与对齐（Safety & Alignment）

商业化必备，但容易忽视。

| 项 | 风险 | 主流做法 | 本项目状态 |
|---|---|---|---|
| Input Guardrails | 越狱 / 提示注入 / PII 泄露 | LLM-as-Judge / 正则 / NeMo Guardrails | ❌ |
| Output Guardrails | 敏感词 / 事实错误 / 格式不合法 | JSON Schema 校验 / 事实核查 | ⚠️ 仅 Pydantic 校验 |
| Tool Permission | 越权调用工具 | RBAC + 工具白名单 | ❌ |
| Token Budget | 单用户/单日预算爆炸 | token 计数 + 配额表 | ❌ |
| Audit Log | 合规审计、回溯追责 | 所有 LLM/Tool 调用入审计库 | ❌ |
| Prompt Injection | 用户输入劫持 system prompt | 输入隔离 / 标记边界 | ❌ |

**本项目建议**：商业化加固（Phase 2）至少做：
1. Token Budget：单用户单日上限 100K token（防恶意刷）
2. Audit Log：所有 LLM 调用入 MySQL `ai_audit_log` 表
3. Prompt Injection 防护：用户输入用 `<user_input>...</user_input>` 标签包裹

---

## 10. 评估与迭代（Eval & Iteration）

| 层级 | 内容 | 工具 | 本项目状态 |
|---|---|---|---|
| 离线 Eval | 标注集 + metric + baseline | 自建 / Langfuse Eval | ❌ |
| 在线 Eval | 用户反馈（点赞/点踩）回流 | 自建 | ❌ |
| LLM-as-Judge | 用强模型评判 Agent 输出 | GPT-4 / Claude 评判 | ❌ |
| Regression Test | 改 prompt 后跑 eval 防回归 | pytest + eval 集 | ❌ |
| A/B Test | 流量分桶对比 prompt/模型 | 自建 / Langfuse | ❌ |

**Metric 设计原则**（关键学习点）：
- 不要只评最终输出，要分节点评（Intent 抽取准确率 / Top-K 命中率 / 理由可读性 各自打分）
- LLM-as-Judge 用便宜模型（gpt-4o-mini / deepseek-chat）评，比人工便宜 100 倍
- 在线 Eval 比离线 Eval 更重要——用户点击/下单才是真 ground truth

---

## 11. 部署与运维（Deploy & Ops）

| 项 | 主流做法 | 本项目状态 |
|---|---|---|
| 容器化 | Docker 多阶段构建 + 非 root 用户 | ❌ |
| 编排 | docker-compose / K8s | ❌（ai-service 未在 compose 里） |
| 弹性伸缩 | HPA 基于 QPS / latency | ❌ |
| 蓝绿/灰度 | 多版本流量切分 | ❌ |
| 熔断 | Hystrix / Sentinel / 自建 | ❌ |
| 限流 | Token Bucket / Leaky Bucket | ❌ |
| 模型路由 | LiteLLM 路由 + 故障切换 | ⚠️ 有 LiteLLM 但无故障切换 |
| Graceful Shutdown | SIGTERM → 拒新请求 → 等在飞 → 退出 | ❌ |
| 健康探针 | /healthz (liveness) + /readyz (readiness) 分离 | ⚠️ 仅 healthz |

---

## 12. 学习路径建议

按"投入产出 + 难度递增"排序，每阶段 1~2 周：

| 阶段 | 学什么 | 实践项目 | 对应文档 |
|---|---|---|---|
| **入门** | ReAct + 短期记忆 + 单工具 | 改造 recommend_coach 为 ReAct（让 LLM 决定调 SQL 工具） | #03 Loop 工程 |
| **进阶 1** | 长期记忆 + 多工具 + Reflection | 加 user_facts 表 + 画像注入 + 推荐理由自评 | #06 Harness |
| **进阶 2** | 混合检索 + Rerank | 把 Node2 升级为 BM25+向量+SQL 三路融合 | #04 RAG 升级 |
| **高阶 1** | 多 Agent + HITL + Eval | 证书审核 Agent（ReAct + HITL）+ 评价摘要 Agent | #08 双 Agent |
| **高阶 2** | 可观测 + 安全 + 灰度 | Langfuse + Token Budget + Audit Log | #05 商业化加固 |
| **商业级** | MCP + K8s + A/B | MCP 工具层 + K8s 部署 + A/B 测试 prompt | #07 MCP |

**学习要点**：
1. 不要一上来就学全部——按项目需要推进，每阶段都能交付价值
2. 学每个能力时，对照"主流框架怎么做"和"自己手撸怎么做"——理解差距
3. 跟上游：LangGraph 1.x / OpenAI Agents SDK / Anthropic Computer Use 的发版说明

---

## 13. 本项目的能力定位（自评）

```
                 生产级 ←─────────────────────────→ 玩具级
                       │
   记忆系统             │  无 Checkpoint / 无长期记忆
   工具系统             │  节点内写死 SQL，未抽象
   规划推理             │  固定 DAG，无 ReAct
   控制流               │  无分支无循环无 HITL
   状态管理             │  有 State 无 Checkpoint
   多 Agent             │  单 Agent
   可观测               │  仅 logging
   安全                 │  无
   评估                 │  1 个 smoke test
   部署                 │  本地脚本
                       │
                       ▼
                  当前在「能跑通的 Demo」与「最小可商用」之间
                  商业化目标：达到「最小可商用」
```

**最小可商用 Agent 的硬指标**（业界共识）：
- ✅ 异步 + 连接池 + 限流（不被打挂）
- ✅ 容器化 + 多副本（高可用）
- ✅ Trace + Metrics（看得见在跑什么）
- ✅ 离线 Eval 集（改 prompt 不慌）
- ✅ Token Budget + Audit Log（成本可控 + 合规）
- ✅ 至少 1 个 HITL 节点（关键决策人工兜底）

当前项目 6 项中 **0 项达标**，所以 #01 文档把"商业化加固"列为 Phase 2 高优先级。

---

## 14. 下一步行动

读完这份全景图后，建议按以下顺序推进后续文档：

1. **#03 Loop 工程落地**（解锁 ReAct / HITL / 重试循环，给后续所有 Agent 铺路）
2. **#04 RAG 混合检索升级**（解决"语义匹配只是关键词子串"的硬伤）
3. **#05 商业化加固**（异步化 + 容器化 + 限流 + 熔断 + Trace）
4. **#06 Harness 工程**（Eval 集 + Langfuse + Prompt 管理）
5. **#07 MCP 工具层**（工具抽象 + 跨语言复用）
6. **#08 第二、第三 Agent 落地**（评价摘要 + 证书审核，把前 5 份文档的能力综合用上）

回复「开始 #03」推进 Loop 工程，或指定想先看的编号。
