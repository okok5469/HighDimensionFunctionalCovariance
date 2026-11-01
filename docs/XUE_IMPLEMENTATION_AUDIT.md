# Xue 实现审计与必要补充

日期：2026-10-21。执行依据：`docs/任务卡2_Xue.md` 与包含第0–19节的最新版 `docs/Xue方法_协方差检验完整提取.md`。单样本主版本是该规范新增的 **Xue-1S-EV**，不是把原论文两样本算法称作单样本原法。

## 总结论

上一版需要局部修订和必要补充，但不是整套数学都写错。旧实现是**未知均值、系数空间、仅跨通道零协方差、解析极值校准的单样本受限版本**。其n分母、中心化、乘积方差代数式、正确轴序、d=ps及Gumbel尺度均有明确依据；它没有实现完整已知目标的Xue-1S-EV，也没有实现Xue两样本原法。

本轮保留并准确命名受限版本为`Xue-1S-EV-cross-zero`，移除静默epsilon钳制，补齐完整目标主版本、同一固定L的目标投影、合法性/退化检查及结构化结果，接通既有模拟、HAR和历史股票调用方的必要接口与标签。未新增MB、BC、自动选阶或另一套两样本研究框架。

**原假设不能偷换。**既定正式配置只规定跨通道协方差为0，各通道自协方差未知；因此`--with-xue`保留cross问题，不能默默补入模拟器真值、样本自协方差或完整零矩阵后冒称主版本。完整主版本必须显式提供确定的`gamma0`或同表示下的`sigma0`。对显式Y+gamma0输入，既有驱动也将同一数据、同一完整目标传给现有时间域检验；原cross正式场景与生成方案均不改变。

## 基准、范围与入口

本轮基准Git提交为`5775687`，任务卡1未提交的代码、配置、文档和验证输出均予保留；未创建分支/worktree，未提交或推送。未改变`common/statistic_calculator_517.py`、M1/M2生成器及三份既定场景配置的内容；没有为了得到某个拒绝率而调阈值、改分布或改数据。

| 入口 | 实际问题与当前名称 | 处理 |
|---|---|---|
| `common/statistic_calculator_xue.py:compute_Tn_xue` | 原受限cross系数统计量 | 保留兼容名称，严格检查，不能解释为完整主版本 |
| `common/xue_helper.py:run_xue_test` | 原Fourier投影+cross三元组 | 保留兼容；明确方法身份，退化抛错 |
| 同文件 `run_xue_cross_test` | `Xue-1S-EV-cross-zero` | 结构化结果供生产调用，稳定校准与完整元数据 |
| `common/statistic_calculator_xue.py:xue_one_sample` | `Xue-1S-EV`，完整已知系数目标 | 新增主版本系数入口，保留上三角含对角 |
| `common/xue_helper.py:run_xue_one_sample` | 实际固定L下的完整已知目标 | 新增曲线/系数适配；目标与实际数据同变换 |
| `simulation/covariance_experiments.py` → `Main_one/Main_two` | 既定cross模拟比较 | `--with-xue`接通明确受限版本；原配置不改 |
| 同一驱动 `--xue-input` | 显式NPZ已知目标主版本 | 真正执行、保存和汇总完整主版本，无额外生成一组数据 |
| `simulation/Main_three.py` | 高斯创新、跨观测MA(1)第三模型cross比较 | 明确受限标签与理论边界；失败立即暴露 |
| `empirical/Main_HAR_empirical.py` | HAR处理后cross检验 | 标签、版本、失败传播；不把活动标签当已知零协方差 |
| `archive/stock_empirical/xue_test.py` | 历史股票系数cross检验 | 复用权威cross核心，保留返回键；不触发下载/合成回退 |

搜索真实函数与调用链后未发现现有Xue-2S-EV、Xue-MB或BC实现；我们的独立双样本bootstrap不是Xue两样本，时间域multiplier bootstrap也不是Xue-MB。本轮因此没有新增这些可选实现。工作区未找到`s11425-023-2441-0.pdf`，本次运算核查依照用户已提供的最新版完整提取文档，不虚称核对了缺失PDF。

## 逐项核查表

