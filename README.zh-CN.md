# DeepSeek Harness Benchmark

[English](README.md) | 中文

这是一个确定性、仓库级的测试集开发库，用来测量模型 harness 的设计变化如何影响项目完成度、可靠性、运行时间、token 使用量和成本。

> 当前状态：早期开发。`minimal-3` 已实现并完成校准；`core-8` 与 `confidence-6` 目前只保留密封测试集规格，等探针框架稳定后再实现。

## 核心原则

- 评测完整的“模型–harness 配置”，而不是孤立的模型名称。
- 项目完成度和关键失败是质量门槛；时间、token 与成本是独立效率维度。
- 隐藏测试和参考实现永远不能进入被测 Agent 的工作区。
- 每次运行前冻结题目、evaluator、资源限制、指令、preset、plugin 和 harness 版本。
- 有效失败不重跑；只有明确的基础设施故障可以作废后重跑。
- 优先使用本地确定性测试，避免把 LLM Judge 作为 ShipReady 的关键门槛。

## 仓库结构

```text
datasets/                  公开题面、starter 和公开测试
private/hidden-tests/      Agent 不可见的隐藏 scorer
private/reference-solutions/ 私有参考实现
src/harnessbench/          校验、工作区准备、评测和结果组装 CLI
schemas/                   task manifest 与运行结果协议
docs/                      英文维护文档
docs/zh-CN/                中文维护文档
tests/                     benchmark 工具自身的测试
AGENTS.md                  Agent/AI 开发者的操作约束
llms.txt                   AI 的最短文档索引
```

## 环境

- Python 3.11 或更高版本
- benchmark 工具本身只使用 Python 标准库
- 任务默认无网络、无 GPU、2 CPU、2 GB 内存

从源码目录直接运行时使用 `PYTHONPATH=src`：

```bash
PYTHONPATH=src python3 -m harnessbench validate datasets/minimal-3
```

## Minimal-3

| ID | 任务 | 主要测量内容 |
|---|---|---|
| M1 | Reservation Repair | 根因诊断、状态不变量、幂等和回滚 |
| M2 | MicroScheduler-12 | 约束建模、确定性和小规模组合优化 |
| M3 | Durable Lease Queue | 从骨架完成项目、lease、重试和持久化 |

原始 starter 都能运行但不能达到 ShipReady；私有参考实现必须达到 ShipReady。M2 使用冻结的 best-known 目标进行归一化，不依赖 GPU、渲染、浏览器或大型模拟。

## 一次完整运行

### 1. 校验测试集

```bash
PYTHONPATH=src python3 -m harnessbench validate datasets/minimal-3
```

### 2. 创建隔离工作区

```bash
PYTHONPATH=src python3 -m harnessbench prepare \
  datasets/minimal-3/m1-reservation-repair \
  /tmp/m1-workspace
```

只把 `/tmp/m1-workspace` 提供给被测 Agent。它包含题面、starter 和公开测试，不包含隐藏 scorer 或参考实现。

### 3. 运行 Agent

- 使用独立 session ID。
- 从 Agent 收到题面时开始记录 wall time 和 usage。
- 不添加解题提示；任何人工消息都计入 `human_interventions`。
- Agent 完成、超时或 harness 失败后停止进程并冻结工作区。

### 4. 在 Agent 外部评分

```bash
PYTHONPATH=src python3 -m harnessbench evaluate \
  datasets/minimal-3/m1-reservation-repair \
  /tmp/m1-workspace \
  --private-root private/hidden-tests \
  --output /tmp/m1-evaluation.json
```

### 5. 合并运行指标

复制并填写 `examples/run-metadata.json`，然后运行：

```bash
PYTHONPATH=src python3 -m harnessbench assemble \
  /tmp/m1-evaluation.json \
  examples/run-metadata.json \
  --output /tmp/m1-result.json
```

## 指标解释

评测器负责：

- `completion_score`
- `ship_ready`
- `critical_failures`
- `capabilities`
- `optimizer_quality`

运行器负责：

- `wall_time_seconds`
- `model_active_seconds`
- 输入、缓存输入、输出和 reasoning token
- 实际 credits 与参考性的 API 等价成本
- tool calls、失败工具调用、测试循环和人工介入

不要把质量和成本压成一个总分。先比较 Invalid、关键失败和 ShipReady 数量；只有完成度接近时才比较时间、token 与 credits。

## 开发新任务

每道公开任务必须包含：

```text
TASK.md
task.toml
starter/
public-tests/
```

对应的私有 scorer 放在：

```text
private/hidden-tests/<task-slug>/
```

开发顺序：

1. 先写能力地图和权重。
2. 编写私有正确参考实现。
3. 编写只暴露接口和基本行为的公开测试。
4. 编写覆盖边界、失败、不变量、重启和回归的隐藏测试。
5. 对 untouched starter、参考实现和故意不完整的 mutation 运行 scorer。
6. 确认 starter 不达到 ShipReady、参考实现达到 ShipReady。
7. 冻结版本和哈希；改变评分语义必须提升 task 或 dataset 版本。

详细中文文档：

- [运行协议](docs/zh-CN/operations.md)
- [任务开发规范](docs/zh-CN/authoring.md)
- [指标协议](docs/zh-CN/metrics.md)
- [Agent/AI 指令说明](AGENTS.md)

## 安全边界

准备后的 Agent 工作区绝不能包含 `private/hidden-tests`、参考实现、同族题目的历史结果、凭证或可写 evaluator。Python CLI 只负责工作流隔离，不是操作系统安全沙箱；正式运行仍需在外层限制网络、文件系统、进程、CPU 和内存。
