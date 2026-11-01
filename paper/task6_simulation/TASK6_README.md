# 任务6：模拟章节和论文图表

先阅读 `SIMULATION_SECTION_ZH.md`，或打开已编译的 `preview.pdf`；逐图检查使用离线 `FIGURE_GALLERY.html`。完整探索和配对表在 `SIMULATION_SUPPLEMENT_ZH.md` 与 `tables/`，来源边界和核验结果见 `TASK6_VALIDATION_REPORT.md`。

在项目根目录运行：

```bash
python paper/task6_simulation/scripts/build_task6_paper.py --config paper/task6_simulation/task6_paper_config.json
```

解压交付ZIP后，在解压目录运行同一相对入口：

```bash
python scripts/build_task6_paper.py --config task6_paper_config.json
```

两条命令均读取随包小型汇总与锁定快照，校验哈希、整数计数、区间、标签，生成主表、完整补表、四张主图及十张补图的PDF/SVG/PNG、离线图册、发布清单、ZIP和SHA256。正文MD和TeX保存为作者可编辑稿，重建不覆盖人工改写；章节数字后续若改动输入须由作者对照派生表更新。

运行环境为Python 3.12，NumPy/Pandas/SciPy/Matplotlib；PDF自动审计另需PyMuPDF，依赖见 `requirements-paper.txt`，可使用 `python -m pip install -r requirements-paper.txt` 安装。当前机器的PDF审计依赖独立位于 `.qa_deps/`，不更改全局科学环境，也不包含在ZIP内；在其他机器正常安装PyMuPDF即可。可通过 `TASK6_QA_DEPS` 为审计子进程指定已有隔离安装目录。审计失败使构建返回非零，不发布新的成功声明；`--skip-qa` 只适用于明确记录无法完成自动审计的环境，不能据此声称核验通过。

如需重编译预览，在本目录运行两遍：

```bash
xelatex -interaction=nonstopmode -halt-on-error preview.tex
xelatex -interaction=nonstopmode -halt-on-error preview.tex
```

图1显示完整确认水平和精度边界；图2显示M1/M2弱信号损失、中强信号饱和与coherent样本量/通道数效应；图3保留全部不利差异及45项校正；图4解释峰值相同而总体系数效应不同的结构，不作新功效或唯一机制证明。图内英文标签避免跨平台中文字体问题，中文正文和完整图注保留；矢量文字可编辑，主图PNG为360/600 dpi。

所有原实验源码、结果、随机种子、锁、发布包保持只读；本任务不需要上传集群、不连接集群、不提交作业，不生成新的Monte Carlo数据。ZIP不含大型逐次记录或环境目录。