| 代码位置／入口 | 现有行为 | 对应文档章节／公式 | 判定类别 | 是否修改及理由 | 影响范围 |
|---|---|---|---|---|---|
| `compute_Tn_xue`均值/协方差 | 按列估计均值，S=ZᵀZ/n | §4.1–4.2、§16.5 | 符合定义／数学等价 | 保留n，绝不全局换成n−1 | 所有Xue调用；我们的n−1不变 |
| 同函数乘积方差 | E[Z²Z²]−S² | §4.5–4.6、§16.5 | 符合定义／数学等价 | 保留定义；严格检查数值和退化，不混成系数方差 | 逐元素学生化 |
| 同函数`maximum(m,eps)` | common阈值1e−10，stock阈值1e−12 | §16.12、§17.8、任务卡§4 | 明确计算偏差 | 去掉静默钳制；必要分母无效时明确失败坐标，不产生有效p或不拒绝 | 触发钳制/退化的旧结果 |
| 同函数cross掩码 | 排除整块同通道，包括其跨基项 | §5.2、§16.6、§19.1 | 已明确标注的其他版本 | cross运算保留，纠正笼统Xue标签；主版另含所有对角/跨基项 | 既定cross场景可继续，但非主版 |
| 同函数零目标 | 无目标参数，直接nS²/m | §16.2–16.6 | 必要功能缺失 | 新增完整sigma0差值，合法对称PSD检查 | 完整单样本主版本 |
| 同函数维度/s | s可能与实际输入末轴不一致 | §16.12 | 必要功能缺失 | 3D明确p/s；flat必须提供p/s；d>1，样本足够 | 防止错误极值中心化 |
| `xue_critical_value` | 标准Gumbel常数与T阈值 | §5.4、§16.7 | 符合定义／数学等价 | 保留常数和尺度，稳定log1p计算；T>tau拒绝 | 普通值相同，极端alpha数值更稳 |
| `xue_pvalue` | 模拟用1−F，HAR用expm1 | §5.5、§16.7 | 符合定义／数学等价 | 保留显式legacy追溯分支；生产使用稳定尾概率并防溢出 | 极小尾概率减法消减 |
| `project_to_fourier_basis` | 固定phi0起始、闭网格、1/M矩形投影 | §3.2–3.3、§16.4 | 已明确标注的其他版本 | 不改变原投影，记录为项目固定约定；不冒称作者三次样条/自动选阶 | 保留原数据表示 |
| `run_xue_one_sample` | 原无数据/目标同投影 | §16.3–16.4 | 必要功能缺失 | L=I⊗Bᵀ/M或显式固定L；Sigma0=L Gamma0 Lᵀ；正确交错轴序 | 非零、跨基、含噪声目标 |
| 已在同基下的sigma0 | 原无一般目标入口 | §16.4、§16.12 | 必要功能缺失 | 直接使用，不再二次投影；缺目标/二义目标明确拒绝 | 系数及曲线主版输入 |
| 目标来源 | 不具备主版完整已知目标信息 | §16.11 | 依据不足，需记录或补齐输入 | 不从当前/训练样本估计目标后忽略估计误差 | full主版须显式确定目标 |
| 比较保存/汇总 | 旧结果只有Xue数值，无严格身份/失败统计 | §19.1–19.3 | 必要功能缺失 | 记录方法、版本、p/s/d、校准、均值/分母、目标/投影、状态；失败不计有效不拒绝 | 新生产结果及重跑追溯 |
| 固定d/重尾/HAR依赖 | 可以算出统计量不等于条件成立 | §7、§17.3、§17.8 | 计算可执行，但理论适用受限 | 记录边界，不改生成器/阈值补偿 | 结果解释而非自动有效性证明 |

## 输入和使用约定

完整系数主版调用`xue_one_sample(scores, sigma0, p=..., s=...)`；未知均值默认由样本估计，n≥3，d=ps>1。扁平列顺序为通道优先、通道内基序号；3D为(n,p,s)。已知均值仅在显式提供真实已知均值且标明模式时使用，不从模拟器内部偷偷取真均值。

完整曲线入口`run_xue_one_sample(Y, gamma0=..., s=5)`或`sigma0=...`二选一。gamma0轴为(p,p,M,M)，展平先transpose(0,2,1,3)；目标是实际观测协方差，含测量噪声时必须包含其同通道同网格方差。固定自定义L必须与数据同一维度/顺序。已知sigma0直接使用；原始目标左上角不是系数目标。

