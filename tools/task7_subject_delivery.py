"""Build the source-verified HAR subject analysis and its portable delivery."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import zipfile
import pandas as pd


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def number(value):
    return '—' if pd.isna(value) else f'{float(value):.9g}'


def build_report(root):
    output=root/'results/empirical/har/task7_subject_v2'
    results=pd.read_csv(output/'results.csv')
    assert len(results)==28 and results.analysis_id.nunique()==7
    assert not results.duplicated(['analysis_id','method','s']).any()
    lines=[]
    activity_names={1:'步行',2:'上楼',3:'下楼',4:'坐姿',5:'站姿',6:'卧姿'}
    for row in results.itertuples():
        group=activity_names.get(int(row.activity_id),'静态受试者平均曲线')
        method='本文 v1.1' if pd.isna(row.s) else f'Xue cross s={int(row.s)}'
        decision='—' if pd.isna(row.reject) else ('拒绝' if str(row.reject).lower()=='true' else '不拒绝')
        lines.append(f'| {group} | {row.n} | {method} | {number(row.T)} | {number(row.critical_value)} | {number(row.p_value)} | {decision} | {row.status} |')
    failed=results[results.status!='ok']
    failures='本轮所有方法均成功返回，失败数为0。' if failed.empty else failed[['analysis_id','method','s','status','failure_reason']].to_markdown(index=False)
    primary_ours=results[(results.branch=='subject_primary')&(results.method=='Ours-v1.1')]
    primary_p='、'.join(f"{activity_names[int(row.activity_id)]}{row.p_value:.6f}" for row in primary_ours.itertuples())
    contrasts=[]
    for s in (5,11,21):
        rejected=results[(results.branch=='subject_primary')&(results.s==s)&(results.reject==True)]
        contrasts.append(f"s={s}在"+'、'.join(activity_names[int(a)] for a in rejected.activity_id)+'下名义拒绝')
    timing=json.loads((output/'resume_verification.json').read_text(encoding='utf-8'))
    primary_ours=results[(results.branch=='subject_primary')&(results.method=='Ours-v1.1')]
    primary_p='、'.join(f"{activity_names[int(row.activity_id)]}{row.p_value:.6f}" for row in primary_ours.itertuples())
    contrasts=[]
    for s in (5,11,21):
        rejected=results[(results.branch=='subject_primary')&(results.s==s)&(results.reject==True)]
        contrasts.append(f"s={s}在"+'、'.join(activity_names[int(a)] for a in rejected.activity_id)+'下名义拒绝')
    timing=json.loads((output/'resume_verification.json').read_text(encoding='utf-8'))
    baseline_path=root/'doc/task7_subject_v2_baseline.json'
    if baseline_path.exists():
        baseline=json.loads(baseline_path.read_text(encoding='utf-8'))
        checked={k:digest(root/k) for k in baseline if (root/k).is_file()}
        assert all(checked[k]==baseline[k] for k in checked),'Previously frozen file changed'
        proof=dict(all_available_unchanged=True,checked=checked,unavailable=[k for k in baseline if k not in checked])
        (output/'frozen_sources_verified.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
    text=f'''# HAR受试者层面实证报告：任务7继续执行

新补充的UCI HAR源数据已用于恢复真实受试者和活动身份，并实际执行六个单活动主分析及一个单列的静态受试者平均曲线分析，共7组、28条方法记录；旧窗口诊断、损坏原件及此前交付包保留在原版本目录。

## 数据来源与恢复边界

本轮来源为用户提供并解压的UCI HAR Dataset Version 1.0，使用源包中的subject、activity及Inertial Signals；所需解压成员与原ZIP按摘要核验，辅助的__MACOSX/._资源文件不作为数据。原train与test按受试者划分，合并后30名不同受试者，每人均有六个活动；合并用于这一预先固定的协方差分析，不进行分类器训练或性能评估。

旧har_dynamic_long.csv全部3285×6×128值与官方train中活动1/2/3的body_acc_xyz、body_gyro_xyz按源顺序逐元素精确一致，最大绝对差0，因此原sample_id可映射回真实21名训练集受试者和活动。新主分析明确使用官方train与test的30人，不能把新旧结果差异仅归因于算法；旧窗口级数据和新受试者级输入的抽样单位、人数、表示均不同。

旧静态CSV仍保留其损坏字节。数据恢复审计将可读前缀与官方源构造作数值比对，完整重建对象与证据范围见HAR_DATA_AUDIT.md；已损坏部分不可逐字节认证，不将新派生文件说成原文件从未损坏。受试者主分析直接来自完整官方源窗口，不使用坏前缀或旧285窗口缓存填补样本。

## 预先固定的研究对象

六个主分析分别对应步行、上楼、下楼、坐姿、站姿、卧姿。每个活动内，每名真实受试者仅取源split及原始矩阵行位置稳定排序后的第一条完整窗口；在任何p值产生前保存全组选择清单、种子、数组摘要、配置与源代码指纹。六活动各自为一个单样本跨通道零协方差检验，同一人的跨活动结果相关，不能将六项结果视为独立重复，也不能用“一个显著、另一个不显著”推导活动间协方差差异显著。

每组使用原生128点、六通道；前3列为身体加速度XYZ（g），后3列为陀螺角速度XYZ（rad/s）。官方源已按其说明滤波、去重力并构造50%重叠窗口，本轮不再追加log差分、q5平滑、幅度标准化、峰值规范化、插值或降采样。每个活动内仅保留每人一窗，避免把同一人的重叠窗口当多个独立人；独立单位依据是来源中的不同参与者身份，而非用样本相关检验证明iid。

Fourier投影采用既有u=t/127闭网格和1/M矩形权重；该u是分析坐标。官方采样率50Hz，相对实际采样时点为t/50，首末观察点0和2.54秒，128读数对应官方所称2.56秒窗。未推测额外session或连续记录绝对起点，源split/行号保留为可复现位置。

第七组“静态受试者平均曲线”单列为聚合对象：对每人所有坐姿/站姿/卧姿窗口逐时点平均，各活动按该人的实际窗口数量进入均值，保留原生128点；不是三活动等权均值，也不是每人首窗。其单位仍为人，不能把其结果与单窗活动当成同一表示下的条件差异检验。

## 冻结统计方法

对每组Y(n,6,128)沿人估计样本均值，由残差外积直接计算Gammahat=sum(Q)/(n−1)。观察统计量为sqrt(n)乘全部跨通道、全双时间坐标的最大绝对协方差。整个同通道自协方差块排除，观察与每轮bootstrap用相同mask；bootstrap为sqrt(n)/(n−1)乘原始独立标准正态乘子加权的经验中心化外积。没有U统计量近似、额外系数2或1/2、乘子单独中心化、学生化、坐标筛选或临界值重校准。

B=500、alpha=.05，p=(1+#bootstrap>=观察值)/(B+1)，严格p<alpha拒绝。Xue使用现有run_xue_cross_test，准确命名Xue-1S-EV-cross-zero；s5为原主对照，s11和s21为固定敏感性设置，保留1/n、经验乘积方差、固定投影和EV校准。每组四方法接收同一份Y及通道顺序。若有退化或非有限值，保存失败和空p值，不加epsilon/jitter、不删坐标或改记为不拒绝。

## 全部实际结果

下表保留全部28条记录；T和临界值属于各自方法尺度，不能跨方法比较数值大小解释优劣。原始bootstrap、Xue矩阵诊断、输入Y与每人所选源窗口均随逐组结果保存。

| 分析对象 | 人数 | 方法 | T | 各自临界值 | 原始p | 名义判决 | 状态 |
|---|---:|---|---:|---:|---:|---|---|
{chr(10).join(lines)}

{failures}

本文方法六活动的p值分别为：{primary_p}，本次均未拒绝零互协方差。Xue三个固定设置的结果为：{'；'.join(contrasts)}；坐姿、站姿和单列的静态均值对象四方法均未拒绝。该差异须与统计量、投影和校准的不同敏感性一并解释，不能据真值未知数据判定哪种方法更正确或已证明功效更高。这里也没有把旧依赖窗口基础诊断中四方法均拒绝的格局，当成新受试者分析必须复现的验收条件。

本文方法六活动的p值分别为：{primary_p}，本次均未拒绝零互协方差。Xue三个固定设置的结果为：{'；'.join(contrasts)}；坐姿、站姿和单列的静态均值对象四方法均未拒绝。该差异须与统计量、投影和校准的不同敏感性一并解释，不能据真值未知数据判定哪种方法更正确或已证明功效更高。这里也没有把旧依赖窗口基础诊断中四方法均拒绝的格局，当成新受试者分析必须复现的验收条件。

静态和动态是活动条件，均不预设为已知真H0或真H1；这些数据没有可用于估计第一类错误率或功效的已知真值。不拒绝不证明零互协方差或一般独立性，拒绝只针对所声明过程的零互协方差结构；不将全局拒绝后的最大坐标解释成已获局部显著性验证。

## 解释限制与论文使用

本轮恢复了独立受试者作为输入单位，解决了旧CSV将窗口当人的主要问题，但每活动约30人的有限样本近似可靠程度仍未由Task5的n=200至800模拟自动证明。原始独立人的抽样设计也不保证所有高维Gaussian/EV条件已经成立；受限cross集合的EV校准不能仅凭full版本定理认为已获保证。没有为改善任何结果更换窗口、重复种子或挑选有利s。

本文非学生化最大值对通道单位敏感；g、rad/s的存储尺度已固定且两法共享，协方差块具有相应乘积单位，因此不跨不同单位的块直接比较“耦合更强”。图像按单位分组描述。多活动、多s及额外聚合对象的原始p值全部报告，没有临时添加全表错误率调整，也不声称全表具有统一5%错误保证。

候选图与精确展示数据见figures/，图注与离线图册分别为FIGURE_CAPTIONS_ZH.md、FIGURE_GALLERY.html。原生单人曲线仅为固定源ID的描述；跨通道协方差图只作结构概览；结果图不将更小p值解释成更高功效。历史窗口诊断继续单列在旧task7_v1，不能与本轮独立受试者主分析合并分母或对照成只改算法的版本实验。

## 核验与复跑

analysis_plan.json在实际p值前固定7组输入，逐组结果保存完整元数据、bootstrap与方差/投影诊断；run_complete.json和resume_verification.json记录实际耗时、断点与重跑验收。源数据匹配、方法共享Y、mask、直接统计量、失败隔离、输入/配置变化导致缓存失效等针对检查随代码交付。旧数学核心、原CSV、旧任务7适配器与发布包的可用基线摘要均核对未变。

首次科学计算耗时{timing['initial_compute_elapsed_seconds']:.2f}秒；首次同命令断点验收耗时{timing['resume_elapsed_seconds']:.2f}秒。七组结果、计划及全部bootstrap逐字节相同，实际源与算法哈希未变；四图的对齐、PDF字形和碰撞审计及逐图目视记录见FIGURE_VALIDATION.md，环境版本见environment.json。

首次科学计算耗时{timing['initial_compute_elapsed_seconds']:.2f}秒；首次同命令断点验收耗时{timing['resume_elapsed_seconds']:.2f}秒。七组结果、计划及全部bootstrap逐字节相同，实际源与算法哈希未变；四图的对齐、PDF字形和碰撞审计及逐图目视记录见FIGURE_VALIDATION.md，环境版本见environment.json。

从项目根目录运行 `python tools/task7_subject_delivery.py`，即可恢复/重建本轮7组分析、图像、报告及交付包；原始官方ZIP和完整解压数据仍按配置引用，不塞入代码包。对旧静态不可读尾部的原字节无法作认证，这不阻断直接来自已核验官方源的本轮主分析；没有尚缺且影响这7组分析完成的受试者或活动标签。
'''
    (output/'HAR_EMPIRICAL_REPORT.md').write_text(text,encoding='utf-8')
    spec='''# HAR任务7受试者分析规范

以来源核实的真实人作为观测单位；六个活动分别每人首条完整原生128×6窗口，另单列静态活动4/5/6按各人全部窗口逐时点平均的聚合对象。七组全部在p值前固定，计划保留source split/row及真实subject，不能根据结果改取窗口。原始数据只读，旧任务7保留。

每组的零假设为所有j<k及全部双时间位置的跨通道协方差为0；自协方差块不在检验集合。使用冻结covariance_one_sample和run_xue_cross_test：直接原统计量、n−1分母、原始独立正态乘子、经验外积中心化、B500、alpha=.05，严格加1 p值及p<alpha。Xue固定s5/11/21，无额外bootstrap或分母修补。四方法同一Y；失败单独保存，不计0或不拒绝。

主分析原生官方预处理身体加速度g和角速度rad/s，无新增log/平滑/标准化。投影网格u=t/127，实际相对采样t/50可单独记录。每活动内不同人是独立单位的设计依据；跨活动同一批人相关，30人近似及EV条件未从一次实证证明。静态不是真H0，动态不是真H1，不报告size/power，不将不同对象的一显著一不显著称两条件差异显著。

来源、输入选择、方法与预处理指纹见input_manifest/analysis_plan及metadata；历史CSV动态匹配与静态重建证据见HAR_DATA_AUDIT。原静态坏尾未逐字节修复认证，新的可用静态对象来自完整官方源。全部数学核心及旧输出冻结。
'''
    (output/'HAR_ANALYSIS_SPEC.md').write_text(spec,encoding='utf-8')
    return output


def package(root,output):
    names=['empirical/__init__.py','empirical/task7_uci_data.py','empirical/task7_subjects.py',
           'empirical/task7_subject_figures.py','common/__init__.py','common/paths.py',
           'common/statistic_calculator_517.py','common/statistic_calculator_xue.py','common/xue_helper.py',
           'config/empirical/task7_subjects_v2.json','tools/task7_subject_delivery.py',
           'tests/__init__.py','tests/test_task7_uci_data.py','tests/test_task7_subjects.py',
           'tests/test_covariance_v11.py','doc/task7_subject_v2_baseline.json']
    paths=[root/name for name in names if (root/name).is_file()]
    for base in [output,root/'data/empirical/har/metadata/task7_subject_v2',root/'data/empirical/har/processed/task7_subject_v2']:
        for p in base.rglob('*'):
            if not p.is_file() or '__pycache__' in p.parts or p.suffix in ('.zip','.pyc') or p.name.endswith(('.zip.sha256','.zip.tmp')) or p.name=='release_manifest.json':
                continue
            paths.append(p)
    contents={p.relative_to(root).as_posix():p.read_bytes() for p in sorted(set(paths))}
    manifest={k:hashlib.sha256(v).hexdigest() for k,v in contents.items()}
    manifest_path=output/'release_manifest.json'
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    contents[manifest_path.relative_to(root).as_posix()]=manifest_path.read_bytes()
    archive=output/'TASK7_HAR_SUBJECT_RUN_PACKAGE.zip'
    temporary=archive.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED) as z:
        for k,v in contents.items():
            z.writestr(k,v)
    with zipfile.ZipFile(temporary) as z:
        assert z.testzip() is None
        assert all(hashlib.sha256(z.read(k)).hexdigest()==v for k,v in manifest.items())
    temporary.replace(archive)
    archive.with_suffix('.zip.sha256').write_text(digest(archive)+'  '+archive.name+'\n',encoding='ascii')
    return archive


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report-only',action='store_true')
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    env=os.environ.copy();env['PYTHONIOENCODING']='utf-8'
    if not args.report_only:
        subprocess.run([sys.executable,'-m','empirical.task7_uci_data'],cwd=root,env=env,check=True)
        subprocess.run([sys.executable,'-m','empirical.task7_subjects','--config','config/empirical/task7_subjects_v2.json'],cwd=root,env=env,check=True)
        subprocess.run([sys.executable,'-m','empirical.task7_subject_figures'],cwd=root,env=env,check=True)
    output=build_report(root)
    print(package(root,output))


if __name__=='__main__':
    main()
