"""Package the explicit monitoring scope; no legacy whole-cell controller or data upload."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parent.parent

def package(output):
    output=Path(output)
    if output.exists():raise FileExistsError('Choose a new output name; existing evidence is not overwritten')
    names=set(json.loads((ROOT/'research_scope.json').read_text(encoding='utf-8'))['runtime_files'])
    names.update(['README.md','docker/build_image.py','scripts/package_monitoring.py','docs/pham_vi_bai_bao_20261106.md','docs/chay_goi_giam_sat.md','docs/TOM_TAT_DU_AN.md','docs/doi_chung_thoi_gian_20261106.md','paper/main.tex','paper/title_abstract.tex','paper/body.tex','paper/references_list.tex','paper/llncs.cls','paper/prepare.py','paper/export_pdf.py','paper/generated/eta_ml_table.tex','paper/generated/eta_monitor_table.tex','paper/generated/network_clock_table.tex','reports/dt_cppps_manuscript_virtual.pdf'])
    names.update('paper/evidence/'+n for n in ['audit.json','claims.csv','source_manifest.json','pdf_qa.json','notes.md','literature_sources_20261103.json','literature_metadata_20261103.json','literature_scope_20261106.json','eta_ml_recording_audit_20261106.json','network_clock_initial_audit_20261106.json'])
    names.update('docker/evidence/'+n for n in ['candidate-20261106-eta-ml.json','candidate-20261106-eta-ml-v2.json','candidate-20261106-eta-monitor-v2.json','candidate-20261106-monitoring-focus.json','candidate-20261106-network-clock.json'])
    manifest={}
    for n in sorted(names):
        p=ROOT/n
        if not p.resolve().is_relative_to(ROOT) or not p.is_file() or p.is_symlink():raise ValueError('Missing or unsafe source: '+n)
        manifest[n]=hashlib.sha256(p.read_bytes()).hexdigest()
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for n in manifest:z.write(ROOT/n,'Monitoring_Study/'+n)
        z.writestr('Monitoring_Study/SOURCE_HASHES.json',json.dumps(manifest,indent=2))
    with zipfile.ZipFile(output) as z:
        assert z.testzip() is None
        for n,h in manifest.items():assert hashlib.sha256(z.read('Monitoring_Study/'+n)).hexdigest()==h
    return {'file':str(output),'source_files':len(manifest),'runtime_files':len(json.loads((ROOT/'research_scope.json').read_text())['runtime_files']),'sha256':hashlib.sha256(output.read_bytes()).hexdigest()}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);print(json.dumps(package(p.parse_args().output)))
