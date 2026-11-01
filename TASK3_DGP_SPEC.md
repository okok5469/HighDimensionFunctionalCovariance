# task3_v1：实现后的数据生成规范

设计依据为[任务卡3](docs/任务卡3_扩展模拟模型与集群运行.md)，实现为`simulation/task3_generators.py`。四家族八规格属于本次明确设计，不归为Xue论文原模拟。

## 完整目标与共同输入

比较完整已知目标$H_0:\Gamma=\Gamma_0$，包含自协方差、跨通道协方差及测量噪声。每份曲线$Y$生成一次，本文方法与`Xue-1S-EV-full / xue-audit-v1 / fixed-Fourier-s5`及固定$s=11,21$接收同一$Y$和$\Gamma_0$，不传oracle系数。本文保持v1.1直接最大值、原始高斯乘子、$B=500,\alpha=.05$；Xue保留$1/n$分母、经验乘积方差学生化与EV校准。

## 新模型统一结构

$H=10,q=20$，$\phi_{2h-1}(u)=\sqrt2\sin(2\pi hu)$、$\phi_{2h}(u)=\sqrt2\cos(2\pi hu)$。网格$u_\ell=\ell/64,\ell=0,\ldots,63$，不重复1端点，$t_0=3/8=u_{24}$，$\Phi^\top\Phi/64=I$。冒烟保持64点与20个生成方向。

$Y_{rj\ell}=\sum_{k=1}^{20}A_{rjk}\phi_k(u_\ell)+\varepsilon_{rj\ell}$，独立高斯噪声方差.0025。每个重复从$p$通道均匀选4个不同通道配成两条不相交边，受试者内支持固定；对称邻接矩阵$E$满足$\|E\|_{op}=1,\|E\|_F^2=4$。通道优先的系数协方差为$I_p\otimes\Lambda+\tau E\otimes D$。

每条匹配边独立生成$Z_+\sim N(0,\Lambda+\tau D),Z_-\sim N(0,\Lambda-\tau D)$，令$A_j=(Z_++Z_-)/\sqrt2,A_k=(Z_+-Z_-)/\sqrt2$；未配对通道独立生成。先检查$\rho=\tau\|\Lambda^{-1/2}D\Lambda^{-1/2}\|_{op}<1$，不裁负特征值、不修补协方差。

$\Gamma_{0,jk}(u_\ell,u_m)=1\{j=k\}[\phi(u_\ell)^\top\Lambda\phi(u_m)+.0025\,1\{\ell=m\}]$；备择差为$\tau E_{jk}\phi(u_\ell)^\top D\phi(u_m)$，不加入零目标。所有新规格无噪声点方差1，含噪声1.0025，不对样本再标准化。

| 家族/规格 | $\Lambda,D$ | $\tau=.30$时$\rho$ |
|---|---|---:|
| spectrum：`spectrum_fast_b4`、`spectrum_slow_b1`、`spectrum_flat_b0` | $w_h=h^{-\beta}/\sum_{a=1}^{10}a^{-\beta}$，$\lambda_{2h-1}=\lambda_{2h}=w_h/2,D=\Lambda$，$\beta=4,1,0$ | .30 |
| band：`band_head`、`band_tail` | $\Lambda=I/20$，$D$在$J=1{:}8$或$13{:}20$的对角为$1/8$ | .75 |
| coherent：`coherent_all`、`coherent_tail` | $\Lambda=I/20,D=aa^\top$，$a_k=1\{k\in J\}\phi_k(t_0)/|J|$，$J=1{:}20$或$13{:}20$ | .30、.75 |
| local：`local_fejer` | $\Lambda=I/20,D=aa^\top$，$a_{2h-1}=\sqrt2(1-h/11)\sin(2\pi ht_0)/10$，余弦对应$a_{2h}$ | $.30\times14/11$ |

local对应$f(u)=\frac2{10}\sum_h(1-h/11)\cos(2\pi h(u-t_0))$、$K_D(s,t)=f(s)f(t)$，有旁瓣，不是紧支撑窗口。八规格均有$\max|\phi(s)^\top D\phi(t)|=1$，故$\|\Gamma_\tau-\Gamma_0\|_{max}=\tau$，但Frobenius总能量不全相等。

## 两个原生成器参考

`legacy_M1_full_reference`、`legacy_M2_full_reference`调用原生成器，保持五基/原谱、30点闭网格、噪声与原上三角支持抽样。原时间核$K$对应$\kappa=\max|K|$，使用`legacy_delta=tau/kappa`、$s_0=4$与原$C=I+\Omega$，记录三个不同参数；完整目标为$1\{j=k\}[K(u_\ell,u_m)+.0025\,1\{\ell=m\}]$。两个新full参考不覆盖原20个cross配置，不同网格只在各自同场景内比较方法。

## 诊断、随机数与解释

每场景保存基/网格、$\Lambda,D$、正定性界、边际方差、时间峰值与加权Frobenius范数，使用实际Fourier算子$L_s$计算$L_s\Gamma_0L_s^\top$及差异。重构时间峰值比与正交坐标Frobenius比独立报告，能量比为范数比平方，零分母记不适用；总体高斯乘积方差诊断只作解释，不进入实际检验校准。

64点网格下s5/s11/s21的重构峰值比：快谱`.98194462/.99844307/1`、慢谱`.51212573/.77956916/1`、平谱`.20/.50/1`、head`.50/1/1`、tail`0/0/1`、coherent-all`.04/.25/1`、coherent-tail`0/0/1`、local`.11933884/.52892562/1`。它们不是标准化系数信号的信息百分比，平坦/慢谱不保证本文胜出。

种子基数20261021；稳定数据键含study/phase、实际零分布或备择规格、完整DGP与形状、重复编号。支持/信号/噪声/bootstrap使用独立命名流；smoke/benchmark/pilot/confirm独立。输出路径、worker数、方法顺序与Slurm ID不入数据键。相同零分布只生成一组物理重复，共享`null_group_id`；方法配置另进run_id，不把共享零假设算成多份独立证据。