原Fourier投影保持phi0…phi4、s=5和1/M；这与M1生成器phi1…phi5不同，不能把q=s=5说成相同基空间，也不能用真实潜在系数只给Xue增加信息。本轮没有假定未提供的样条结点、自动候选集合、GCV或作者选阶规则。

`--xue-input`读取无需pickle的NPZ，二选一：

- `scores`加`sigma0`，flat还需标量`p,s`；只执行系数主版，不宣称可与未提供的时间域数据比较。
- `Y`加`gamma0`或同表示`sigma0`，可附`grid,s,operator`。Y+gamma0时，也调用原时间域核心在相同完整目标上检验；可附`B,bootstrap_seed`控制该核心的既有bootstrap输入。

不合法目标、样本或退化分母不会被eps修复；结构化核心失败含status、failure_reason及坐标，p/拒绝结论为空。兼容三元组与批量入口用清楚异常停止。驱动记录失败原因，不把失败记成不拒绝或静默从分母删除；成功汇总明确有效次数和共同有效次数。

## 历史结果影响与重跑清单

| 历史结果／配置 | 旧方法实际含义 | 发现的问题或差异 | 数值是否受影响 | 是否需重跑 | 原因与建议命令 |
|---|---|---|---|---|---|
| `results/validation_v1.1_20261021/smoke/M1/with_xue/`四份逐次JSON | 可确认来源的旧cross版 | 原标签写任务卡1未审计，不是full主版 | 同固定观测的有效普通分母下数学等价；极尾算术可能末位不同 | 可沿用为旧cross历史；要当前严格版本则新目录重跑 | `python -m simulation.covariance_experiments --profile smoke --model M1 --with-xue --output results/xue_audit_v1_20261021/rerun_M1_cross` |
| `results/simulation/model1/*.csv`、`results/history/with_xue/all_experiments_results_model{1,2}.csv` | 旧cross聚合结果 | 无逐次m/钳制触发及完整版本证据 | 是否触发eps/失败无法由汇总确认；M1生成器还已在任务卡1更新 | 待核实；用于当前实现比较需重跑 | `python -m simulation.covariance_experiments --profile formal --with-xue --output results/xue_audit_v1_20261021/formal_cross`；本轮不执行 |
| `results/empirical/har/experiment_results/`、`archive/results/har_first_version/` | 历史HAR cross及其处理约定 | 无完整逐次版本/分母诊断；活动标签和重叠窗口不能证明iid H0 | 本轮未据少数样本推定全部旧结果有效/失效 | 来源待核实；要当前严格cross输出需重跑既有实证流程 | `python -m empirical.Main_HAR_empirical`，新输出在HAR版本子目录；本轮不批量执行 |
| `archive/results/legacy/empirical_results*`等股票结果 | 历史独立stock cross实现 | 原eps为1e−12，来源/目标/缓存映射信息不全，旧流程可能下载或回退合成 | 无逐次证据，待核实 | 暂不自动重跑 | 先确认真实缓存、样本和预处理；已补单次系数入口可用`archive.stock_empirical.xue_test.xue_test(a)`复核，不运行下载/合成回退 |
| `results/history/simulation/`及`archive/results/legacy/model*`不含Xue列的表 | 原本文方法或其他历史模拟 | 非本次Xue修改路径 | 不因本轮Xue修改而改变 | 可沿用其原历史身份 | 不把任务卡1的独立数值变更归咎于Xue，也不重标历史版本 |
| 第三模型M3的旧Xue汇总 | 高斯布朗创新产生跨观测MA(1)依赖的cross EV数值 | 个体间独立的EV前提不直接覆盖该MA(1)依赖 | 计算与理论要分开；重跑也不会自动修复理论条件 | 源信息不足者待核实；当前版本需要时另跑 | `python -m simulation.Main_three`沿用旧参数、新版本目录；不为改善size改变DGP，本轮不完整运行 |
| 任何被发现m≤0/非有限、eps钳制后仍给有效p的记录 | 数值伪修复后的输出 | 明确计算偏差 | 可能改变Q、p和拒绝/有效重复数 | 需重跑；重跑应失败或明确报告有效子集，不能把失败保留为不拒绝 | 必须用对应原观测/真实配置和新严格入口；只有汇总而无观测时无法精确恢复 |
| 完整主版Xue-1S-EV | 新增已知目标检验 | 旧cross数据表没有同版旧数值 | 属新增结果，不是给旧结果改标签 | 需要新增结果 | `python -m simulation.covariance_experiments --xue-input 已知目标输入.npz --output 新目录` |

