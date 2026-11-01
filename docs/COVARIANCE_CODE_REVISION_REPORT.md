# 协方差检验代码修订报告（任务卡1）

日期：2026-10-21；方法版本：v1.1；单样本为主，独立双样本为推广。

## 依据与范围

- 方法：`docs/高维函数型协方差检验_完整方法_单样本与双样本.md`。
- DGP：`docs/高维函数型协方差检验_两套模拟数据生成与设置.md`。
- 执行范围：`docs/任务卡1`，已逐份完整读取。
- 本轮开始时Git工作区干净，基准提交 `5775687`。未创建分支/worktree，未提交或推送，未修改历史结果及任务卡2/Xue数学实现。
- 沿用Python、NumPy、pandas及现有common/simulation/tests目录，无新增依赖或调度系统。

## 实际调用链与核对表

`simulation.Main_one/Main_two` 与统一CLI → `simulation.covariance_experiments` → `simulation.data_generation` 生成一次数据 → `common.statistic_calculator_517` 检验 → 逐次JSON、场景汇总CSV；可选Xue对照复用同一个Y。

| 方法要求 | 文件/函数 | 原状与本次处理 |
|---|---|---|
| 无偏协方差、正确轴序 | `common/statistic_calculator_517.py:calculate_u_statistic_matrices` | 原实现正确，保留n−1及reshape后transpose |
| 一般确定目标、完整/局部集合 | 同文件 `covariance_one_sample` | 新增显式gamma0及布尔通道对mask；默认完整核，旧包装仍为零跨分量 |
| 全双时间最大绝对偏差 | 同文件单/双样本函数 | 保留直接协方差统计量，无学生化、积分或投影替代 |
| 原始乘子与经验外积中心化 | 同文件 `_centered_weighted_outer` | 显式扣除sum(xi)·qbar；不修改xi，不增加2或1/2 |
| 有限B判决 | 同文件 `_decision` | 去掉95百分位插值；按p<alpha允许计数求秩，处理并列和浮点边界 |
| 独立双样本 | 同文件 `covariance_two_sample` | 复用同一准备/加权核心，各组独立中心化，n−1/m−1，尺度sqrt(nm/(n+m)) |
| 输入/网格/空集合 | 同文件准备与校验函数 | 非有限数据、样本不足、目标/mask/乘子/网格不匹配报错，空集合不再返回0 |
| M1五基与谱 | `simulation/data_generation.py` | 修订生产生成器为phi1…phi5，无常数项，lambda=k^-2；保留旧投影基辅助函数供兼容 |
| M2实际网格增量 | 同文件 `_sample_components` | 含0、1；M−1个增量，方差为实际时间步长，零起点 |
| 支持、相关与噪声 | 同文件 `sparse_correlation/symmetric_sqrt/simulate_one` | 无放回抽s0/2条边，允许共享端点；每次重复固定支持；检查正定，不投影修复；独立标准差0.05噪声 |
| 稳定随机流 | 同文件 `make_rng` | SHA-256规范JSON、前8字节小端、基准20261021、replicate×13579、SeedSequence流/组隔离；无全局RNG |
| 正式20场景 | `simulation/configs/formal.json` | 两模型分别4水平+4功效+2维度场景；M30/B500/100重复/alpha0.05 |
| 冒烟隔离 | `simulation/configs/smoke.json`、`two_sample_smoke.json` | 另设小配置，正式参数不覆盖；双样本明确标识及不等组样本量 |
| 生产入口与保存 | `simulation/covariance_experiments.py`、`Main_one/Main_two.py` | 旧入口转接权威核心；逐次保存原始bootstrap、配置、真值、版本、环境、耗时，完成后汇总 |
| 失败与断点 | 同文件 `run_tasks` | 失败单独记录并抛出，不计成不拒绝、不删除分母；逐次结果先写临时文件再原子替换；resume校验版本/完整任务/重复编号/bootstrap/配套数值判决 |

## 数值变化及兼容性

旧式“中心化乘子×原始外积”与新式“原始乘子×中心化外积”逐次代数等价，改写本身不构成bootstrap尺度纠错。原协方差和轴序也正确。

真正影响新实验数值的变化包括M1基序、稳定随机流与新抽样序列、配套临界值规则；B默认从300统一为500，且alpha可显式指定。旧数据和旧实验输出不能重标为v1.1。

保留`covariance_test(Y, B=500, seed=None)`三元组接口，以及`multiplier_bootstrap`、`compute_Tn`、`calculate_u_statistic_matrices`。新单/双样本接口返回统计量、p值、临界值、拒绝指标、bootstrap序列、方法版本、分母、网格、索引和配置标识。固定乘子审计参数分别为`multipliers=xi`和`multipliers=(xi,eta)`，seed可接收局部Generator。

两生成器旧数据入口保留名称和主要返回键，并支持显式`task/replicate`；旧seed作为明确配置字段生成可复现新数据，不保证旧全局RNG数列。生产M1只接受冻结q=5,c=1,beta=2，不把旧q值悄悄映射成其他模型。第三模型生成器、Xue与HAR预处理保留原回归；HAR和第三模型调用的共享bootstrap核心采用新版本。

任务卡1统一驱动串行运行，保留Windows spawn下可调用的小任务接口。没有增加分块或并行数值算法，因此不额外构造分块测试。

## 已执行的核心验证

采用测试先行：核心先观察缺失接口失败；DGP先观察缺失模块/包装参数失败；实验契约先观察驱动缺失失败，再实施并验证。旧迁移测试中要求M1/M2及bootstrap与旧版逐位不变的断言改为当前规范独立数学验证；未通过放宽误差掩盖数值偏差。

