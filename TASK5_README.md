# Task5：统一模型，一次启动

新批次 `task5_unified_v1_20261024`，复用原myenv、站点与Slurm；不改旧task3/task4目录。开发机只完成代码和小规模验证，正式模拟与8份B500资源基准均由用户启动后的计算节点执行。

## 上传范围

只上传以下本轮新文件到：

```text
/public/home/xjh/xmx/high_dimension_functional_data_covariance/incoming/task5_unified_v1_20261024/
```

| 本地文件 | 作用 |
|---|---|
| `dist/covariance_task5_unified_v1_20261024.zip` | 新版本完整源码、配置、说明及验证 |
| 同名 `.zip.sha256` | 整包校验 |
| `dist/task5_submit.sh` | 默认Bash入口，保持LF换行 |
| `cluster_config_task5.json` | 集中配置，复用原实际资源值 |

旧包和旧结果不用重传。新发布位置为 `.../releases/task5_unified_v1_20261024/`。入口用Python zipfile按包内原名验证整体SHA256、全部成员及manifest；相同字节复用，缺文件补齐，已有字节不同立即停止，不覆盖历史版本或绕过摘要。

## 集中配置

本地 `cluster_config_task5.json` 与example已填已知根路径、account=xjh、partition=CMO_HPC、anaconda3/myenv及独立run_name。六项资源预算仍为null：bootstrap/control/worker的内存MB及时间分钟；SSH主机、端口、用户名、认证仅PowerShell传输需要，未编造。

若旧task4 incoming中的 `cluster_config.json` 正是上次实际运行配置，可在集群incoming/task5目录用下面命令只补新配置中的空值，并把package_file指向本目录新包；不会改旧配置。先上传上述四文件，再执行一次：

```bash
cd /public/home/xjh/xmx/high_dimension_functional_data_covariance/incoming/task5_unified_v1_20261024
python - <<'PY'
import json
from pathlib import Path
p = Path('cluster_config_task5.json')
new = json.loads(p.read_text(encoding='utf-8-sig'))
old = json.loads(Path('../task4_fixed_methods_v1_20261023/cluster_config.json').read_text(encoding='utf-8-sig'))
keys = ('bootstrap_memory_mb', 'bootstrap_time_minutes', 'control_memory_mb',
        'control_time_minutes', 'worker_memory_limit_mb', 'worker_time_limit_minutes')
for key in keys:
    if new.get(key) is None:
        new[key] = old.get(key)
missing = [key for key in keys if type(new.get(key)) is not int or new[key] <= 0]
assert not missing, 'Fill actual approved resource budgets: ' + ', '.join(missing)
new['package_file'] = 'covariance_task5_unified_v1_20261024.zip'
p.write_text(json.dumps(new, indent=2) + '\n', encoding='utf-8')
PY
```

若旧路径或字段不符，应填实际值，不猜测或调高站点上限。旧配置经校验后仅在首次启动前补全；run建立后配置身份不可改，遇资源缺口应保留状态并依据日志处理，不能擅自修改配置继续混跑。

## 启动、查看、恢复、下载

在上述incoming目录中执行：

```bash
bash task5_submit.sh start --dry-run
bash task5_submit.sh start
```

入口自动完成计算节点smoke与四形状各两份B500基准，按实际形状耗时/峰值内存校验资源，再提交有限worker数组与afterany收集，全部9300份探索完成后锁定三anchor及可选扩展确认，最后汇总。不存在登录节点常驻nohup控制器，也不需要逐模型或逐阶段人工提交。基准与内存/时间预算不满足时停止，不降B、不缩规模。

查看及技术故障处理后的同身份恢复：

```bash
bash task5_submit.sh status
bash task5_submit.sh resume
```

resume检查旧提交回执、来源和作业归属；有活动作业或未确认回执时停止，不删除锁或盲目重提，DONE不会重新计算。技术失败保留原记录，显式resume只按同数据身份重试；bootstrap超时保留已完成的逐份基准。某方法保守、膨胀、未决或功效低不是技术失败，不取消已锁定单元。

集群打包下载结果（仍在上述目录）：

```bash
bash task5_submit.sh download
```

该命令把结果打成配置download_dir中的归档；使用原传输工具取回。需要本地自动上传/下载时使用可选PowerShell入口：

```powershell
powershell -NoProfile -File .\dist\submit_task5.ps1 -Config .\cluster_config_task5.json -DryRun
powershell -NoProfile -File .\dist\submit_task5.ps1 -Config .\cluster_config_task5.json
powershell -NoProfile -File .\dist\submit_task5.ps1 -Config .\cluster_config_task5.json -Action status
powershell -NoProfile -File .\dist\submit_task5.ps1 -Config .\cluster_config_task5.json -Action resume
powershell -NoProfile -File .\dist\submit_task5.ps1 -Config .\cluster_config_task5.json -Action download
```

PowerShell在仓库根目录执行，另需填SSH真实字段；dry-run不联网。默认Bash路径无需SSH字段。旧作业仍只读核实，不按历史作业号取消。

## 结果、日志和完成标志

```text
/public/home/xjh/xmx/high_dimension_functional_data_covariance/results/task5_unified_v1/task5_unified_v1_20261024/
```

| 路径 | 内容 |
|---|---|
| `controller_state.json`、`logs/*.out`、`logs/*.err` | 阶段、作业回执、实际运行和错误 |
| `benchmark/production_n*_p*_r*.json`、`production.json` | 8份独立基准及完整集合；时间/内存据此估算 |
| `pilot_resource_estimate.json`、`confirm_resource_estimate.json` | 按形状资源需求、worker小时及假设 |
| `scenario_catalog.csv`、`normalization_and_projection_diagnostics/` | 完整设计、规范化与实际投影 |
| `pilot/replicates/`、`confirm/replicates/` | 逐次四方法原始结果和bootstrap最大值 |
| `pilot_level_summary.csv`、`pilot_power_summary.csv` | 全部探索水平、功效与区间 |
| `extension_selection.csv`、`confirm_locked.json` | 固定扩展规则的全部选择依据和不可变确认锁 |
| `confirm_level_summary.csv`、`confirm_power_summary.csv` | 独立确认结果，单方法校准标签 |
| `paired_comparisons.csv`、`runtime_summary.csv` | 按阶段分别报告的配对差和耗时 |
| `integrity_and_failures/`、`*_diagnostic_summary.csv` | 缺失/失败及T、临界值、p值分布 |
| `figures/`、`TASK5_RESULTS_REPORT.md` | 分阶段趋势图与总报告 |

完成需同时具备：`DONE.json`、controller阶段DONE、pilot和confirm的完整性文件均为complete=true。队列中有作业、目录已创建或某个worker成功均不能单独证明完成。

正式统计总预算15000份，符合固定扩展条件时18800份，另加8份基准和5份小形状低B冒烟；不把旧任务或探索H0加入确认。M1 s5有截断遗漏、Brownian s21未覆盖潜在全秩；输出说明这些适用范围，水平与功效结论必须等待新数据。
