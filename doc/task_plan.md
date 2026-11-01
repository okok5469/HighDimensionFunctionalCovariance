# 任务卡1：协方差检验 v1.1

## 目标与边界
修订当前 common、simulation 的本文检验与两套生成器，保留 Xue 数学实现与旧结果；不启动20场景正式实验，不创建分支或提交。

## 阶段
1. 规范、调用链、Git现状核对：complete。
2. 核心独立参考测试与最小修订：complete（core）。
3. 生成器确定性测试与修订：complete（dgp）。
4. 正式配置、已有入口接入、逐次保存与冒烟：complete（主线）。
5. 回归、独立复核、报告：complete。

## 最终验收
21项测试、编译、diff空白检查通过；单样本/双样本各4场景8份逐次输出；旧模块/直接脚本与Xue保留对照链路通过；CLI恢复成功。报告在docs/COVARIANCE_CODE_REVISION_REPORT.md。正式20×100未运行，无未解决阻塞。

## 决策
沿用 common/statistic_calculator_517.py 作为唯一统计核心；保留三元组旧接口；M1/M2旧入口接入同一版本化实验驱动，正式配置和smoke配置分离。两份完整规范及任务卡已指定设计、数学和验收，普通实现已获用户授权，无需再确认。

## 环境
上一轮Git缺失，用户上传后本轮git status成功且初始工作区干净。

## 任务卡2（2026-10-21）
目标：按新版Xue规范0–19核查真实实现，保留正确cross版本、补完整已知目标Xue-1S-EV及同一固定L目标投影，必要局部修改、小规模验证、XUE_IMPLEMENTATION_AUDIT.md；不启动正式/实证重跑、不添加MB/BC/2S研究。

阶段：
1. 规范、旧方法身份与调用链核对：complete。
2. 系数核心与投影适配测试先行：complete（core、dgp）。
3. 既有调用方标签/失败传播与比较保存：complete（audit、主线）。
4. 独立数值与端到端小验证、历史影响报告：complete。

边界：任务卡1未提交改动全部保留；517核心、生成器、正式场景和随机任务配置不改。cross复合零假设不等于完整已知核，禁止用样本自协方差或模拟器真值偷偷补充对角目标。主版显式接收确定目标，既有cross场景准确标为受限版本。

任务卡2验收完成：40项回归、编译、diff、主版/受限版真实入口、失败状态和恢复均通过；报告已交付，无代码阻塞，正式与完整实证未运行。

## 任务卡3（2026-10-22）
设计依据：docs/任务卡3_扩展模拟模型与集群运行.md 已明确DGP、方法、选择规则、接口边界和验收，用户要求直接执行；沿用现有架构新增 task3 命名空间，不改核心、不创建分支或提交。
阶段：1.依据与接口核对 in_progress；2.生成器/确定性验证 pending；3.共同输入/计划/原子恢复 pending；4.汇总/锁定/确认 pending；5.集群与打包 pending；6.干净解压冒烟/最终验收 pending。
执行边界：仅必要测试和小规模smoke；不连接或提交集群、不本地执行完整B500大形状基准/探索/确认；目标Python3.9.25、NumPy2.0.2、SciPy1.13.1，保留既有工作区改动。

## 任务卡3最终状态（2026-10-22）
阶段1–6全部complete：依据/接口、生成器与真值、共同输入/恢复、汇总选择/确认、集群打包、最终ZIP干净解压冒烟均完成。
交付：dist/covariance_task3_v1_20261022.zip、同名.sha256、submit_task3.ps1、cluster_config.example.json；实际验收证据dist/task3_validation_20261022.json。
最终73项全量回归通过；包56成员整体/逐文件校验通过；最终包在干净目录实际运行25场景50份smoke，0失败；包外四文件独立PowerShell dry-run通过；编译、Python3.9语法和diff检查通过。
边界如任务卡：本地验证Python3.12.8/NumPy1.26.4/SciPy1.16.1；原myenv目标运行与完整B500资源基准待用户启动计算节点阶段验证；没有大规模探索/确认、网络连接或集群提交。

## 集群并发锁故障（2026-10-22，恢复处理中）
用户提供真实worker日志确认environment.lock使用非阻塞fcntl.LOCK_NB，正常争用导致BlockingIOError开头退出；pyyaml仅NumPy配置显示警告，不是根因。pilot1250中1200有效，50missing，不能反复resume或覆盖原冻结release。
最小修复：record_lock增加blocking参数，环境登记使用blocking=True，重复记录写锁仍非阻塞。测试先行，8真实进程复现失败后修复通过；不改统计核心、DGP、种子和判决。
独立运维恢复入口在旧release之外复用原调度代码，以允许的%1并发补缺并继续阶段，保留原config/controller_state/封印/来源哈希，记录独立恢复审计；新锁实现另行打包，不替换旧批次源码。
阶段：锁缺陷修复与并发回归 complete；独立恢复入口/验证 in_progress；固定版交付 pending。

