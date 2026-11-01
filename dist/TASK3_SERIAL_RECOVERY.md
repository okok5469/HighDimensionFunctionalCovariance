# 旧批次串行恢复：保留现有有效结果

适用于 `task3_v1_20261022` 原批次在探索 worker 并发争用 `environment.lock` 后，控制器已阻塞且集群作业已结束的情况。恢复使用原冻结版本计算，不修改原配置、源码、manifest、计划、记录中的实现哈希或 `controller_state.json`；已有有效记录由原 worker 校验后跳过，仅补缺失记录。串行调度速度比并发慢。

仅上传 **`dist/task3_serial_recovery.py`** 到：

```text
/public/home/xjh/xmx/high_dimension_functional_data_covariance/incoming/task3_v1_20261022/task3_serial_recovery.py
```

不要把脚本放进 `releases/task3_v1_20261022`，不要用锁修复新版 ZIP 覆盖这个旧 release。保持原 `cluster_config.json` 完全不变，也不要再启动原控制器。

## 1. 激活原环境并预览

```bash
module load anaconda3
conda activate myenv
cd /public/home/xjh/xmx/high_dimension_functional_data_covariance/incoming/task3_v1_20261022
python -B task3_serial_recovery.py --release /public/home/xjh/xmx/high_dimension_functional_data_covariance/releases/task3_v1_20261022 --config cluster_config.json --dry-run
```

预览仅检查原来源、配置和 worker mapping 并打印串行调度计划，不提交作业、不写恢复状态；实际运行时才会查询旧作业终态，并独占原控制器锁。任何检查失败都先停止。

## 2. 启动恢复

```bash
nohup python -B task3_serial_recovery.py --release /public/home/xjh/xmx/high_dimension_functional_data_covariance/releases/task3_v1_20261022 --config cluster_config.json > serial_recovery.log 2>&1 < /dev/null &
```

脚本会先检查旧 worker 和汇总作业均已终止，再执行：探索 worker 数组（`%1`）→ afterany 探索汇总 → 汇总成功后锁定确认计划 → 生成确认 worker mapping → 确认 worker 数组（`%1`）→ afterany 确认汇总与报告。所有计算继续由原 `run.slurm` 调用原科学代码。

调度覆盖仅为内存配置副本中的 `array_concurrency=1`；原配置文件保持不变。独立恢复状态记录实际命令、job ID、来源和配置 SHA256，不会把旧控制器状态改成 `done`。

## 3. 查看进度和结果

```bash
tail -n 80 serial_recovery.log
squeue -u "$USER"
python -m json.tool /public/home/xjh/xmx/high_dimension_functional_data_covariance/results/task3_v1/task3_v1_20261022/serial_recovery_state.json
```

完成须同时满足：独立 `serial_recovery_state.json` 的 `stage` 为 `done`；`pilot_integrity.json` 与 `confirm_integrity.json` 的 `complete` 都为 `true`。旧 `controller_state.json` 会保留原 `blocked` 状态，属于预期。

结果仍在原目录：

```text
/public/home/xjh/xmx/high_dimension_functional_data_covariance/results/task3_v1/task3_v1_20261022/
```

查看 `TASK3_RESULTS_REPORT.md`、`pilot_summary.csv`、`confirm_summary.csv`、`paired_comparisons.csv` 和 `figures/`；逐次记录、旧日志与新日志继续保留。恢复审计记录在该目录的 `serial_recovery_state.json`。

## 4. 中断后恢复

仅在日志原因已解决后使用：

```bash
nohup python -B task3_serial_recovery.py --release /public/home/xjh/xmx/high_dimension_functional_data_covariance/releases/task3_v1_20261022 --config cluster_config.json --resume >> serial_recovery.log 2>&1 < /dev/null &
```

已获 job ID 的作业会继续跟踪，不盲目重提。如果状态保留 `submission_intent`，说明 `sbatch` 回执不确定，脚本会拒绝继续；保留状态、日志及队列/记账信息，先核实真实提交情况，不自行删除 intent 或恢复状态。如果再次汇总失败，脚本立即停下，不进入确认锁定。
