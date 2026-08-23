# Benchmark 运行协议

本 benchmark 评测运行记录中冻结的完整“模型–harness 配置”，不能把结果解释为模型的固有能力。

## 运行模式

必须在看到结果前预先声明以下一种模式，不能根据结果再选择模式。

### 探针模式

探针模式是 `minimal-3` 等开发集的默认模式。

- 每个配置对每道题只运行一次。
- 不重跑有效失败。
- 只有 benchmark 基础设施明确故障时才能作废并重跑。
- 用探针结果淘汰较弱方案并选择少量候选方案进入确认阶段。
- 某道题的 evaluator 失败一旦影响 harness 修改，该题就只能作为开发证据。

探针模式刻意保持低成本。它不能证明较小的分数差异足以抵抗模型采样方差。

### 确认模式

确认模式用于比较探针筛选后的少量候选 harness。

- 第一次运行前声明题集、配置、重复次数和比较规则。
- 每次重复使用新的 session 和工作区。
- 无论早期结果如何都完成全部预定重复，不能在结果看起来有利时提前停止。
- 不选择性重跑单个有效结果。
- 条件允许时交错运行配置，例如 A1、B1、A2、B2，以降低 provider 或客户端漂移。
- 报告全部重复结果，同时汇总交付稳定性和效率，不能只保留最好结果。

预先计划的独立重复不是失败后的重跑；区别在于重复次数是否在看到结果前冻结。

## 运行前

1. 冻结 benchmark 版本以及 starter、evaluator、系统指令、preset、plugin 和 harness commit hash。
2. 记录声明的运行模式；确认模式还要冻结重复次数和比较规则。
3. 创建唯一的 run ID 和 session ID；不同任务或重复不能共享 session。
4. 使用 `harnessbench validate` 校验数据集。
5. 使用 `harnessbench prepare` 创建新的隔离工作区。
6. 确认工作区中没有 `private/`、隐藏实例、scorer、参考实现、历史结果或其他任务的 trace。

## 运行中

- 在发送 `TASK.md` 之前立即开始 wall time 和 usage 记录。
- Agent 只能读取和修改准备后的工作区。
- 不提供解题提示；无法避免的操作性消息必须完整记录为人工介入。
- Agent 主动完成、harness 失败或达到任务 timeout 时立即结束。
- timeout 和 harness crash 是有效结果，不属于基础设施作废。

## 运行后

1. 停止 Agent，将工作区设为只读或创建快照。
2. 保存完整 trace、工具调用、usage ledger、workspace diff 和结束原因。
3. 在 Agent 环境之外运行 `harnessbench evaluate`。
4. 将 evaluator 输出与运行指标合并为 run-result 格式。
5. 只有 runner 或 evaluator 自身发生明确故障时才标记 `infrastructure_invalidated`；重跑前必须记录具体故障。

## 比较顺序

1. Invalid 和关键失败。
2. ShipReady 任务数量。
3. 完成度与能力覆盖。
4. 优化任务的 objective quality。
5. 在完成度接近的结果中比较 wall time、token、credits、失败工具调用和人工介入。

不要生成一个混合质量与成本的万能总分，应保留 Pareto frontier。确认运行应报告各题在全部重复中的结果；改进最好能跨任务或重复出现，而不是依赖一次异常强的样本。

## 能力硬门槛

任务可在 `task.toml` 中声明 `required_capabilities`。每个必需能力都必须获得 evaluator 分配的全部权重，结果才能达到 ShipReady，即使总完成分已经超过 `ship_ready_score`。

只应把缺失后会使产物根本无法交付的属性设为硬门槛，例如持久化、授权边界、安全不变量或优化可行性；不要用它强制可选质量维度必须满分。

## 测试集退役与密封

`minimal-3` 是公开开发探针，其 evaluator 和参考实现在本仓库中可见，不能视为真正的密封选择集。

某道题的 evaluator 失败一旦影响 harness 修改，该题只能作为开发证据。它可以继续作为回归测试，但不能再作为独立的选择结果。

选择集和最终确认集应把 evaluator 案例与参考实现保存在被测 Agent 无法访问的仓库和环境之外，直到比较结束。若复现需要后续公开，应在运行前冻结并记录 evaluator 哈希，结束后再公开密封材料。
