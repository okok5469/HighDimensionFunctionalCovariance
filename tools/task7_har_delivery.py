"""Run/resume the authorized HAR diagnostics, then build their report and delivery."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
import pandas as pd


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def report(root):
    output=root/'results/empirical/har/task7_v1'
    run=output/'har_empirical_task7_v1'
    table=pd.read_csv(run/'results.csv')
    assert len(table)==3604 and table.analysis_id.nunique()==901
    base=table[table.experiment=='basic']
    complete=json.loads((run/'resume_verification.json').read_text(encoding='utf-8'))
    manifest=json.loads((root/'data/empirical/har/metadata/task7_v1/frozen_sources_before.json').read_text(encoding='utf-8'))
    assert all(sha(root/k)==v for k,v in manifest['sha256'].items())
    (output/'frozen_sources_after.json').write_text(json.dumps(dict(all_unchanged=True,sha256=manifest['sha256']),indent=2),encoding='utf-8')
    rows=[]
    for row in base.itertuples():
        name='本文 v1.1' if pd.isna(row.s) else f'Xue cross s={int(row.s)}'
        rows.append(f'| {name} | {row.T:.10g} | {row.critical_value:.10g} | {row.p_value:.10g} | {row.status} | {bool(row.reject)} |')
    summary=pd.read_csv(run/'summary.csv')
    grid=summary[summary.experiment=='pn_grid']
    gridrows=[]
    for (n,p),group in grid.groupby(['n','p']):
        vals=[float(group[group.method=='Ours-v1.1'].rejection_proportion.iloc[0])]
        vals += [float(group[group.s==s].rejection_proportion.iloc[0]) for s in (5,11,21)]
        gridrows.append(f'| {n} | {p} | '+' | '.join(f'{v:.0%}' for v in vals)+' |')
    text=f'''# HAR实证重跑报告

本轮完成了本机数据审计和全部可追溯的历史动态窗口诊断；**尚未完成受试者层面主实证**。静态文件本机副本确实损坏，动态窗口缺真实受试者/活动映射，不能把窗口数当人数或把名义拒绝解释为有效受试者推断。

## 数据与身份

用户所列raw目录和docs/tasks目录在本机不存在；任务卡实际位于docs/，旧工程明确的数据位于data/har/，已通过配置映射，无重复复制或覆盖。动态CSV为30,684,607字节，SHA256为6335b05784bd4bf09c109fa1b9f4c997aa3d3bb39f2d0c65be38f9c948d7e1d5，严格解析420,480行、3285条128×6窗口完整。相邻窗口2937/3284对存在逐值相等半窗重叠（89.4336%）。

本机静态CSV已逐字节重新核验，535,372字节，SHA256为d860b0403608700d5f0a7901e9182f7901dcc9b4f926ee096948449cd67c5f00，首非法UTF8偏移131072，404,134个NUL；与上传损坏副本相同，这是本机独立验证的结果。坏前缀仅用于定位，没有提取前七条进行检验。历史静态缓存285×6×48无完整原始输入及真实身份，未升级为正式分析。

项目只能追溯两个CSV的原样迁移，未找到原始导出脚本、可信公开数据来源或subject/activity/session映射。六通道继续称var_0至var_5；物理名称、单位、采样率、真实人数与活动组成未知，时间0至127仅为索引。不能据128×6猜测UCI来源、50Hz或传感器名称。

## 可恢复的分析对象与冻结算法

按旧入口精确恢复动态处理：每个sample_id作为原窗口分组；各列最小值非正时平移至正，使用原函数的log(x+shift+1e-8)差分；127点上M=48、stride=2产生40条二级窗口；q=5固定Fourier伪逆重建；沿全部131400窗口轴逐坐标标准化，保留旧预处理原有+1e-12规则。该微小常数属于旧标准化，不是本轮对Xue乘积方差作jitter。新池与旧动态缓存逐元素最大差6.217248937900877e-15，在1e-12容差下同一；没有重命名为受试者。

检验的是上述预处理过程在整个双时间网格上的跨通道零协方差，排除整个同通道自协方差块。本文调用冻结covariance_one_sample，直接计算sqrt(n) max|Gammahat|，协方差分母n−1，bootstrap为sqrt(n)/(n−1)乘原始独立正态乘子加权的经验中心化外积，B=500、alpha=.05，p=(1+#bootstrap>=观察值)/(B+1)，p<alpha拒绝；没有U统计量近似、额外系数2或乘子单独中心化。

Xue调用冻结run_xue_cross_test，准确标注Xue-1S-EV-cross-zero，s5原主对照、s11/s21预设敏感性设置，保留1/n、经验乘积方差和EV校准。该受限坐标集合的EV条件未由full版本自动获得理论保证；窗口依赖又使独立性不满足。四法始终共享完全相同Y及输入指纹，没有潜在系数、自动选阶或新增bootstrap对照。

## 实际运行与完整结果

先保存analysis_plan和逐项ID再计算。基础单次为seed42、n=200、p=6、M=48；重复方案100次，seed=2025+1009r；网格n=50/100/150/200、p=3/4/5/6，每格50次，seed=5000+10n+p+1009r，通道取原前p列。共901次分析、3604条方法结果，全部成功，未删失败或不利结果。真实受试者数一律unknown。

| 方法 | T（各自尺度） | 各自临界值 | 原始p | 状态 | 名义拒绝 |
|---|---:|---:|---:|---|---|
{chr(10).join(rows)}

同一窗口池的100次重抽样中四方法均拒绝；这是该重抽样方案的结果，既不是第一类错误率，也不是已知备择功效。下表列出全部16格、每格50次的拒绝比例；不附独立二项CP区间，因为重复间共享窗口且真实受试者未知。

| n（窗口数） | p | 本文 | Xue s5 | Xue s11 | Xue s21 |
|---:|---:|---:|---:|---:|---:|
{chr(10).join(gridrows)}

基础及全部逐次结果见har_empirical_task7_v1/results.csv与results.json，完整汇总见summary.csv。每项目录保存所选源窗口及二级窗口位置、bootstrap序列、Xue方差/投影诊断、方法元数据及断点成员哈希。不同方法T或临界值不能直接比较大小解释优劣；较小p值也不证明更高功效或更正确。这里的高拒绝比例只能作为依赖窗口数值诊断，不能用作论文受试者层面主要实证证据，也不能将静态/动态解释为真H0/真H1。

## 运行核验、图像与资源

首次完整运行{complete['initial_compute_elapsed_seconds']:.2f}秒，第一次同命令断点复跑{complete['resume_elapsed_seconds']:.2f}秒；901项断点和全部成员摘要通过，汇总逐字节一致，9项针对性测试通过。记录的单进程最高peak_wset为1,115,312,128字节，这是单进程历史峰值，不能当6进程总内存峰值。没有降低B、网格、精度或删除通道，没有构建全n外积缓存。

figures/中的原始六通道曲线、跨通道样本协方差、四法p值及重抽样汇总均为实际结果图；图册为FIGURE_GALLERY.html，中文图注为FIGURE_CAPTIONS_ZH.md。图像属于数据描述和历史流程诊断候选图，不冒称主实证图；静态只报告缺项，不画伪核或零柱。旧结果与数学核心六份源文件哈希均未改变，结果写入独立版本目录。

## 仍需的最小补件

1. 完整可严格解析的静态CSV原件，或可核实上游静态数据和确切生成/聚合脚本；不能用坏前缀、补零或插值代替。
2. 动态每个sample_id对应的真实subject_id、activity、原始split/session/record、窗口起点及来源；静态subject对应真实人的映射、活动与受试者内平均等聚合规则。可用可信原始窗口加确定性导出脚本或逐窗口可验证一一匹配恢复，不能靠ID连续段和重叠链猜测。
3. 若要标物理单位和秒轴，还需可验证的六通道名称/顺序/单位及采样频率；缺失这些不应伪造标签。

当前入口明确执行已核实的历史诊断，主分支保存blocked，不声称补一份任意映射表就会自动运行。补齐并核验身份后须在独立新分析配置/输出版本中固定每活动每人首条完整曲线清单，再启用受试者分支；不复用本轮依赖窗口断点。跨活动结果非独立，单独显著/不显著不等于两活动协方差差异显著；不拒绝也不证明通道独立。
'''
    (output/'HAR_EMPIRICAL_REPORT.md').write_text(text,encoding='utf-8')
    return output


def package(root,output):
    paths=[root/p for p in ['empirical/__init__.py','empirical/task7_har.py','empirical/task7_figures.py',
        'empirical/har_data_loader.py','common/__init__.py','common/statistic_calculator_517.py',
        'common/statistic_calculator_xue.py','common/xue_helper.py','common/paths.py',
        'config/empirical/task7_har.json','tools/task7_har_delivery.py','tests/__init__.py',
        'tests/test_task7_har.py','tests/test_covariance_v11.py']]
    paths += list((root/'data/empirical/har/metadata/task7_v1').glob('*'))
    for p in output.rglob('*'):
        if not p.is_file() or p.suffix in ('.zip','.pyc') or '__pycache__' in p.parts or p.name.endswith('.zip.sha256') or p.name=='release_manifest.json':
            continue
        if 'legacy_diagnostic' in p.parts and p.name not in ('result.json','selected_windows.csv','bootstrap.npy'):
            continue
        paths.append(p)
    paths=sorted(set(p for p in paths if p.is_file()))
    contents={p.relative_to(root).as_posix():p.read_bytes() for p in paths}
    manifest={k:hashlib.sha256(v).hexdigest() for k,v in contents.items()}
    (output/'release_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    contents[(output/'release_manifest.json').relative_to(root).as_posix()]=(output/'release_manifest.json').read_bytes()
    archive=output/'TASK7_HAR_RUN_PACKAGE.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for key,value in contents.items():
            z.writestr(key,value)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert all(hashlib.sha256(z.read(k)).hexdigest()==v for k,v in manifest.items())
    archive.with_suffix('.zip.sha256').write_text(sha(archive)+'  '+archive.name+'\n',encoding='ascii')
    return archive


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--report-only',action='store_true')
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    if not args.report_only:
        subprocess.run([sys.executable,'-m','empirical.task7_har','--config','config/empirical/task7_har.json'],cwd=root,check=True)
        subprocess.run([sys.executable,'-m','empirical.task7_figures'],cwd=root,check=True)
    output=report(root)
    print(package(root,output))


if __name__=='__main__':
    main()
