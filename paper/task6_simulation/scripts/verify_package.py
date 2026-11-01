"""Verify all archived bytes and rebuild in a clean independent directory."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


def verify(root):
    archive=root/'TASK6_SIMULATION_CHAPTER_AND_FIGURES.zip'
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==archive.with_suffix('.zip.sha256').read_text().split()[0]
    with tempfile.TemporaryDirectory(prefix='task6_portable_') as temp:
        clean=Path(temp)
        with zipfile.ZipFile(archive) as z:
            manifest=json.loads(z.read('release_manifest.json'))
            assert all(hashlib.sha256(z.read(k)).hexdigest()==v for k,v in manifest.items())
            assert all(not Path(k).is_absolute() and '..' not in Path(k).parts for k in z.namelist())
            z.extractall(clean)
        author_files=['SIMULATION_SECTION_ZH.md','simulation_section.tex','FIGURE_CAPTIONS_ZH.md']
        before={k:hashlib.sha256((clean/k).read_bytes()).hexdigest() for k in author_files}
        env=os.environ.copy()
        env['TASK6_QA_DEPS']=str(root/'.qa_deps')
        run=subprocess.run([sys.executable,'scripts/build_task6_paper.py','--config','task6_paper_config.json'],
                           cwd=clean,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
        if run.returncode:
            raise RuntimeError(run.stdout+run.stderr)
        assert before=={k:hashlib.sha256((clean/k).read_bytes()).hexdigest() for k in author_files}
        derived=['methods.csv','paired.csv','geometry_diagnostics.csv','figure_coverage.json']
        assert all((clean/'data'/k).read_bytes()==(root/'data'/k).read_bytes() for k in derived)
        result=dict(zip_members_verified=len(manifest),clean_rebuild='passed',
                    author_files_preserved=True,derived_data_byte_identical=derived,
                    full_pdf_qa_reexecuted=True,stdout=run.stdout.strip())
        (root/'data/portable_rebuild_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        return result


if __name__=='__main__':
    print(json.dumps(verify(Path(__file__).resolve().parents[1]),ensure_ascii=False,indent=2))
