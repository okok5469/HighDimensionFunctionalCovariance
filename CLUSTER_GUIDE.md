# 高维函数型数据协方差检验：集群运行说明

更新日期：2026-10-22（北京时间）。部署目标为 `/public/home/xjh/xmx/high_dimension_functional_data_covariance`；本文依据当前仓库代码整理，本次未连接集群、安装环境或提交作业。

## 后续交付固定要求（2026-10-24起）

后续按“新增/变更文件与集群绝对目标目录 → 所在目录与可复制的Bash命令 → 日志、结果和完成标志”的顺序交付，优先提供`.sh`提交与同批次续跑入口，减少人工步骤。当前任务4实际操作以[TASK4_README.md](TASK4_README.md)为准；下文保留早期入口说明，不作为任务4默认提交方式。

- 已上传文件、原myenv、站点配置、已完成记录和冻结发布版本继续保留，仅上传本轮新增或变化的必需文件，不重复上传旧包或重新安装环境。
- ZIP含中文文件名时，用Python zipfile按包内原名解包，并在提交前核验整包SHA256、成员摘要和发布清单；unzip结束、目录存在、squeue中有作业均不能单独证明实验成功。
- 已有发布目录缺文件时，直接用集群原ZIP补齐：先检查整包、清单和全部现存文件，字节不一致即停止；只创建缺失文件，不覆盖源码、配置、结果、锁或清单，不跳过校验。
- 补齐成功后才提交，命令用`&&`衔接成功条件；任务4具体修复命令见上述说明第1.1节。
- 计算节点批处理逐批保存检查点并输出进度，明确排队、正常暂停、失败和完成；续跑保持原数据身份，不清空结果、不盲目重提、不擅自取消旧作业。
- 新脚本保持LF换行，核验Bash及目标Python3.9语法；本地测试与远端验证分开陈述，故障根因依据实际日志，未知资源限制不猜测。

## 1. 站点配置与上传范围

| 项目 | 配置与依据 |
| --- | --- |
| 项目根目录 | `/public/home/xjh/xmx/high_dimension_functional_data_covariance`，用户指定 |
| 本地工作区 | `C:\XiangMingXu\26-27秋季\HDF\high_dimension_functional_data_covariance`，不能用于 Linux 命令 |
| 系统 / Shell | 原项目记录为 Linux x86_64 / Bash，模板使用 `#!/bin/bash -l` |
| Slurm account / 分区 | 沿用原站点记录的 `xjh` / `CMO_HPC`，尚未在本项目实际提交验证 |
| 环境模块 | 原站点使用 `module load anaconda3` 后直接 `conda activate`，不添加猜测的初始化路径 |
| 本项目 Conda 环境 | 用户确认沿用原项目的 `myenv`，不新建环境、不升级或降级现有依赖 |
| SSH | 原记录出现过 `xmx@mu01`，但外网主机、端口与认证方式未知，不能据此编造上传连接命令 |

原指南的 Tensor-ABESS、v5.1/v5.2、700 项数组、冻结计划与 Gate 均不适用于本仓库。本仓库当前没有现成的集群提交脚本，第 3 节为待保存的模板。

按原目录结构上传 `common/`、`simulation/`（包括 `simulation/configs/`）、`empirical/`、`requirements.txt` 及说明文档。HAR 另需 `data/har/har_static_subject.csv` 和 `data/har/har_dynamic_long.csv`。仅运行 M1/M2 不需要 HAR 数据或联网下载数据。

不要上传本地虚拟环境（`数值模拟/.venv`、`实证分析/.conda`）、`__pycache__/`，也不要把历史 `results/` 当作新实验输入。需要测试时上传 `tests/`；全部历史回归测试另需 README 指定的 `.planning/project-cleanup/original_code.zip` 基准。Excel 或历史股票流程的额外依赖位于 `requirements-optional.txt`，股票流程另需对应 `archive/` 代码。

## 2. Python 环境

用户确认本项目集群环境与原项目一致，后续打包和代码适配以该环境为目标：

