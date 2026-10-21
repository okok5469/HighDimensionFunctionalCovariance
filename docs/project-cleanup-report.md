# 项目整理报告

日期：2026-10-06。目录及调用路径已整理，实验计算和原配置保留。

## 主要迁移

| 原位置 | 新位置 |
| --- | --- |
| 数值模拟/Main_*.py、data_generator_*.py | simulation/ |
| 三份 bootstrap 模块、两份 Xue 统计量及辅助工具 | common/ 中各一个当前实现 |
| 实证分析/Main_HAR_empirical.py、har_data_loader.py | empirical/ |
| 实证分析/har_*.csv | data/har/ |
| 实证分析/cache/ | data/cache/stock/ |
| 数值模拟/experiment_results_model1/ | results/simulation/model1/ |
| 实证分析/experiment_results/、figures/ | results/empirical/har/ 下同名子目录 |
| result/simulation_results_可用/ | results/history/simulation/ |
| result/加入Xue数值模拟/ | results/history/with_xue/ |
| result/暂时废弃/ | archive/results/legacy/ |
| 实证分析/人体结果1（废）/ | archive/results/har_first_version/ |
| 实证分析/old/ | archive/stock_empirical/，main.log 单独归档 |
| 调试输出及历史日志 | archive/logs/ |
| 原 test_data_generator_two.py | tests/ |

逐文件映射在 `.planning/project-cleanup/migration_manifest.json`，147 个原项目文件均有记录。

## 重复代码的处理

- bootstrap 三份的检验计算相同，差别在演示导入；合并到 common，演示导入指向现有模型 1 生成器。
- xue_helper 两份字节完全相同，合并到 common。
- Xue 统计量两份主要区别为注释编码和 p 值尾概率计算；采用中文可读注释，保留两种尾概率算法。HAR 使用稳定计算，模拟显式使用 legacy=True。
- 历史股票 xue_test 与当前方法实现不同，保留在 archive/stock_empirical，不合并。
- 24 个原 Python 文件完整保存在 original_code.zip；4 个不再参与调用的重复文件另保存在 duplicate_sources。

## 完全相同的数据和结果

下面按迁移前 SHA256 找到的重复组列出。相同结果可能用于不同版本的追溯，因此保留每个原文件，没有据此删除数据或输出。

**重复组 1**

- `results/simulation/model1/experiment1_partial.csv`
- `results/simulation/model1/experiment1_results.csv`

**重复组 2**

- `results/simulation/model1/experiment2_partial.csv`
- `results/simulation/model1/experiment2_results.csv`

**重复组 3**

- `results/simulation/model1/experiment3_partial.csv`
- `results/simulation/model1/experiment3_results.csv`

**重复组 4**

- `results/empirical/har/experiment_results/Tn_boot_list.npy`
- `archive/results/har_first_version/experiment_results/Tn_boot_list.npy`

**重复组 5**

- `results/empirical/har/experiment_results/Y_pool.npy`
- `archive/results/har_first_version/experiment_results/Y_pool.npy`

**重复组 6**

- `results/history/simulation/experiment_results_0527可用/experiment1_partial.csv`
- `results/history/simulation/experiment_results_0527可用/experiment1_results.csv`

**重复组 7**

- `results/history/simulation/experiment_results_0527可用/experiment2_partial.csv`
- `results/history/simulation/experiment_results_0527可用/experiment2_results.csv`

**重复组 8**

- `results/history/simulation/experiment_results_0527可用/experiment3_partial.csv`
- `results/history/simulation/experiment_results_0527可用/experiment3_results.csv`

**重复组 9**

- `results/history/simulation/experiment_results_model1_0527可用/experiment1_partial.csv`
- `results/history/simulation/experiment_results_model1_0527可用/experiment1_results.csv`

**重复组 10**

- `results/history/simulation/experiment_results_model1_0527可用/experiment2_partial.csv`
- `results/history/simulation/experiment_results_model1_0527可用/experiment2_results.csv`

**重复组 11**

- `results/history/simulation/experiment_results_model1_0527可用/experiment3_partial.csv`
- `results/history/simulation/experiment_results_model1_0527可用/experiment3_results.csv`

**重复组 12**

- `results/history/simulation/experiment_results_model3_0601可用/experiment1_partial.csv`
- `results/history/simulation/experiment_results_model3_0601可用/experiment1_results.csv`

**重复组 13**

- `results/history/simulation/experiment_results_model3_0601可用/experiment2_partial.csv`
- `results/history/simulation/experiment_results_model3_0601可用/experiment2_results.csv`

**重复组 14**

- `results/history/simulation/experiment_results_model3_0601可用/experiment3_partial.csv`
- `results/history/simulation/experiment_results_model3_0601可用/experiment3_results.csv`

**重复组 15**

- `archive/results/legacy/model1results/all_experiments_results.csv`
- `archive/results/legacy/Plots/all_experiments_results.csv`

**重复组 16**

- `archive/results/legacy/model1results/experiment1_partial.csv`
- `archive/results/legacy/model1results/experiment1_results.csv`

**重复组 17**

- `archive/results/legacy/model1results/experiment2_partial.csv`
- `archive/results/legacy/model1results/experiment2_results.csv`

**重复组 18**

- `archive/results/legacy/model1results/experiment3_partial.csv`
- `archive/results/legacy/model1results/experiment3_results.csv`

**重复组 19**

- `archive/results/legacy/model2results/experiment1_partial.csv`
- `archive/results/legacy/model2results/experiment1_results.csv`

**重复组 20**

- `archive/results/legacy/model2results/experiment2_partial.csv`
- `archive/results/legacy/model2results/experiment2_results.csv`

**重复组 21**

- `archive/results/legacy/model2results/experiment3_partial.csv`
- `archive/results/legacy/model2results/experiment3_results.csv`

**重复组 22**

- `archive/results/legacy/model2results/model2_results.csv`
- `archive/results/legacy/Plots/model2_results.csv`

## 文件与计算核验

- 原项目文件 147 个；129 个迁移后 SHA256 完全相同。
- 全部 123 个原非代码文件（输入、缓存、CSV、NPY、图片、TeX、日志）保持字节一致。
- 18 个代码文件因导入、路径或去重兼容调整发生变化，其原版本 ZIP 哈希均一致。
- 核验 13 个实验任务、统计计算及子抽样核心函数，AST 与原实现完全一致。
- 三个模型生成器的 H0/H1 输出与原代码在固定种子下完全一致；bootstrap 和 Xue 数值与原版本一致，包括尾概率极端值。
- 8 项 unittest 通过，包含原生成器测试、Windows spawn、小规模三模型三类实验完整输出和 HAR 真实数据加载及子抽样。
- 当前和历史股票模块完成语法及导入检查；四个当前主入口完成异地直接文件加载检查。
- 未重跑完整规模实验；所有验证生成的结果写入临时目录，原有结果没有覆盖。

## 保留的环境及历史行为

原 .venv、.conda、隐藏配置和旧 __pycache__ 留在原中文目录；这些属于运行环境，不纳入实验重复文件判定。

历史股票代码只调整调用和路径，保留原下载、缓存与合成回退行为，未验证其研究结论。历史缓存生成和临时调试脚本仍保持原顶层执行语句。

本项目目录没有有效 Git 仓库；恢复和追溯使用代码 ZIP、原哈希、迁移清单和 verification.json。
