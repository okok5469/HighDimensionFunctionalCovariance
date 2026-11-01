# 高维函数型数据协方差检验实验

当前本文检验采用 **v1.1（2026-10-21）**，单样本为主，独立双样本为推广。修订依据、数值验证及兼容性说明见 [任务卡1修订报告](docs/COVARIANCE_CODE_REVISION_REPORT.md)。M1/M2 的权威配置位于 `simulation/configs/`，默认运行 smoke；正式20场景须显式选择 `--profile formal`。

```powershell
python -m simulation.covariance_experiments --profile smoke
python -m simulation.covariance_experiments --profile two_sample_smoke
# 正式实验命令，仅准备，本轮未启动；结果目录与 smoke 分离。
python -m simulation.covariance_experiments --profile formal --output results/simulation_v1.1_20261021/formal
# 继续同一配置与结果目录，已完成的逐次 JSON 不重算。
python -m simulation.covariance_experiments --profile formal --output results/simulation_v1.1_20261021/formal --resume
```

`--model M1` 或 `--model M2` 可限定模型；`--with-xue` 在既定cross场景调用明确标注的 `Xue-1S-EV-cross-zero`，新输出位于 `results/xue_audit_v1_20261021/`，完整已知目标主版通过 `--xue-input` 调用，见 [Xue审计报告](docs/XUE_IMPLEMENTATION_AUDIT.md)。结果含配置、真值支持、随机流规则、bootstrap值与逐次判决；已有结果不会作为当前版本断点读取。临界值为正无穷时，JSON 用 `null` 表示。已有逐次文件时须明确使用 `--resume` 或另选目录。

项目包含三个数值模拟模型、HAR 人体活动实证，以及保留供追溯的历史股票实证。模拟与 HAR 共用 `common/` 中的检验代码。

GitHub 仓库发布代码、文档、测试、HAR 原始 CSV 和回归测试所需的原始代码基准。实验结果、股票数据缓存及本地 Python 环境不纳入版本控制；下方目录树展示的是本地工作区布局。

## 目录

```text
common/                 共享统计量、bootstrap、Xue 基投影、项目路径
simulation/             三个模拟入口及数据生成器
empirical/              HAR 实证入口及数据加载器
data/
  har/                  原始 HAR CSV
  cache/stock/          历史股票缓存
results/
  simulation/model1/    模型 1 输出；模型 2、3 运行后生成各自目录
  empirical/har/        HAR 的 experiment_results/ 和 figures/
  history/              原标记可用的模拟版本及加入 Xue 的历史结果
archive/
  stock_empirical/      历史股票实证代码
  results/              原标记废弃的结果及其绘图脚本
  logs/                 历史和调试日志
tests/                  生成器及迁移回归验证
docs/                   设计、文件迁移及重复核对报告
.planning/project-cleanup/  本地迁移材料；仅原代码 ZIP 随测试上传
数值模拟/、实证分析/       本地虚拟环境目录（环境文件不上传）
```

本地历史结果保留原版本标签和文件名；没有把不同版本的结果混成一张表。结果文件不随此次上传，详细位置见 [整理报告](docs/project-cleanup-report.md)。

## 环境

本次用 Python 3.12.8 验证。已有环境可继续使用；`requirements.txt` 记录本次验证环境的核心库版本。新环境可运行：

```powershell
python -m pip install -r requirements.txt
```

HAR 的默认输入为 CSV，不需要网络或股票接口。Excel 输入和历史股票代码的额外依赖见 `requirements-optional.txt`。

原 `数值模拟/.venv` 和 `实证分析/.conda` 留在原位置，避免环境内的绝对路径失效；本次没有修改或重新安装这些环境。

## 运行实验

在本 README 所在的项目根目录运行：

| 实验 | 命令 | 输出目录 |
| --- | --- | --- |
| 模型 1 | `python -m simulation.Main_one` | `results/validation_v1.1_20261021/smoke/M1/` |
| 模型 2 | `python -m simulation.Main_two` | `results/validation_v1.1_20261021/smoke/M2/` |
| 模型 3 | `python -m simulation.Main_three` | `results/simulation/model3/` |
| HAR 实证 | `python -m empirical.Main_HAR_empirical` | `results/empirical/har/` |