```powershell
python -m unittest tests.test_covariance_v11 tests.test_generation_v11 -v
```

9项通过。核心参考使用n=7,m=11,p=3,M=4、非零均值/目标及完整、跨分量、局部集合，测试代码直接构造受试者四维外积，不调用生产内部函数构造期望值。float64容限atol/rtol=1e-10；实测最大绝对误差：

| 对象 | 最大绝对误差 |
|---|---:|
| 样本协方差、单样本/双样本观察统计量 | 0 |
| 单样本bootstrap全部9个值 | 2.6645352591003757e-15 |
| 双样本bootstrap全部9个值 | 1.7763568394002505e-15 |
| 各坐标H求和 | 2.4424906541753444e-15 |

覆盖均值平移、只读固定原乘子、全局RNG不变、全双时间、整块掩码、p>n、非法输入、并列值、B9/alpha0.8浮点边界及B500第476顺序统计量。DGP以独立SHA-256种子参考和固定创新矩阵计算M1/M2及噪声，容限1e-12；未把随机样本经验协方差接近总体设为硬性测试。

### 最终全链路验收

```powershell
python -m unittest discover -s tests -v
python -m compileall -q common simulation empirical tests
git -c core.safecrlf=false diff --check
python -m simulation.covariance_experiments --profile smoke
python -m simulation.covariance_experiments --profile two_sample_smoke
python -m simulation.covariance_experiments --profile smoke --resume
python -m simulation.Main_one --profile smoke --with-xue
python simulation/Main_two.py --profile smoke
```

- 全部21项测试通过，包含正式20场景集合的逐项精确比较、保存/汇总/复现、损坏断点拒绝、空任务报错、双样本n_X/n_Y汇总及Windows spawn；Xue旧概率约定、第三模型旧数据、HAR预处理等保留回归通过。
- 字节码编译与diff空白检查通过；普通沙箱首次编译拒绝写入既有缓存，按同一授权受控提权后检查成功，未修改文件权限。
- 单样本smoke共4场景、8份逐次JSON；独立双样本smoke共4场景、8份逐次JSON；所有记录包含统计量、p值、配套临界值、判决与bootstrap序列，CSV汇总已落盘。
- 已对保存的单样本结果执行CLI恢复；单元测试另验证恢复前后逐次JSON字节不变，错误的p值/不完整JSON被拒绝。
- 旧模块入口M1追加Xue对照与直接脚本入口M2各运行2场景、4份逐次JSON，分别位于`smoke/M1/with_xue/`与`smoke/M2/`，证明旧入口实际接入新核心。
- 两套主要smoke中H0/H1拒绝率均为0（每场景仅2次）；这仅是链路运行记录，不据此评价经验水平或功效，不要求小样本备择必拒绝。
- 正式配置准备完毕，完整20场景×100重复未运行，未创建正式结果目录或提交集群任务。任务卡1规定的数值一致性、输入校验、可复核输出及小规模链路验收均已满足；无剩余代码阻塞。

## 运行命令与输出

```powershell
# 单样本：两模型分别H0/H1，n24,p6,M8,B39,每场景2次。
python -m simulation.covariance_experiments --profile smoke
# 独立双样本：两模型分别H0/H1，nX20,nY28,p4,M8,B39,每场景2次。
python -m simulation.covariance_experiments --profile two_sample_smoke
# 保留旧入口及直接脚本运行。
python -m simulation.Main_one --profile smoke
python simulation/Main_two.py --profile smoke
# 正式20场景，仅准备命令，本轮不执行。
python -m simulation.covariance_experiments --profile formal --output results/simulation_v1.1_20261021/formal
# 同一配置和目录断点续跑。
python -m simulation.covariance_experiments --profile formal --output results/simulation_v1.1_20261021/formal --resume
```

可追加`--model M1/M2`限定模型，或`--config 路径`读取明确配置。`--with-xue`保留现有对照并共享本次数据，记录phi0…phi4、s=5及未在任务卡1审计的版本标签；任务卡2应完成其独立数学核对后再解释正式对照结果。

默认新输出位于`results/validation_v1.1_20261021/<profile>/`；每个完整任务SHA-256前16位为场景子目录，内含`replicate_000.json`等逐次文件。JSON的临界值`null`表示正无穷（有限B无法拒绝）。汇总文件为`all_experiments_results.csv`及各实验partial/results CSV，含完整配置、场景ID、拒绝率与MCSE。逐次记录含原始bootstrap值、C、零起始支持边、最小特征值、网格、噪声方差、版本、基准种子和哈希/流规则，以及NumPy/Python/平台/线程信息。

按模型筛选的默认输出额外进入`M1/`或`M2/`，启用对照再进入`with_xue/`，避免这些选择刷新另一套默认汇总；显式`--output`按用户指定目录执行。

恢复以同一配置逐次文件为依据，不依赖汇总CSV；变更任何完整任务字段产生新场景ID，已有文件默认拒绝覆盖，损坏或不匹配断点立即报错。无自动集群提交。

## 范围与理论边界

本轮不执行正式20×100模拟或完整HAR实证，不重新计算历史表。小规模验证证明给定公式、实现与链路的一致性，不证明高维水平控制、功效、连续域渐近性质或配对数据适用性。

既有文件写入曾遇沙箱权限拒绝，已暂停并报告；用户再次授权后受控提权审批通过，只写目标文件，未修改ACL。
