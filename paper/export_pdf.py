"""Compile the active LNCS draft with LaTeX; never approximate it with a text renderer."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
from prepare import prepare

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent

def export(engine=None):
    prepare()
    fallback=ROOT/'tmp/springer_template/tectonic/tectonic.exe'
    compiler=engine or shutil.which('tectonic') or shutil.which('pdflatex') or (str(fallback) if fallback.is_file() else None)
    if not compiler: raise SystemExit('Install Tectonic or pdfLaTeX, or pass --engine /path/to/compiler.')
    build=ROOT/'tmp/paper_build';build.mkdir(parents=True,exist_ok=True)
    if 'tectonic' in Path(compiler).name.lower():
        command=[compiler,'--keep-logs','--outdir',str(build),'main.tex']
        passes=1
    else:
        command=[compiler,'-interaction=nonstopmode','-halt-on-error','-output-directory='+str(build),'main.tex']
        passes=2
    for _ in range(passes):
        result=subprocess.run(command,cwd=HERE,text=True,capture_output=True,encoding='utf-8',errors='replace')
        (build/'compiler_output.txt').write_text(result.stdout+result.stderr,encoding='utf-8')
        if result.returncode:
            print((result.stdout+result.stderr)[-4000:]);raise SystemExit(result.returncode)
    output=ROOT/'output/pdf/dt_cppps_manuscript_virtual.pdf';output.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(build/'main.pdf',output)
    shutil.copyfile(output,ROOT/'reports/dt_cppps_manuscript_virtual.pdf')
    print(str(output),flush=True)
    return output

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--engine');export(p.parse_args().engine)