既定JSON配置中的旧`xue_version`字段保留为**原任务哈希/数据种子标识**，避免修改它后生成另一批观测；实际新方法身份以逐次结果的`method`、`implementation_version=xue-audit-v1`及新汇总版本为准。不会把旧断点接成新Xue版本，也不会覆盖旧结果。

## 验证与限制

已完成的独立参考、固定观察对照、实际入口与40项回归证据见下节；正式和完整实证未运行。

EV成功计算不代表理论条件经样本检验成立：主版本要求独立个体、确定表示、非退化乘积方差、尾部与乘积依赖/增长条件；固定p,s不因增加n就自动达到Gumbel极限；本项目M3跨观测MA(1)依赖、HAR窗口依赖、有限截断遗漏和选阶误差需独立讨论；若未来引入t4系数，其四阶矩问题是另一项边界，不能误称当前M3分布。MB可在固定维度有限四阶矩场景作为后续另项比较，BC可另做敏感性分析，但不能用它们掩盖未知目标、退化或重尾问题，本轮未添加。


## 最终验证证据

已完成40项测试、编译与diff空白检查；没有启动正式模拟、完整实证或集群任务。

```powershell
python -m unittest discover -s tests -q
python -m compileall -q common simulation empirical archive/stock_empirical tests
git -c core.safecrlf=false diff --check
python -m simulation.covariance_experiments --profile smoke --with-xue
python -m simulation.covariance_experiments --profile smoke --with-xue --resume
python -m simulation.covariance_experiments --xue-input results/xue_audit_v1_20261021/inputs/reference_scores.npz --output results/xue_audit_v1_20261021/reference_scores
python -m simulation.covariance_experiments --xue-input results/xue_audit_v1_20261021/inputs/full_known_M1.npz --output results/xue_audit_v1_20261021/full_known_M1
```

完整日志：`results/xue_audit_v1_20261021/unittest.log`，最终为“Ran 40 tests / OK”。M3故意注入的退化ValueError由assertRaises验证通过，不是测试失败；核心5项、投影6项、调用方4项、驱动4项，加上保留的21项回归全部通过。

主要位置：`common/statistic_calculator_xue.py:xue_one_sample`（164行）、`xue_cross_zero`（174行）；`common/xue_helper.py:projection_operator`（62行）、`run_xue_one_sample`（82行）、`run_xue_cross_test`（152行）；`simulation/covariance_experiments.py:run_xue_input`（263行）。

### 精确参考与目标适配

| 任务卡n=4,d=2参考量 | 实测 |
|---|---:|
| Q | 1.393822393822394 = 361/259 |
| T | −1.7452792489990516 |
| p_EV | 0.3795921950507266 |
| argmax（0起始） | (0,0)，对应任务卡(1,1) |
| tau_0.05 | 2.716219070555093 |
| 判决 | 不拒绝 |

S、m与三个上三角q对任务卡精确分数的最大绝对误差均为0；Q/T/p按1e−12容差通过。原迁移测试逐位相等产生3.552713678800501e−15舍入差异，已改为明确atol/rtol=1e−12的数学等价检查，独立精确参考测试保留。不存在为通过测试而改动统计定义。

非平凡固定L测试使用不同p/M/s、非零非对角目标，独立核对数据与目标的相同变换及观测噪声项；另覆盖系数目标不二次投影、目标对称PSD容差、缺失/非法目标、复数拒绝、已知均值模式、极尾与极端alpha无溢出、RNG不变。

实际`full_known_M1`复用既有M1 smoke观测(n=24,p=6,M=8)，将既定H0公式的**完整含噪声观测目标**显式保存后输入。它是完整目标接口验证，不把原cross正式场景重新命名；Xue只得到同一Y的投影，未获真实潜在系数，两方法均从样本估计均值。

