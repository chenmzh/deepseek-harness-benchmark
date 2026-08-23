# DeepSeek Harness Benchmark

[English](README.md) | 中文

这是一个确定性、仓库级的测试集开发库，用来测量模型 harness 的设计变化如何影响项目完成度、可靠性、运行时间、token 使用量和成本。

> 当前状态：早期开发。`minimal-3` 是第一个已实现的**公开开发探针集**，用于低成本的 harness 迭代和回归测试，不能作为独立的密封选择集。更大的密封测试集仍处于规格阶段，等待探针框架稳定。

## 核心原则

- 评测完整的“模型–harness 配置”，而不是孤立的模型名称。
- 项目完成度和关键失败是质量门槛；时间、token 与成本是独立效率维度。
- 运行期间 evaluator 和参考实现不能进入被测 Agent 的工作区。
- 真正用于选择和最终确认的 evaluator 必须保存在被测 Agent 无法访问的仓库和环境之外，直到比较结束。
- 每次运行前冻结题目、evaluator、资源限制、结果协议、指令、preset、plugin、harness 版本和运行模式。
- 探针模式不重跑有效失败；确认模式只执行查看结果前预先声明的重复次数。
- 优先使用本地确定性测试，避免把 LLM Judge 作为 ShipReady 的关键门槛。

## 仓库结构

```text
datasets/                  公开题面、starter 和公开测试
private/hidden-tests/      公开开发 evaluator；绝不能复制到 Agent 工作区
private/reference-solutions/ 开发参考实现；不构成密封证据
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

`minimal-3` 适合频繁执行一次性探针运行。某道题的 evaluator 失败一旦影响 harness 修改，该题只能继续用于回归测试，不能再作为选择最终 harness 的独立证据。

任务可在 `task.toml` 中声明 `required_capabilities`。这些能力是 ShipReady 硬门槛：总分不能补偿会让产物根本无法交付的能力缺失。

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

对应的开发 scorer 放在：

```text
private/hidden-tests/<task-slug>/
```

开发顺序：

1. 先写能力地图和权重。
2. 识别缺失后会使产物根本无法交付的能力，并将其声明为 `required_capabilities`。
3. 编写私有正确参考实现。
4. 编写只暴露接口和基本行为的公开测试。
5. 编写覆盖边界、失败、不变量、重启和回归的隐藏测试。
6. 对 untouched starter、参考实现和至少两个故意不完整的 mutation 运行 scorer；mutation 必须覆盖每个必需能力。
7. 确认 starter 不达到 ShipReady、参考实现达到 ShipReady。
8. 冻结版本和哈希；改变评分语义或 ShipReady 门槛必须提升 task 或 dataset 版本。

详细中文文档：

- [运行协议](docs/zh-CN/operations.md)
- [任务开发规范](docs/zh-CN/authoring.md)
- [指标协议](docs/zh-CN/metrics.md)
- [Agent/AI 指令说明](AGENTS.md)

## 安全边界

准备后的 Agent 工作区绝不能包含 `private/hidden-tests`、`private/reference-solutions`、同族题目的历史结果、凭证或可写 evaluator。Python CLI 只负责工作流隔离，不是操作系统安全沙箱；正式运行仍需在外层限制网络、文件系统、进程、CPU 和内存。

本公开仓库中的 `private/` 只是开发探针的工作区隔离边界，不是真正的保密边界。用于选择和最终确认的 evaluator 与参考材料必须保存在被测 Agent 无法访问的位置；运行前记录其哈希，比较结束后可按需要公开。
