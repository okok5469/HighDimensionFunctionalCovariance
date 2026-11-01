# Task4：两份新文件，一条Bash命令提交

更新：2026-10-24。复用已经上传的代码包、已解压的发布目录、`cluster_config.json`及全部已有结果，不重新上传ZIP、不改算法。本次使用一个计算节点作业串行推进原任务4流程，不再依赖登录节点常驻控制器或sacct轮询。

仅凭squeue列表和空目录，无法确定上次运行的根因；没有实际日志不能宣称已经修复。下面的状态命令会打印真实输出路径、保存记录数和日志，用于区分查错目录、阶段未推进与计算失败。

## 1. 只上传这两个新增文件

| 本地文件 | 集群目标目录 |
|---|---|
| `dist/task4_submit.sh` | `/public/home/xjh/xmx/high_dimension_functional_data_covariance/incoming/task4_fixed_methods_v1_20261023/` |
| `dist/task4_batch.py` | 同上 |

二者与已有`cluster_config.json`放在同一目录。旧ZIP、源码、结果和环境都不用重传；`.sh`保持LF换行。原发布目录仍为：

```text
/public/home/xjh/xmx/high_dimension_functional_data_covariance/releases/task4_fixed_methods_v1_20261023/
```

## 1.1 发布目录缺文件：从已有ZIP补齐后提交

若报`FileNotFoundError`且路径位于任务4发布目录，不重新上传ZIP，不删除结果，不跳过校验。原包已确认包含本次缺失的`docs/任务卡2_Xue.md`；下面用Python按ZIP内原名补齐文件。仅遇到缺文件时执行，正常提交直接用第2节。

```bash
cd /public/home/xjh/xmx/high_dimension_functional_data_covariance/incoming/task4_fixed_methods_v1_20261023
module load anaconda3
conda activate myenv
python - <<'PY' && bash task4_submit.sh
import hashlib, json, zipfile
from pathlib import Path

archive = Path('covariance_task4_fixed_methods_v1_20261023.zip')
release = Path('/public/home/xjh/xmx/high_dimension_functional_data_covariance/releases/task4_fixed_methods_v1_20261023')
sha = lambda data: hashlib.sha256(data).hexdigest()
assert sha(archive.read_bytes()) == '7f880133c397f526cb97b61c579a8657c57b85aa0a21061179b2fd00e02df52d', 'ZIP checksum mismatch'
pending = []
with zipfile.ZipFile(archive) as z:
    assert (release / 'manifest.json').read_bytes() == z.read('manifest.json'), 'Release manifest mismatch'
    for name, expected in json.loads(z.read('manifest.json'))['files'].items():
        data = z.read(name)
        assert sha(data) == expected, 'Archive mismatch: ' + name
        target = release / name
        if target.exists():
            assert sha(target.read_bytes()) == expected, 'Existing file changed: ' + name
        else:
            pending.append((target, data))
    for target, data in pending:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as f:
            f.write(data)
print('Restored missing files:', len(pending))
PY
```

全部检查通过才补齐并提交；已有字节不同则停止，不覆盖或重封摘要。本段要求原发布目录已有正确的`manifest.json`；清单本身缺失或不同应先核对部署位置。后续新发布同样采用Python按原名解包和完整清单验证，不单独依赖系统unzip。

## 2. 提交

登录集群后只执行：

```bash
cd /public/home/xjh/xmx/high_dimension_functional_data_covariance/incoming/task4_fixed_methods_v1_20261023
bash task4_submit.sh
```

脚本自动激活原myenv、读取已有配置并调用sbatch，终端会直接显示作业号、日志路径和结果路径。这里用`bash`执行提交入口，不要再加nohup，也不要对入口直接运行`sbatch`。

提交前会检查原控制器锁、未确认提交回执和本run已知的排队/运行作业。存在冲突就明确停止，不能并行启动两套流程；不会擅自取消旧作业。若因此拒绝提交，把下面状态命令的输出提供给助手定位，不要删除锁、状态或旧记录来强行继续。

## 3. 看进度或错误

在上述目录执行一条：

```bash
bash task4_submit.sh --status
```

它列出真实结果目录、原控制器和新批处理状态、smoke/pilot/fallback/confirm各阶段已保存JSON数，以及最近日志。排队期间没有新记录是正常现象；进入worker后每批完成会打印`CHUNK ... SAVED`，原始结果随即写盘，不等最后总汇总。

新日志在结果目录的`logs/batch-作业号.log`和`logs/batch-作业号.err`；阶段或环境错误保留完整报错，不再把作业仅出现在队列里视为计算成功。

## 4. 到时限后如何继续

单作业沿用现有配置的`worker_time_limit_minutes`和`worker_memory_limit_mb`，不猜测或提高站点上限，不承诺一个作业跑完整个实验。接近时间预算时记录`PAUSED`并正常退出；当该作业结束后，仍执行同一条：

```bash
bash task4_submit.sh
```

已完整保存的记录跳过，原始随机数与数据身份不变；不会重新随机生成一批。如果作业被站点强制TIMEOUT，也按相同命令检查点续跑。若状态为`FAILED`，先看错误，不把失败当成正常暂停。若单批计算无法容纳于现有预算，或内存超预算，会明确停止，需要依据日志处理资源或分块问题，不空转重投。

首次冒烟和B500基准也在计算节点运行，耗时尚未测出时不能保证它们一定在当前时限内完成；重复在基准阶段TIMEOUT应先检查日志和已获准资源，而非无限重复提交。

## 5. 在哪里收获结果

结果继续使用原目录，不另开一份空目录：

```text
/public/home/xjh/xmx/high_dimension_functional_data_covariance/results/task4_fixed_methods_v1/task4_fixed_methods_v1_20261023/
```

| 文件或目录 | 内容 |
|---|---|
| `batch_state.json` | 新入口状态，`PAUSED`可续跑、`FAILED`看报错、`DONE`已结束 |
| `logs/batch-*.log`、`logs/batch-*.err` | 当前作业的即时进度与完整错误 |
| `pilot/replicates/*.json` | 每次重复的四方法配对原始结果，计算中持续写入 |
| `fallback/replicates/`、`confirm/replicates/` | 触发后备、入选确认时的原始结果 |
| `pilot_summary.csv`、`pilot_paired_comparisons.csv` | 第一轮完整收集后生成的水平、功效与配对差 |
| `candidate_selection.csv`、`search_decision.json` | 选择或未入选原因 |
| `confirm_locked.json`、`confirm_summary.csv`、`confirm_paired_comparisons.csv` | 入选时的确认设计与完整确认结果 |
| `*_diagnostic_summary.csv`、`*_integrity.json`、`*_failures.csv` | 统计量、信号诊断、完整性与失败 |
| `TASK4_RESULTS_REPORT.md` | 探索、选择、确认的总报告 |

新入口的完成标志是`batch_state.json`中`stage: DONE`，并且实际执行的每阶段`*_integrity.json`为`complete: true`。不要要求旧`controller_state.json`变成done；它仅保留旧流程历史，不由新入口改写。无合格候选时正常结束，不会强行启动确认。

需要带回结果时，用原传输工具下载整个结果目录即可。实验范围仍为600份探索、条件性150份后备、最多2200份独立确认；旧任务3数据不拼入。本次新增入口在冻结发布目录之外，原ZIP及SHA256保持不变。
