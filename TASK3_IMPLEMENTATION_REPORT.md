# task3_v1：实现与交付报告

日期：2026-10-22（北京时间）。依据任务卡3新增task3命名空间；保留任务卡1/2、原M1/M2与20个cross配置及历史结果。未创建分支/worktree或Git提交，未连接集群、安装或修改myenv，未运行本地大规模探索/确认。

## 实际改动

- `simulation/task3_generators.py`：四家族八规格、两full参考、含噪声完整目标、matching精确生成及真值/实际投影诊断。
- `task3_experiments.py`、`task3_io.py`、`task3_summary.py`：共同输入四方法、独立随机流、封印计划、原子写入与原生锁、worker分块、失败/缺失/重复/混版检测、固定选择及独立确认、配对统计、图表与报告。
- `simulation/configs/task3/`：小型冒烟、25场景1250份探索、固定确认规则与维度扩展边界，不改原cross配置。
- `cluster/task3/`：现有myenv校验、登录节点轻量控制、计算节点全部重计算、8并发数组、afterany收集成功门控、状态/恢复/下载。
- `tools/build_task3_package.py`与dist入口：当前真实源码字节与Git脏状态、3.9语法检查、ZIP内manifest/SHA256SUMS和外部校验，4文件独立PowerShell上传启动。

本文调用唯一v1.1核心，保持原始乘子与bootstrap p值约定；Xue主对照冻结为`Xue-1S-EV-full / xue-audit-v1 / fixed-Fourier-s5`，s11/s21分别输出，不组合最小p值、不新增FPCA或改阈值。大型确定性对象按场景单独保存并关联哈希，逐次保留bootstrap最大值和必要字段。

## 统计解释

全部探索有利/不利/失败均保留；宽松筛查为配套零假设任一方法拒绝率不超过.12。按两个强度的本文功效减三个固定Xue最大功效之平均差排序，最多2候选优先不同机制，固定保留快谱和M2；分数非正也不换种子追优。

确认零500、各备择300，校准工作性筛查为单侧95%上限不超过.08，不把alpha改为.08；显式报告保守性。拒绝率用二项区间；配对差保存四格计数、配对MCSE与可处理零不一致次数的保守Clopper–Pearson组合区间。正式标签对冻结全部配对声明作Bonferroni控制，epsilon=.05；失败/未完成/校准不通过时不输出有效功效优势。尚无正式科学结果，不宣称已发现优势。

## 验收与限制

测试覆盖代数真值/正定性/峰值/实际投影、共享输入/随机数、独立阶段/恢复、封印/完整性、固定选择/不确定性、Slurm收集失败不锁定及恢复、4文件独立PowerShell参数解析/dry-run、打包范围/哈希。集群部分9项离线测试已通过，真实PowerShell dry-run无网络/提交；Windows脚本执行策略仅在测试子进程设置Bypass，无持久策略变更。Slurm脚本LF，按原环境先module/conda成功再启用nounset。

实际本地验收：完整回归70项先前通过，随后新增的3个针对用例及相关复验通过，当前共73项；集群部分9项离线测试通过。真实smoke完成25个场景、每场景2次、共50份共同输入数据，0失败（n24、p6，新增模型保持M64/q20，B39）；不要求备择冒烟必拒绝。本地小型benchmark入口亦成功：n24/p6/M64/B3，总耗时0.0504404秒，进程峰值41.6836 MiB；环境Python3.12.8、NumPy1.26.4、SciPy1.16.1，这些数字只用于入口验证，不外推生产资源。

最终ZIP干净解压、全部校验和、同入口smoke及包外4文件独立dry-run的实际记录将另存`dist/task3_validation_20261022.json`。该外部验收记录在最终打包后生成，避免为记录验收而回写已封印源码或替换ZIP；它不能替代目标myenv计算节点验收。
本机Python3.12.8测试与3.9语法检查不代表目标Python3.9.25/NumPy2.0.2/SciPy1.13.1实际运行通过。计算节点版本校验、smoke和B500正式资源测量为流水线前置阶段，失败即停；pandas/Matplotlib/tqdm需现有环境可导入，不自动安装。

## 交付与追溯

### 后续集群并发锁修复

真实集群日志发现：环境信息登记共用的 `environment.lock` 原先使用非阻塞锁，多个合法 worker 同时进入时会触发 `BlockingIOError`，导致整块任务在计算开始前退出。NumPy 提示安装 `pyyaml` 只是配置显示警告，与该失败无关。

修复仅让环境登记等待共享锁；同一逐次记录的写锁仍立即拒绝重复写入。新增真实8进程竞争回归先复现失败，修复后8份小记录全部完成；统计核心、生成器、方法参数和随机数据键未变。

锁修复与独立恢复入口完成后，全量81项回归通过，日志为 `results/task3_validation_20261022/lockfix_unittest_final.log`；包括8真实进程环境锁竞争与7项离线恢复调度测试，未连接集群或替用户提交任务。

修复版另存 `dist/covariance_task3_v1_lockfix_20261022.zip`，不覆盖原 ZIP。不能把新源码覆盖到已经冻结来源哈希的旧批次后直接续跑；旧批次可使用包外独立串行恢复入口，调用旧 release 的原计算与调度接口，保留原配置、封印和有效记录，并保存独立调度审计。详情见 `dist/TASK3_SERIAL_RECOVERY.md`。

目标包为`dist/covariance_task3_v1_20261022.zip`、同名`.zip.sha256`、`dist/submit_task3.ps1`和`dist/cluster_config.example.json`。源码稳定后按真实字节打包；manifest记录各文件SHA-256、实现哈希、目标环境与Git HEAD/未提交状态；SHA256SUMS覆盖包内文件，外部校验覆盖ZIP整体。打包器拒绝覆盖同名已有包。

最终ZIP须在干净临时目录校验包内哈希并运行`python -m simulation.task3_experiments smoke --output <独立目录>`，另独立实测包外4文件PowerShell dry-run；最终验收记录以本次实际测试与解压smoke输出为准。包不携带密钥/凭据/个人SSH配置、完整旧结果、环境/缓存或无关项目；只携当前任务必要测试，不携旧完整回归依赖的`.planning`历史档案ZIP。

未解决的真实信息仅集中配置SSH与站点预算、account/partition当前可用性及登录节点轻量控制政策；不阻止本地代码和ZIP交付。正式资源数值、1250份探索与最多6000份确认待用户启动集群后产生；后续源码修复必须新版本新批次，不能混接原确认重复。
