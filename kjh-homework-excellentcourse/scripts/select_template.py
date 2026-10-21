"""Copy explicit template, otherwise bundled default; never overwrite."""
import argparse,hashlib,json,shutil
from pathlib import Path
from zipfile import ZipFile
def main():
 p=argparse.ArgumentParser();p.add_argument('--template');p.add_argument('--output',required=True);p.add_argument('--report',required=True);a=p.parse_args()
 source=Path(a.template) if a.template else Path(__file__).resolve().parents[1]/'assets/default_homework.docx'
 out,report=Path(a.output),Path(a.report)
 if len({source.resolve(),out.resolve(),report.resolve()})!=3 or out.exists() or report.exists():raise ValueError('New and distinct output/report paths required')
 with ZipFile(source) as z:
  if z.testzip() is not None or 'word/document.xml' not in z.namelist():raise ValueError('Not a valid Word package')
 out.parent.mkdir(parents=True,exist_ok=True);report.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(source,out)
 h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
 report.write_text(json.dumps({'mode':'explicit' if a.template else 'default','source':str(source.resolve()),'output':str(out.resolve()),'source_hash':h(source),'output_hash':h(out),'status':'COPIED_NOT_REVIEWED'},ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
