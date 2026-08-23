# 测试任务开发规范

## 必需内容

公开任务目录：

```text
TASK.md
task.toml
starter/
public-tests/
```

开发 evaluator 位于 `private/hidden-tests/<task-slug>/`，并由 `task.toml` 的 `private_scorer` 字段引用。真正的密封选择集或确认集必须把 evaluator 保存在被测 Agent 无法访问的仓库和环境之外。

## 开发流程

1. 先写能力地图。每项评分要求必须有唯一归属和明确权重。
2. 识别缺失后会使产物根本无法交付的能力，并将其名称声明为 `required_capabilities`。
3. 编写正确的私有参考实现。
4. 编写确定性的公开 smoke tests，只公开接口而不泄露所有边界案例。
5. 编写覆盖边界、异常、不变量、重启和回归的隐藏测试。
6. 使用 untouched starter、参考实现以及至少两个故意不完整的 mutation 校准 scorer；mutation 必须覆盖每个必需能力。
7. 冻结哈希并设置版本；评分语义或 ShipReady 门槛改变必须提升任务版本。

## 质量要求

- 不联网也必须能够完成任务。
- 公开题面必须声明全部必需行为。隐藏测试可以隐藏示例，不能隐藏需求。
- 修改测试、删除 fixture、伪造证据或针对隐藏输入硬编码都不能获得分数。
- 优先测试行为与不变量，不依赖具体代码结构。
- 只有无法确定性评测的能力才考虑 LLM Judge，并尽量不让它决定 ShipReady。
- 任务优化质量和运行效率必须分开记录。

## 必需能力

`required_capabilities` 是 `task.toml` 中 evaluator 区段的可选数组：

```toml
[evaluator]
ship_ready_score = 85
private_scorer = "example/score.py"
required_capabilities = ["durability", "authorization_boundary"]
```

每个名称都必须出现在 scorer 的 `capabilities` 对象中，并提供数值类型的 `earned` 和 `weight`。只有 `earned == weight` 时该能力才通过。缺失、格式错误或只获得部分分数的必需能力都会使结果不能达到 ShipReady，即使总完成分超过阈值。

应谨慎使用该机制。适合设为硬门槛的包括持久化保证、安全不变量、授权边界和优化可行性；不要用它强制可选质量维度必须满分。

## 优化任务

每个实例必须具有确定性 baseline，以及冻结的 best-known 目标、正确 oracle 或有效下界。合法性始终是门槛；非法解不能获得优化质量分。实例应来自多个预先冻结的分布，避免一种启发式算法控制全部结果。
