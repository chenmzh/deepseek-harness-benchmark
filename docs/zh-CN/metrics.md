# 指标协议

质量和效率是独立维度。evaluator 负责完成度、ShipReady、关键失败、能力明细和优化质量；runner 负责时间、usage、工具活动、人工介入和结束状态。

完成两侧记录后运行：

```bash
harnessbench assemble evaluator.json run-metadata.json --output result.json
```

## 质量指标

- `completion_score`：0–100 的加权行为覆盖。
- `ship_ready`：达到任务门槛并且没有关键失败。
- `critical_failures`：安全、完整性或必要行为失败。
- `optimizer_quality`：适用于优化任务的归一化质量。

## 效率指标

- `wall_time_seconds`：用户实际等待的完整时间。
- `model_active_seconds`：能够观测时记录的模型执行时间。
- 输入、缓存输入、输出和 reasoning token。
- 实际订阅 credits 与可选的 API 等价成本。
- 工具调用、失败调用、测试循环和人工介入。

使用订阅运行时，API 等价成本只是反事实估计，不能报告为实际花费。只有质量和关键失败状态接近时才比较效率。