| 方法 | 统计量 | p值 | 判决 |
|---|---:|---:|---|
| Xue-1S-EV（d=30） | Q=11.782650882883086，T=−0.5980111030639939 | 0.23584929045682143 | 不拒绝 |
| 现有时间域完整目标检验（B=39） | 7.715104012490267 | 0.525 | 不拒绝 |

同一Y、gamma0及alpha进入两个核心；输出保存实际L、sigma0和时间域原始bootstrap值。两者统计量尺度不同，不能比较临界值大小解释优劣。

### 同一观察的新旧对照与真实失败

`baseline_same_input.json`记录HEAD旧源代码哈希、任务、输入SHA-256与旧数值；`comparison_same_input.json`逐项记录新旧对照。M1/M2各选H0/H1的replicate=0共4份固定观察，所需m最小值约1.40e−5至3.59e−5，未触发1e−10钳制；最大|delta T|=7.105427357601002e−15、最大|delta p|=7.494005416219807e−16，判决改变0次。这证明这些有效输入下为数学等价整理，不证明所有历史输入都未触发钳制。

另只读检查HAR H0缓存Y_pool.npy（285,6,48），该固定输入cross所需m最小值3.5582013909243534e−5，也未触发钳制；不据此认证全部旧抽样或已知H0。

常数输入(n=4,p=2,s=1)的真实退化验证：旧cross钳制后T=−3.1391016428214455、p=0.6164775137502865并报告不拒绝；新cross返回`degenerate_product_variance`、失败坐标(0,1)，p/reject为空。完整主版文件入口同样保存失败，`degenerate_scores/xue_summary.csv`明确n_total=1,n_valid=0,n_failed=1，然后抛出清楚异常，未产生有效不拒绝。

### 原场景、恢复与规模

`smoke/with_xue/`实际完成原M1/M2、H0/H1四场景，每场景2次，共8次有效、0失败，共同有效次数各2；本次两方法均0次拒绝。新版实际恢复命令通过；旧断点缺少当前方法/版本/status会被拒绝。驱动测试确认失败记录原因后停止，不能当作不拒绝或从分母静默删除。每场景仅2次，不把它当可靠水平/功效估计，也不要求每个备择必拒绝。

本轮未额外启动Monte Carlo零假设校准：固定观察有效cross判决未变化，完整主版为新增方法，未取得需要进一步解释的已证实size异常；小验证不替代理论。

### 本轮实际文件与可追溯性

- `common/statistic_calculator_xue.py`：主版/严格cross、稳定EV、合法性与退化诊断。
- `common/xue_helper.py`：保留旧投影，补L、匹配目标、完整/受限入口。
- `simulation/covariance_experiments.py`：同一驱动接通两种明确问题，完整目标接口复用原时间域核心，版本/失败保存及汇总。
- `empirical/Main_HAR_empirical.py`、`simulation/Main_three.py`、`archive/stock_empirical/xue_test.py`：真实生产调用改为权威严格cross、稳定校准及T阈值判决，补标签/维度/理论限制、版本目录和失败传播；stock公开校准函数也复用稳定核心。
- `tests/test_xue_core.py`、`test_xue_projection.py`、`test_xue_callers.py`、`test_xue_workflow.py`新增针对性测试；`tests/test_project_structure.py`只调整已证实的舍入回归要求；README和本报告更新说明，工作记录仅在doc/。

`implementation_manifest.json`保存实际源代码哈希和实现版本。我们的517核心、M1/M2生成器及三份既定配置共7个文件SHA-256与任务2开始相同；任务卡1未提交工作得到保留。未覆盖历史结果或启动完整重跑。

没有剩余代码阻塞。若把原cross正式比较改为完整已知核研究，仍须另行明确完整确定目标及研究问题；本轮不替用户猜测这一统计选择。

既有文件的普通自动审批多次超时，核验后在相同授权范围内正规受控提权重试成功，未修改ACL；无未解决权限阻塞。最终文档检查另发现命令行中文编码导致替换未生效/追加乱码，已改用ASCII转义后明确按UTF-8写入并核验内容；计算结果和测试日志未受影响。
