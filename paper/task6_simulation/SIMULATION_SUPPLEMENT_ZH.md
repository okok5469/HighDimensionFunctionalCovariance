# 模拟实验补充材料

本材料与模拟章节配套，机器CSV全部概率以0至1保存；配对差为本文减去固定Fourier的Xue单样本EV扩展。主表2/3的可读版以四方法横列显示拒绝数/重复数、拒绝率及CP95%区间（%），补表保持概率单位；正文中的差以百分点表示。探索与独立确认分别报告，不能合并分母。探索的较小重复数及多场景搜索意味着其趋势只作描述。

## S1 完整设计与参数

全部实验使用半开网格 (u_l=l/64,l=0,\ldots,63)，高斯创新，独立受试者，生成均值为零，但两个检验均估计样本均值。观测噪声标准差为0.05，在潜在过程归一化后加入。H1每次重复随机抽取两条不共享端点的通道边，同一重复的受试者共用边支持。因此信号在通道支持上稀疏；时间域相干不意味着全部通道共同变化。四个对称非对角元素对应这两条边。

M1五基傅里叶使用原基序与五个基，谱权重为 λ_k=(200/441)k⁻²。归一化后最大潜在边际方差和信号形状网格峰值均为1。M2由63个方差为1/64的独立标准布朗增量生成，过程乘 √(64/63)，协方差乘64/63；保留首时点潜在值为零但含测量噪声的观测，不作周期化。coherent使用20维平坦潜在背景 Σ=I/20、方向向量 a=ϕ(3/8)/20 及秩一信号D=aaᵀ。

local与coherent使用同一q=20平坦背景，其信号为原冻结Fejér形状；fast使用q=20正余弦配对、h⁻⁴快速衰减谱。二者仅在(800,20)探索，不提供确认结论。对应全部原始spec身份、整数计数与来源键保存在[完整探索表](tables/tableS01_pilot_methods.md)，不另行改变生成器、归一化、信号或检验。

探索覆盖(200,20)、(400,20)、(800,20)、(800,50)，主模型强度为0、0.15、0.30、0.45、0.60；H0每格500次，H1每格50次。确认覆盖M1和M2的(800,20)，以及coherent的(400,20)、(800,20)、(800,50)，强度为0、0.15、0.30、0.60；H0每格1000次，H1每格300次。详见[设计表](tables/table01_design.md)。local/coherent相同探索形状引用一份flat H0，只有13个探索H0物理单元。

固定Fourier设置s5为主对照，s11和s21为预设敏感性设置。s5包含常数及M1前四个生成基、遗漏第五基；s11/s21覆盖M1潜在信号，s21覆盖coherent潜在生成方向。M2潜在网格秩为63，s21未完全覆盖。潜在覆盖不能等同于覆盖64维测量噪声，也不支持事后选取最有利的s。

## S2 完整结果表与图

全部确认水平和功效见[表2](tables/table02_confirm_size.md)与[表3](tables/table03_confirm_power.md)，完整探索方法表见[补表S1](tables/tableS01_pilot_methods.md)。表内保留拒绝数、有效重复数、点估计、CP95%和MCSE，CSV提供原始精度，TeX提供可编辑长表。

全部45项确认配对见[补表S2](tables/tableS02_confirm_paired.md)，全部168项探索配对见[补表S3](tables/tableS03_pilot_paired.md)。两表同时保留四格计数、配对差、区间、方向、非劣和双方H0状态。全部方法的统计量及临界值中位数见[补表S4](tables/tableS04_diagnostics.md)；完整诊断分位数保存在[data/diagnostics.csv](data/diagnostics.csv)。诊断量只帮助解释同一算法的尺度，不根据中位数推算拒绝概率，不跨算法比较统计量大小。

补图S1为[全部确认配对区间](figures/supplement/figS01_all_confirm_pairs.png)。探索功效分模型显示于[M1](figures/supplement/figS_power_M1.png)、[M2](figures/supplement/figS_power_M2.png)、[coherent](figures/supplement/figS_power_coherent.png)、[local](figures/supplement/figS_power_local.png)、[fast](figures/supplement/figS_power_fast.png)；探索水平分背景显示于[M1](figures/supplement/figS_size_M1.png)、[M2](figures/supplement/figS_size_M2.png)、[flat](figures/supplement/figS_size_flat.png)、[fast](figures/supplement/figS_size_fast.png)。这些图保留全部三个Fourier设置及每个探索形状，不能视作独立确认。

coherent探索中(400,20)在τ=0.30的本文功效为34/50=68%，独立确认为213/300=71%；两阶段不能互换。固定n=800时，p=20至50的确认弱信号功效从33/300=11%至26/300=8.67%，τ=0.30则为300/300和299/300。探索显示的10%至6%不是确认趋势；维数增加仍有弱信号代价。local/fast及τ=0.45的结果仅具有探索性质。

## S3 区间、校准与修正说明

单格使用双侧Clopper–Pearson 95%精确区间及MCSE=√[p̂(1−p̂)/R]。零拒绝或全拒绝时，插件MCSE为零，CP区间仍有正宽度；300/300的区间为[0.987779,1]。确认H0区间完全落在[0.03,0.07]才支持接近；上界小于0.03为明显保守，下界大于0.07为明显膨胀，其余未决。coherent(400,20)本文下界约0.02958，按未舍入数值仍未决。

四格依次为双方拒绝a、仅本文拒绝b、仅Xue拒绝c、双方不拒绝d，差为(b−c)/R。对b/R与c/R分别构造CP区间，每尾概率0.05/(4m)，组合为[Lb−Uc,Ub−Lc]。确认固定m=45，即使主图只展示部分比较也不缩小。探索以m=1作逐项描述，原CSV中的m=168区间另存于source_adjusted_ci_low/high与source_familywise_declarations，不覆盖输入。

新的展示层修正原报告六条M1/M2弱信号配对的“方向证据不足”标签：其校正区间全低于0、上界低于−0.05，均支持负差及超过5个百分点劣势。完整更正行见[data/label_corrections.csv](data/label_corrections.csv)。确认45项的互斥展示分类实际为18项正差、15项仅支持非劣、6项负差、6项方向未决；正差也满足非劣，因此应独立保留direction、noninferiority、inferiority_beyond_margin三个字段。未证优势不能一律改为方向未决，未显著也不能等同非劣。

只有双方对应H0均支持接近，才将配对差解释为预定工作性容忍范围内的功效比较，否则仅解释为固定名义阈值下拒绝概率差。M1三Xue校准均未决；M2四方法支持接近；coherent(800,50)仅本文与s11双方支持接近。校准未决不等于证明失准，逐格CP与配对多重校正不构成统一联合5%保证，也未证明严格相同的实际5%水平。

## S4 适用范围与可复现边界

本研究只验证所列高斯分布、n、p、网格、噪声和离散强度。已考察τ=0.30与0.60的高功效不能外推至所有τ≥0.30；coherent的τ=0.15低功效以及M1/M2弱信号相对劣势均保留。pM>n不等于验证p>n，未验证非高斯稳健性，也未验证双样本推广。

本次只核对小型汇总文件、锁、既有完整性声明和报告，未重新扫描18,800份逐次记录，也未新生成数据或运行bootstrap。既有报告记载的18,805份逐次审计及30项来源核验属于此前审计，不冒称为本次重新完成。完整来源清单见[source_manifest.json](source_manifest.json)，本次核验细节见[DATA_VALIDATION.md](DATA_VALIDATION.md)。