集群并发锁故障阶段全部complete：锁等待修复、81项回归、独立串行恢复（原科学来源不变）、原ZIP dry-run和新包干净目录8进程验收完成。实际集群恢复由用户上传新入口后执行，本机没有远端操作；旧1200记录和旧发布包不修改。

恢复入口v2：旧作业squeue按ID查询返回非零的适配缺陷已在包外独立工具修复；11项离线测试及Python3.9语法/CLI检查complete。用户上传v2后执行实际旧批次恢复，原科学来源冻结不变。

## Task4 (2026-10-23)
- Design: authorized task card4; fixed methods, bounded 600/750 exploration, <=2200 confirmation.
- In progress: isolated generators/selection, workflow, cluster/package.
- Pending: integration, tests, smoke, frozen hashes, clean ZIP verification.

## Task4 completed
- Isolated source, strict search policy, two-peak DGP, bounded workflow and independent cluster delivery implemented.
- 26 new tests + 45 task3 regressions passed; final-source B3 one-dataset smoke and replay passed.
- Frozen 8 sources + two historical ZIP checksums unchanged.
- No remote activity or formal exploration/confirmation.

## Task4 shell delivery (2026-10-24)
- User requests direct sh submission and visible persisted results.
- Implement external shell/batch adapter, reuse frozen release and existing checkpoints, no remote action.
- Validate bounded execution, locks, fail-fast, logs and single-command restart.

## Task5 (2026-10-24)
Authorized full taskcard5 design. No architecture replacement, no branches, commits, remote operations or formal local simulations.
1. Context/design and frozen baseline complete.
2. Generator, fixed design, cluster adapters in progress (delegated isolated files).
3. Main workflow/summary/report integration in progress.
4. Targeted tests, small smoke, Python3.9 and clean immutable ZIP verification pending.

## Task5 final verification
Phases 1-3 complete: adapters/design, workflow/report and cluster/package implementation. 89 tests passed; 5 actual B3 smoke datasets plus two explicitly small B3 benchmarks passed. Phase4 release sealing and clean unpack verification in progress.

## Task5 delivery complete
All four development phases complete. Immutable 104-member Task5 ZIP and SHA256 built; clean unpack verified all bytes, 45 packaged tests and real 5-dataset B3 smoke/replay passed. Statistical study and production resource benchmarks remain user-started compute-node work, not development completion claims.

## Task6 (2026-10-26)
Approved taskcard: paper-only deterministic build; legacy inputs frozen. Data, manuscript, geometry delegated; main owns statistical figures, integration, final ZIP. No Monte Carlo/bootstrap/cluster operations.
1. Intake complete; 2. data and manuscript in progress; 3. plots/QA pending; 4. portable rebuild/LaTeX/ZIP pending.

## Task6 complete
Data/manuscript/geometry/statistical plots complete. 356 method rows and 213 paired comparisons verified; four main and ten supplement figures audited; 9-page XeLaTeX preview compiled/rendered. Portable clean ZIP full rebuild passed with author texts preserved and derived tables byte-identical. Legacy 15 input hashes unchanged. No new simulations or remote actions.

## Task7
901 historical dynamic analyses and 3604 method results complete; static corrupt and real subject mappings absent, main branches blocked. Final delivery validation in progress.

Task7 available work complete: local audit, 901x4 actual diagnostics, four exported figures and all rendered QA, reports and SHA256 package. Subject-level branches remain blocked by genuine static corruption and absent verified real-subject/activity mapping. Integrated command executed successfully; 9 tests and unchanged frozen sources verified.


Task7 continuation: new official UCI files supplied. Source/ZIP/old-CSV matching, subject runner and figures delegated in isolated v2 namespace. Complete each of six activities from 30 real subjects using one fixed native window; preserve frozen cores and previous task7 run.


Task7 subject continuation complete: official source/archive and full numeric mapping verified; 30 subjects x six single-activity analyses plus a separate subject mean, 7 groups/28 methods all successful; original frozen sources/CSVs/v1 package unchanged. Four final figures and clean package full rebuild passed. No subject/activity input blocker remains for these analyses.
