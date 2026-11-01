# 核对发现

- 规范位于 docs/高维函数型协方差检验_完整方法_单样本与双样本.md 与 docs/高维函数型协方差检验_两套模拟数据生成与设置.md；执行范围为 docs/任务卡1。
- 原样本协方差n−1、轴序、跨分量整块掩码正确；中心化乘子加权原外积与原始乘子加权中心化外积代数等价。
- 实际需修订：95百分位插值、全局随机状态、B默认值、一般目标/局部索引/双样本/输入校验；M1原含常数基，不符冻结phi1…phi5。
- 有限B临界值按p<alpha允许计数求秩，避免B9 alpha0.8浮点误差；默认B500应第476个。
- 原迁移回归对M1/M2及bootstrap逐位不变的断言需更新为当前规范行为；Xue/HAR/第三模型保持原回归。

## 任务卡2
- 最新docs/Xue方法_协方差检验完整提取.md已包含0–19节，执行卡为docs/任务卡2_Xue.md。
- 旧Xue未知均值、n分母、m=E[Z²Z²]−S²、轴序、d=ps极值尺度正确；实为cross零目标受限版，不是完整Xue-1S-EV。
- 需要补一般已知目标与对角项、LΓLᵀ、元数据与输入检查；旧np.maximum(m,eps)会静默修复退化，必须移除并明确失败。
- 既有正式cross配置不允许默默改成完整已知核假设；保留cross方法准确命名，主版需显式目标输入。固定Fourier矩形投影是项目约定，不是原论文样条拟合/自动选阶。
- 未发现已有Xue两样本、MB或BC；不新增可选版本，不把我们bootstrap叫Xue-MB。

- 任务卡2最终40项测试、编译和diff检查通过；主版系数/完整含噪声曲线目标CLI、原cross四场景8次有效0失败及恢复通过。
- 固定同观察最大deltaT=7.105427357601002e-15，判决0次改变；真实常数退化旧p约0.6165，新版明确失败并将p/reject置空。
- 已核验7份原核心/生成器/场景配置哈希不变；没有覆盖历史结果或启动完整模拟、实证和集群任务。
- Debug、第一性原理复核和精简完成；实际代码、40项验证、历史结果分类和重跑命令记录于docs/XUE_IMPLEMENTATION_AUDIT.md。
- 普通审批超时后正规受控提权完成，未改ACL；发现文档中文编码错误后改为ASCII转义与UTF-8明确写入并核验，未影响数值结果。

## 任务卡3
- 真实接口已确认：covariance_one_sample 支持完整gamma0/实际grid/Generator；run_xue_one_sample 支持实际grid和完整gamma0，三个s固定5/11/21。
- 新生成器、统计汇总与集群交付分工独立文件；主线负责版本/来源清单、统一驱动/配置及最终集成。
- 本地可用Python3.12解释器，目标集群为3.9.25；不得将本地冒烟标成已验证集群环境。

- task3最终科学边界：新增full_known_gamma0与旧20场景cross完全分开；新8规格s21覆盖全部生成方向，legacy Brownian仍可能有截断，报告区分；smoke不提供优势结论。
- 正式默认探索25×50=1250数据，确认最多6000，最多8并发；资源映射按真实B500基准和2倍安全因子算分块/时限，超过用户预算即停；真实生产测量尚未执行。
- 最终73项回归和干净包50份smoke全部通过，目标3.9.25/2.0.2/1.13.1未在本机冒充验证，集群入口先校验版本与smoke。

- 环境登记共享锁应阻塞等待，记录锁应非阻塞拒绝重复写；两种语义不能共用非阻塞选项。
- 旧冻结批次无需重算1200或改来源hash：独立操作入口复用原release和调度函数，仅把允许范围内实际数组并发改为1并完整记录；原科学checkpoint和confirm lock身份保持旧代码来源。

## Task4
- Existing source bytes frozen in doc/task4_frozen_before.json before changes.
- No remote connection, cancellation or formal simulation authorized in development.

## Task4 limits
- Local Python3.12 validation is distinct from compute-node Python3.9.25 runtime checks.
- SSH connection fields and six site resource budget fields remain user-filled unknowns; launch dry-run reports them.
- Task4 scientific results do not yet exist; development smoke cannot evidence power.

## Empty remote results report
- No task4 remote logs uploaded; root cause remains unverified. squeue listing alone does not prove worker success.
- New external adapter must not edit frozen release or resume scientific records under new hashes.

## Task5 design decisions
Taskcard is approved implementation specification. Pilot 13 nulls x500 + 56 alternatives x50 =9300. Three mandatory anchors 5700; optional one model at two shapes adds3800; total15000/18800. Xue alarms never stop planned research. Confirm H0/H1 random namespaces separate; exact CP target band [.03,.07], fixed full family multiplicity. No production benchmark/local large shape during development.

- Final task5 policy separates statistical evaluation from technical progression: every anchor always runs; incomplete confirmation stays incomplete. Worker node path/platform are logged independently, while scientific versions/BLAS/threads remain fingerprinted. All 27 legacy sources/archive hashes preserved.

- Deliverable source identity 8e6d441ad5f326bb52e7a6a39ccd72e1a30b58f1baadb3407897a3374519d348; 27 old source/archive hashes unchanged. Actual cluster fields six resource budgets and SSH remain unknown; Bash manual deployment can fill resource values from previously working task4 config without changing old run.

## Task6
Taskcard permits complete report extraction if local machine-readable results absent. Matplotlib/scipy/pandas and XeLaTeX available; PyMuPDF missing in all three local environments; local QA dependency install requires network escalation.

Task6 final: negative-label correction counts 18 positive/15 NI-only/6 negative/6 unresolved. CSV exploration adjusted family m168 differs from requested report m1; source fields retained and display recomputed deterministically. Manuscript normalized coefficient sum/difference explicitly includes sqrt(2). 15 original input hashes unchanged; no scientific missing input.

Task7: actual inputs data/har; local static corruption independently verified; dynamic3285 windows with2937/3284 half-overlaps; historical dynamic pool recovered to6.22e-15. No identifiable subject/activity mapping.


Official files found at data/har/UCI HAR Dataset/UCI HAR Dataset; source ZIP retained. README identifies 30 volunteers, six activity labels, subject-based split and 128-point 50%-overlap signals; dataset channels require matching to old CSV before declaration.


Old dynamic maps exactly to 3285 train dynamic windows and 21 real people, zero ambiguity across10299 unique source windows. Old static953 intact rows match all-source per-subject static mean exactly; independently reconstructed30-person file uses actual IDs, with no claim about unreadable old tail. Main native128-point30-person analyses: Ours all nonreject; Xue rejects locomotor and lying groups; no correctness/power conclusion follows.
