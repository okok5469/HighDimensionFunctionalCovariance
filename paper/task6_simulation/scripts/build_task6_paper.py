"""Portable deterministic rebuild. Never imports experimental test routines."""
from pathlib import Path
import argparse
import hashlib
import html
import json
import os
import subprocess
import sys
import zipfile


def audits(root):
    qa=Path(__file__).parent/'qa'
    results=[]
    env=os.environ.copy()
    env['PYTHONIOENCODING']='utf-8'
    for pdf in sorted((root/'figures').rglob('*.pdf')):
        if '.collision-audit' in pdf.name:
            continue
        for tool,args in [('audit_pdf_text.py',['--json']),
                          ('audit_figure_collisions.py',['--json-out',str(pdf.with_suffix('.collision-audit.json'))])]:
            script=qa/tool
            # Isolate optional PDF runtime from the installed scientific stack.
            code='import sys,runpy;sys.path.insert(0,sys.argv[1]);sys.argv=sys.argv[2:];runpy.run_path(sys.argv[0],run_name="__main__")'
            deps=os.environ.get('TASK6_QA_DEPS',str(root/'.qa_deps'))
            cmd=[sys.executable,'-c',code,deps,str(script),str(pdf),*args]
            run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',env=env)
            log=pdf.with_suffix('.'+tool.replace('.py','.log'))
            log.write_text(run.stdout+run.stderr,encoding='utf-8')
            results.append(dict(figure=str(pdf.relative_to(root)),tool=tool,exit_code=run.returncode))
            if run.returncode:
                raise RuntimeError(f'Figure QA blocked: {pdf.name}: {tool}; see {log.name}')
    for source in ('plot_statistics.py','geometry.py'):
        run=subprocess.run([sys.executable,str(qa/'validate_figure.py'),str(root/'scripts'/source),'--json'],capture_output=True,text=True,encoding='utf-8',env=env)
        (root/'data'/f'{source}.source-audit.json').write_text(run.stdout,encoding='utf-8')
        if run.returncode:
            raise RuntimeError(f'Source QA blocked: {source}')
    (root/'data/figure_audits.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    return results


def gallery(root):
    captions=(root/'FIGURE_CAPTIONS_ZH.md').read_text(encoding='utf-8')
    parts=['<!doctype html><html lang="zh"><meta charset="utf-8"><title>任务6图册</title>',
           '<style>body{max-width:1100px;margin:35px auto;font-family:Arial,sans-serif;line-height:1.6}img{width:100%;height:auto}section{margin:50px 0}pre{white-space:pre-wrap}</style>',
           '<h1>模拟实验论文图册</h1><p>图中英文坐标对应中文图注；所有图片来自本地实际绘制。</p>',
           '<nav><a href="SIMULATION_SECTION_ZH.md">中文正文</a> · <a href="preview.pdf">论文预览PDF</a> · <a href="SIMULATION_SUPPLEMENT_ZH.md">补充材料</a></nav>',
           '<h2>完整图注</h2><pre>'+html.escape(captions)+'</pre>']
    for png in sorted((root/'figures').rglob('*.png')):
        rel=png.relative_to(root).as_posix()
        sections=captions.split('## ')[1:]
        index={'fig01':0,'fig02':1,'fig03':2,'fig04':3}.get(png.stem[:5])
        selected=(sections[index] if index is not None else next((s for s in sections if png.stem in s), '补图：完整覆盖探索设置或确认配对；定义见上方完整中文图注。'))
        parts.append(f'<section><h2>{html.escape(png.stem)}</h2><a href="{rel[:-4]}.pdf">PDF</a> · <a href="{rel[:-4]}.svg">SVG</a><img src="{rel}" alt="{html.escape(png.stem)}"><pre>{html.escape(selected)}</pre></section>')
    (root/'FIGURE_GALLERY.html').write_text('\n'.join(parts)+'</html>',encoding='utf-8')


def package(root):
    output=root/'TASK6_SIMULATION_CHAPTER_AND_FIGURES.zip'
    files=[]
    for directory,dirs,names in os.walk(root):
        dirs[:]=sorted(d for d in dirs if d not in ('.qa_deps','__pycache__','.rebuild_check'))
        for name in sorted(names):
            p=Path(directory)/name
            if p.suffix in ('.zip','.pyc','.aux','.log','.out','.toc') or p.name.endswith('.zip.sha256'):
                continue
            files.append(p)
    manifest={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
              for p in files if p.name!='release_manifest.json'}
    (root/'release_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    files=[p for p in files if p.name!='release_manifest.json']+[root/'release_manifest.json']
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p,p.relative_to(root).as_posix())
    with zipfile.ZipFile(output) as z:
        assert z.testzip() is None
        assert all(hashlib.sha256(z.read(k)).hexdigest()==v for k,v in manifest.items())
    output.with_suffix('.zip.sha256').write_text(hashlib.sha256(output.read_bytes()).hexdigest()+'  '+output.name+'\n',encoding='ascii')
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=Path(__file__).resolve().parents[1]/'task6_paper_config.json')
    parser.add_argument('--skip-qa',action='store_true',help='only for a documented runtime without PyMuPDF; never implies QA pass')
    args=parser.parse_args()
    root=args.config.resolve().parent
    config=json.loads(args.config.read_text(encoding='utf-8'))
    assert config['experiment_id']=='task5_unified_v1'
    from prepare_data import prepare
    import plot_statistics
    from geometry import build as geometry_build
    methods,paired=prepare(root)
    coverage=plot_statistics.build(root,methods,paired)
    geometry_build(root)
    (root/'data/figure_coverage.json').write_text(json.dumps(coverage,indent=2),encoding='utf-8')
    if not args.skip_qa:
        audits(root)
    gallery(root)
    package(root)
    print(f'Rebuilt {len(methods)} method rows / {len(paired)} paired comparisons; manuscripts preserved.')


if __name__=='__main__':
    main()