四个主入口也支持直接执行，例如 `python simulation/Main_one.py` 或在 IDE 中运行文件。输入和输出路径根据项目位置推导；直接执行时可以从其他工作目录启动。

M1/M2 两个入口转接同一版本化驱动，支持上述 CLI 参数，配置的 bootstrap 与重复次数分别为 smoke 的39/2及正式的500/100；任务卡1驱动串行逐次保存。第三模型和 HAR 保留各自现有配置与并行设置。

运行会在本地写入上表目录中的固定文件名。保留重要的运行版本时，可另设入口中的 `OUTPUT_DIR`，HAR 可设置 `RESULTS_DIR` 和 `FIGURES_DIR`。本次上传不包含已有模拟、HAR 或 archive 结果。

HAR 使用 `data/har/har_static_subject.csv` 和 `har_dynamic_long.csv`；加载后进行窗口构造、Fourier 平滑、标准化和子抽样。其预处理与调用接口保留，调用的共享 bootstrap 核心已更新为v1.1，旧实证结果仍为历史记录。

## 共享检验与历史代码

`common/statistic_calculator_517.py` 是 bootstrap 检验，`common/statistic_calculator_xue.py` 是当前 Xue 统计量，`common/xue_helper.py` 完成模拟的 Fourier 投影和 Xue 检验。基展开截断数保持原来的设置。

Xue新生产调用采用稳定EV尾概率和严格乘积方差检查，退化失败不会当作不拒绝。`run_xue_test`三元组兼容包装和显式`legacy=True`保留旧尾概率算术用于追溯；新生产使用结构化结果。旧cross版本、完整Xue-1S-EV与原论文两样本版本不能混名。

历史股票入口可用 `python -m archive.stock_empirical.empirical_main` 和 `python -m archive.stock_empirical.empirical_null_calibration` 调用。其输入缓存定位到 `data/cache/stock/`，新输出定位到 `results/empirical/stock/`。这些代码原来已归入 old，保留其下载、合成数据回退和独立 Xue 实现；本次只验证导入和路径，没有重新验证股票数据来源或实验有效性。

历史 `make_synthetic_cache.py` 会生成并写入合成缓存；`tmp_verify_empirical.py` 含删除缓存操作，保留作为原调试记录。这两个脚本仍有顶层执行语句，请按其原用途显式运行。

## 验证与恢复

```powershell
python -m unittest discover -s tests -v
python -m compileall -q common simulation empirical archive/stock_empirical tests
```

历史回归验证需要保留 `.planning/project-cleanup/original_code.zip`，用于确认未改的Xue、第三模型、HAR预处理及样本协方差定义。任务卡1的新测试以独立外积、固定创新与规范配置核验新数值，不要求M1/M2或bootstrap与旧版本逐位一致。

本次未执行完整规模模拟和实证，也没有用验证输出覆盖原结果。回归测试基准 ZIP 包含原始 24 个 Python 文件；本地迁移清单和重复模块源文件未随仓库上传。


## Xue完整已知目标入口

```powershell
# NPZ含scores+sigma0（flat还需p,s），或Y+完整gamma0，不由当前样本估目标。
python -m simulation.covariance_experiments --xue-input your_known_target.npz --output results/xue_audit_v1_20261021/known_target_run
# 保持原场景、原假设的cross比较；已有审计结果时使用resume。
python -m simulation.covariance_experiments --profile smoke --with-xue --resume
```

完整曲线目标按实际固定映射L投影为L gamma0 L转置，含噪声时目标也应含噪声；已有系数目标sigma0不重复投影。Y+gamma0入口同时将相同观察和目标交给我们的完整协方差核心；仅scores输入不宣称具有时间域比较数据。详细字段、40项验证、同输入对照及重跑清单见 [Xue审计报告](docs/XUE_IMPLEMENTATION_AUDIT.md)。HAR与第三模型新结果隔离在各自的 `xue-audit-v1` 子目录；本轮未完整重跑模拟或实证。
