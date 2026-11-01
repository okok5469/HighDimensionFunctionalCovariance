# task3_v1：集群操作

1. **配置**：将ZIP、`.zip.sha256`、`submit_task3.ps1`、`cluster_config.example.json`放在同一目录，复制后者为`cluster_config.json`；填写SSH与站点资源预算。`package_file`指向同目录ZIP。先运行`powershell -NoProfile -File .\submit_task3.ps1 -Config .\cluster_config.json -DryRun`检查参数，不联网、不提交。
2. **启动**：`powershell -NoProfile -File .\submit_task3.ps1 -Config .\cluster_config.json`。一次上传、校验、解压并启动登录节点控制器，自动执行计算节点冒烟、正式资源基准、探索、锁定、独立确认及汇总。
3. **恢复**：查明日志/失败原因后，保持同一ZIP和原配置，运行`powershell -NoProfile -File .\submit_task3.ps1 -Config .\cluster_config.json -Action resume`；未结束的作业继续等待，已验证成功重复跳过，同一失败重复保留原数据键重试。
4. **下载**：`powershell -NoProfile -File .\submit_task3.ps1 -Config .\cluster_config.json -Action download`。下载到配置`download_dir`；查看状态用同一命令加`-Action status`。

## 配置与环境

启动电脑需Python 3.9或更高版本、Windows PowerShell及OpenSSH的`ssh/scp`。脚本在完整仓库内直接调用上传器，单独交付时从通过外部SHA-256校验的ZIP读取上传器，无需拼接源码。SSH使用已受信任的主机密钥及`BatchMode=yes`；首次连接信任应按站点流程预先完成。认证只支持已配置的SSH agent或本地私钥路径，私钥不上传，配置不存密码。

未确定的信息集中在`cluster_config.example.json`：`ssh.host/port/user/authentication`，选择`identity_file`认证时另填`ssh.identity_file`；`bootstrap_memory_mb/bootstrap_time_minutes`、`control_memory_mb/control_time_minutes`与`worker_memory_limit_mb/worker_time_limit_minutes`须按站点资源上限填写。worker预算是上限，测量申请超限立即停止，不自动扩预算。默认`array_concurrency=8`，允许1至8；`seconds_per_chunk=1800`。`account=xjh`、`partition=CMO_HPC`沿用原指南，仍需确认当前可用；不猜外网地址、端口或资源限制。

部署根目录`/public/home/xjh/xmx/high_dimension_functional_data_covariance`，每个ZIP按外部哈希解压到`releases/<ZIP_SHA256>/`，已有源码与历史结果不覆盖；结果位于`results/task3_v1/<run_name>/`。中转与控制器日志位于`.task3_upload/<ZIP_SHA256>/`。新科学批次必须换`run_name`，恢复保持原值。

集群固定使用`module load anaconda3`、`conda activate myenv`，要求Python **3.9.25**、NumPy **2.0.2**、SciPy **1.13.1**，计算节点入口逐项校验；pandas、Matplotlib、tqdm须已安装且可导入。**不执行`pip install -r requirements.txt`，不修改myenv**。`requirements.txt`是历史本地环境清单，`manifest.json`另记目标环境。Python3.9语法检查不替代目标环境运行验收，版本或依赖不符即停止。

若Windows执行策略禁止脚本，按本机管理规则审阅并允许运行；离线测试仅对子进程使用`powershell -NoProfile -ExecutionPolicy Bypass -File ... -DryRun`，没有修改用户/机器持久策略。是否允许该命令由本机规则决定。

## 阶段与失败处理

登录节点控制器只使用Python标准库、`sbatch/squeue/sacct`、小型状态JSON及等待循环。所有数值计算、场景诊断和科学汇总均通过单CPU Slurm作业执行，不要求计算节点调用`sbatch`。控制器用`nohup`保持运行；需站点允许登录节点轻量控制进程并提供Slurm accounting，政策不允许时停止，不绕过调度规则。

顺序为`smoke → init → benchmark(B=500) → plan-workers(pilot) → pilot数组 → afterany collect → lock → plan-workers(confirm) → confirm数组 → afterany collect/report`。探索全部完成且校验成功才生成不可变确认清单；worker失败后收集仍运行，保留失败清单，禁止半成品进入确认。依据：[Slurm数组规范](https://slurm.schedmd.com/job_array.html)、[sbatch依赖与退出语义](https://slurm.schedmd.com/sbatch.html)。

单BLAS线程，逐次原子写入，原生文件锁保护相同重复及控制器。源码/配置/封印哈希、数据ID或方法身份不符立即停止。源码修复不得混接原确认批次，应更换版本包并启动独立批次。若在`sbatch`提交后Job ID落盘前中断，状态保留`submission_intent`并拒绝自动续提；先核对`squeue/sacct`与日志、查明Job ID后再整理状态，不能盲目重复提交。

查看`controller_state.json`、`.controller.log`、结果目录`logs/`和`pilot_failures.csv/confirm_failures.csv`；`status`展示最后持久状态。完整性以逐次记录、封印与`*_integrity.json`为准，队列为空不代表成功；Slurm日志目录在提交前创建。

## 本地入口与产物

解压后从项目根目录运行`python -m simulation.task3_experiments smoke --output <独立临时目录>`。小型基准为`benchmark --small`，不作为生产资源依据；完整基准由集群自动运行。默认含有限维度扩展，若预先关闭，在首次启动前设`skip_dimension_extension=true`，之后不按结果改配置。

产物包括场景/诊断、逐次JSON、探索与确认汇总、配对区间、锁定清单、失败/耗时、图和结果报告。原M1/M2的20个cross场景通过`python -m simulation.task3_experiments legacy --output <独立目录>`独立调用，默认流程不重复启动，也不混入新full表。

机制见[TASK3_DGP_SPEC.md](TASK3_DGP_SPEC.md)，规模见[TASK3_RESOURCE_PLAN.md](TASK3_RESOURCE_PLAN.md)，实现与验收见[TASK3_IMPLEMENTATION_REPORT.md](TASK3_IMPLEMENTATION_REPORT.md)。
