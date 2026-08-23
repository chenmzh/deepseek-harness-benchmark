# 单次运行协议

本协议评测的是记录中冻结的完整“模型–harness 配置”，不能把结果解释为模型的固有能力。

## 运行前

1. 冻结 benchmark 版本以及 starter、evaluator、系统指令、preset、plugin 和 harness commit hash。
2. 创建唯一的 run ID 和 session ID；不同任务不能共享 session。
3. 使用 `harnessbench validate` 校验数据集。
4. 使用 `harnessbench prepare` 创建新的隔离工作区。
5. 确认工作区中没有 `private/`、隐藏实例、scorer、参考实现、历史结果或其他任务的 trace。

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

不要生成一个混合质量与成本的万能总分，应保留 Pareto frontier。

## 测试集退役

如果某道题的隐藏失败已经影响 harness 修改，这道题只能作为开发回归题，不能继续提供独立选择证据。后续选择必须使用密封数据集或预先生成并冻结的 shadow variant。