| 组件 | 原项目记录的集群版本或位置 |
| --- | --- |
| Conda 环境 | `myenv` |
| Python | CPython **3.9.25** |
| NumPy | **2.0.2** |
| SciPy | **1.13.1** |
| OpenBLAS | **0.3.27** |
| 已观察到的环境目录 | `/public/home/xjh/xmx/.conda/envs/myenv`，实际 Python 路径用 `command -v python` 核对 |

README 中 Python 3.12.8 及 `requirements.txt` 中的版本是本地验证环境记录，不是集群安装清单。**不要在 `myenv` 中执行 `pip install -r requirements.txt`，也不要为匹配本地环境新建 Python 3.12 环境或改动集群依赖。** pandas、Matplotlib、tqdm 等其他依赖的集群版本未在原指南记录，应实际读取，不套用本地版本。

以下命令逐行执行，仅激活和检查现有环境；任何一步失败应停止并保留报错：

```bash
module load anaconda3
conda activate myenv
cd /public/home/xjh/xmx/high_dimension_functional_data_covariance
command -v python
python -m pip check
python -c 'import sys,numpy,scipy,pandas,matplotlib,tqdm; print(sys.version); print("numpy",numpy.__version__,"scipy",scipy.__version__,"pandas",pandas.__version__,"matplotlib",matplotlib.__version__,"tqdm",tqdm.__version__)'
```

后续终端只需加载模块、激活环境并进入根目录。项目没有 `src/` 目录，从根目录使用 `python -m ...` 即可，不需要另一个项目的 `PYTHONPATH`。

### 后续打包与兼容性要求

- 打包前按 Python 3.9.25 检查语法、标准库及类型注解的运行时兼容性；不能仅凭 Python 3.12 下的验证认定集群可运行。
- 按 NumPy 2.0.2、SciPy 1.13.1 检查所调用的 API、数据类型和数值行为；其他依赖以实际环境清单为准。需要修改时以适配现有集群环境为目标，不自动安装、升级依赖或修改统计方法补偿差异。
- 在匹配目标版本的环境中验证模块导入及相关测试，保留实际版本与检查结果；上传后先在计算节点运行单样本和双样本 smoke，验收成功后再提交正式实验。
- 若依赖缺失、版本冲突或数值结果异常，停止并报告具体问题，再决定代码适配范围；不默认改变共享环境、不跳过校验。
- 上传包保留源码、配置和必要数据，不携带本地环境；部署说明明确区分本地验证环境与集群运行环境。尚未完成上述检查时，只能标记为待验证，不能宣称已兼容。

## 3. M1/M2 的 Slurm 脚本模板

将以下内容保存为项目根目录的 **`run_covariance.slurm`**，使用 UTF-8、Linux LF 换行，再上传。本文只修改说明文档，不自动创建此文件。多步骤放入脚本，提交命令保持一整行，不手工拼接续行反斜杠或 here-document。

```bash
#!/bin/bash -l
#SBATCH --job-name=hdf-cov
#SBATCH --account=xjh
#SBATCH --partition=CMO_HPC
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --no-requeue
#SBATCH --chdir=/public/home/xjh/xmx/high_dimension_functional_data_covariance
#SBATCH --output=/public/home/xjh/xmx/high_dimension_functional_data_covariance/logs/cov-%j.out
#SBATCH --error=/public/home/xjh/xmx/high_dimension_functional_data_covariance/logs/cov-%j.err

module load anaconda3 || exit $?
conda activate myenv || exit $?
set -euo pipefail
cd -- /public/home/xjh/xmx/high_dimension_functional_data_covariance
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 BLIS_NUM_THREADS=1
export MPLBACKEND=Agg PYTHONUNBUFFERED=1

date -Is
command -v python
python --version
python -m pip check
python -m pip freeze
python -u -m simulation.covariance_experiments "$@"
date -Is
```

**提交前先创建日志目录**，Slurm 在脚本运行前打开日志，不能依靠作业内部创建：

```bash
mkdir -p /public/home/xjh/xmx/high_dimension_functional_data_covariance/logs
```

