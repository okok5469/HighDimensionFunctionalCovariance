# 高维函数型数据协方差检验实验

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
| 模型 1 | `python -m simulation.Main_one` | `results/simulation/model1/` |
| 模型 2 | `python -m simulation.Main_two` | `results/simulation/model2/` |
| 模型 3 | `python -m simulation.Main_three` | `results/simulation/model3/` |
| HAR 实证 | `python -m empirical.Main_HAR_empirical` | `results/empirical/har/` |

四个主入口也支持直接执行，例如 `python simulation/Main_one.py` 或在 IDE 中运行文件。输入和输出路径根据项目位置推导；直接执行时可以从其他工作目录启动。

各入口顶部仍保留原配置：模拟的 `TEST_MODE`、`B`、`n_repeats`、`USE_PARALLEL`、`NUM_PROCESSES`，HAR 的 `B`、`N_REPEATS`、`M`、`Q_SMOOTH` 和并行配置。模型 1 原来是 `TEST_MODE=True`，模型 2、3 是 `False`；这些默认值没有改变。测试模式只缩小参数网格，仍使用配置的 bootstrap 和重复次数。

运行会在本地写入上表目录中的固定文件名。保留重要的运行版本时，可另设入口中的 `OUTPUT_DIR`，HAR 可设置 `RESULTS_DIR` 和 `FIGURES_DIR`。本次上传不包含已有模拟、HAR 或 archive 结果。

HAR 使用 `data/har/har_static_subject.csv` 和 `har_dynamic_long.csv`；加载后进行窗口构造、Fourier 平滑、标准化和子抽样，分别输出 H0、H1 及比较结果。处理和检验逻辑保持原实现。

## 共享检验与历史代码

`common/statistic_calculator_517.py` 是 bootstrap 检验，`common/statistic_calculator_xue.py` 是当前 Xue 统计量，`common/xue_helper.py` 完成模拟的 Fourier 投影和 Xue 检验。基展开截断数保持原来的设置。

原模拟和 HAR 对 Xue 尾概率使用不同的浮点计算方式。`xue_pvalue(Tn)` 保留 HAR 的稳定 `expm1` 算法；`xue_pvalue(Tn, legacy=True)` 保留模拟的 `1 - F` 算法，模拟辅助工具显式调用后者。这样合并代码不会改变原实验的尾概率计算。

历史股票入口可用 `python -m archive.stock_empirical.empirical_main` 和 `python -m archive.stock_empirical.empirical_null_calibration` 调用。其输入缓存定位到 `data/cache/stock/`，新输出定位到 `results/empirical/stock/`。这些代码原来已归入 old，保留其下载、合成数据回退和独立 Xue 实现；本次只验证导入和路径，没有重新验证股票数据来源或实验有效性。

历史 `make_synthetic_cache.py` 会生成并写入合成缓存；`tmp_verify_empirical.py` 含删除缓存操作，保留作为原调试记录。这两个脚本仍有顶层执行语句，请按其原用途显式运行。

## 验证与恢复

```powershell
python -m unittest discover -s tests -v
python -m compileall -q common simulation empirical archive/stock_empirical tests
```

回归验证需要保留 `.planning/project-cleanup/original_code.zip`：测试直接对照迁移前的代码，检查生成器、两种检验、真实 HAR 数据读取、小规模模拟输出以及 Windows spawn 多进程。

本次未执行完整规模模拟和实证，也没有用验证输出覆盖原结果。回归测试基准 ZIP 包含原始 24 个 Python 文件；本地迁移清单和重复模块源文件未随仓库上传。