M1/M2 驱动按场景、重复次数串行运行，申请 1 个 CPU；增加 CPU 不会自动并行。当前 CLI 没有 `--task-id` 或 Slurm 数组分发功能，不添加 `--array`，也不允许多个作业同时写同一输出目录。

模板未指定内存和时限，因为本项目没有集群实测值，站点默认值及上限也未知。提交前核对分区要求；正式运行按实际资源记录及站点规则补充 `--mem`、`--time`，省略不代表资源无限。smoke 只验证流程，其资源用量不能直接代表正式大规模场景。

## 4. 提交顺序

先用 `squeue -u "$USER"` 检查已有作业，避免重复提交。下面每条命令都是一整行；示例目录供一次独立实验使用，再次独立运行时更换目录名。

### 单样本 smoke

```bash
sbatch /public/home/xjh/xmx/high_dimension_functional_data_covariance/run_covariance.slurm --profile smoke --output /public/home/xjh/xmx/high_dimension_functional_data_covariance/results/cluster_20261022/smoke
```

### 独立双样本 smoke

```bash
sbatch /public/home/xjh/xmx/high_dimension_functional_data_covariance/run_covariance.slurm --profile two_sample_smoke --output /public/home/xjh/xmx/high_dimension_functional_data_covariance/results/cluster_20261022/two_sample_smoke
```

两种 smoke 均为 4 个场景，每场景 2 次重复、每次 39 次 bootstrap，权威配置在 `simulation/configs/`。

### 单样本正式模拟

smoke 成功并核对资源后，再提交正式任务，默认不启用 Xue：

```bash
sbatch /public/home/xjh/xmx/high_dimension_functional_data_covariance/run_covariance.slurm --profile formal --output /public/home/xjh/xmx/high_dimension_functional_data_covariance/results/cluster_20261022/formal
```

`formal.json` 包含 M1/M2 共 20 个场景，每场景 100 次重复、每次 500 次 bootstrap，共 2000 份逐次结果。当前没有预置双样本 formal 配置，不能把 `two_sample_smoke` 当作正式实验。

可加 `--model M1` 或 `--model M2` 分别运行，但必须使用独立输出目录，如 `formal_M1`、`formal_M2`；不要同时再提交包含两者的完整 formal 作业。

### 断点续跑

确认前一作业已结束，保持同一配置、模型选择、源码及环境，在同一目录显式加 `--resume`：

```bash
sbatch /public/home/xjh/xmx/high_dimension_functional_data_covariance/run_covariance.slurm --profile formal --output /public/home/xjh/xmx/high_dimension_functional_data_covariance/results/cluster_20261022/formal --resume
```

已有逐次 JSON 而不加 `--resume` 会报错。续跑校验已完成记录并跳过，缺失重复重新计算；它不是源码或完整环境的冻结校验，不要跨版本混合续跑。记录损坏或配置不匹配时停止排查，不删除记录绕过校验。

## 5. Xue、第三模型与 HAR

M1/M2 的 `--with-xue` 调用 **`Xue-1S-EV-cross-zero`**，保留配置中的 cross 零假设；不能与完整已知目标版本或原论文双样本版本混称。只用于单样本配置，输出另放独立目录：

```bash
sbatch /public/home/xjh/xmx/high_dimension_functional_data_covariance/run_covariance.slurm --profile smoke --with-xue --output /public/home/xjh/xmx/high_dimension_functional_data_covariance/results/cluster_20261022/smoke_with_xue
```

完整已知目标版本通过 `--xue-input` 接收预先上传的 NPZ（`scores+sigma0` 或 `Y+gamma0/sigma0` 等字段），具体要求见 [Xue 审计报告](docs/XUE_IMPLEMENTATION_AUDIT.md)。此模式输出 `xue_result.json`、`xue_summary.csv`，不能用 `--resume` 覆盖已有结果。

| 其他实验 | 入口 | 当前输出（相对根目录） | 并行设置 |
| --- | --- | --- | --- |
| 第三模型 | `python -u -m simulation.Main_three` | `results/simulation/model3/xue-audit-v1/` | 默认启用进程池，上限 16 |
| HAR | `python -u -m empirical.Main_HAR_empirical` | `results/empirical/har/xue-audit-v1/experiment_results/`、`figures/` | 默认启用进程池，上限 8 |

这两个入口不支持 M1/M2 的 `--profile`、`--output`、`--resume`，不能直接使用上面的 1 CPU 模板。独立脚本应分别申请与实际进程数匹配的 CPU（现配置可申请 16、8），保留单线程 BLAS、`MPLBACKEND=Agg` 和独立日志，先核对站点资源。代码用 `multiprocessing.cpu_count()` 计算进程数，不读取 `SLURM_CPUS_PER_TASK`，仅减少申请 CPU 不能保证限制进程数。

M3/HAR 使用固定输出文件名，重跑可能覆盖；已有结果时先停止并决定保存方式。HAR 使用本地 CSV，无需股票接口；历史股票流程不属于默认集群任务。

## 6. 结果与作业检查

M1/M2 在 `--output` 目录下生成：

| 文件 | 含义 |
| --- | --- |
| `<scenario_id>/replicate_000.json` 等 | 配置、bootstrap 值、判决及版本信息等逐次结果 |
| `<scenario_id>/failure_000.json` 等 | 某次运行异常的诊断记录，结合 stderr 排查 |
| `experiment*_partial.csv` | 已完成场景的阶段汇总，不能单独证明整批完成 |
| `experiment*_results.csv` | 各实验最终汇总 |
| `all_experiments_results.csv` | 当前运行的全部场景汇总 |

不指定输出时，普通 M1/M2 默认根目录为 `results/validation_v1.1_20261021/<profile>/`，加 `--model` 时追加模型目录。启用 Xue 的默认根目录为 `results/xue_audit_v1_20261021/`，加 `--with-xue` 时追加 `with_xue/`。集群提交建议始终显式指定输出目录。

查看队列：

```bash
squeue -u "$USER"
```

下面 `12345` 必须替换为 `sbatch` 返回的真实 Job ID：

```bash
sacct -j 12345 --format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS
```

```bash
tail -n 80 /public/home/xjh/xmx/high_dimension_functional_data_covariance/logs/cov-12345.out /public/home/xjh/xmx/high_dimension_functional_data_covariance/logs/cov-12345.err
```

成功需同时核对调度状态、退出码和结果：日志应有 `Completed 4 scenarios`（两种 smoke）或 `Completed 20 scenarios`（完整 formal），最终汇总行数和逐次记录数应匹配配置；限定单模型时按筛选后的场景数验收。`squeue` 为空、存在部分 CSV 或仅有 stdout 都不能证明成功，`sacct` 可用性尚未在本次集群验证。

## 7. 常见问题与待确认项

- `ModuleNotFoundError`：检查上传是否完整、是否进入项目根目录，不引用另一个项目的 `src/`。
- Python 或 Conda 不可用：检查当前终端的模块加载与环境激活记录，不猜测固定初始化路径。
- `sbatch: Unable to open file`：检查 `run_covariance.slurm` 是否已保存、上传，以及路径和文件名。
- 无日志：检查是否返回 Job ID、`logs/` 是否预先存在、account 和分区是否可用。
- `^M` 或 CRLF 错误：把提交脚本保存为 LF 换行后重新检查，不改实验代码补偿。
- `FileExistsError`：同一实验明确加 `--resume`，新实验更换独立目录，不清空旧结果。
- 运行异常或断点无效：保留日志及失败记录，定位原因后决定续跑，不自动重复提交或降低校验。

尚待实际确认：计算节点依赖兼容性、正式任务内存和时长、分区默认/最大资源、并发配额及实际完成情况。原项目成功记录不能替代本项目 smoke 和正式验收。

依据：[项目 README](README.md)、[v1.1 修订报告](docs/COVARIANCE_CODE_REVISION_REPORT.md)、[Xue 审计报告](docs/XUE_IMPLEMENTATION_AUDIT.md)、[仓库约束](AGENTS.md)。
