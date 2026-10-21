"""Fill explicitly selected Word template cells while retaining package/layout parts.
Plan: list of {table,row,cell,expected,paragraphs:[{text,prototype?,bold?}]}.
Only content in selected cells changes. Each paragraph clones a local prototype.
"""
import argparse, copy, hashlib, json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as E
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
N={'w':W}
def q(s): return '{'+W+'}'+s
def main():
 a=argparse.ArgumentParser();a.add_argument('--input',required=True);a.add_argument('--output',required=True);a.add_argument('--plan',required=True);a.add_argument('--report',required=True);o=a.parse_args()
 src,dst,rpt=map(Path,(o.input,o.output,o.report))
 if src.resolve() in (dst.resolve(),rpt.resolve()) or dst.exists() or rpt.exists():raise ValueError('New output/report paths required')
 with ZipFile(src) as z: entries={x.filename:(x,z.read(x.filename)) for x in z.infolist()}
 root=E.fromstring(entries['word/document.xml'][1]);changes=[]
 for item in json.loads(Path(o.plan).read_text(encoding='utf-8')):
  cell=root.findall('.//w:tbl',N)[item['table']].findall('w:tr',N)[item['row']].findall('w:tc',N)[item['cell']]
  current=''.join(cell.xpath('.//w:t/text()',namespaces=N))
  if current!=item['expected']:raise ValueError('Template content mismatch: '+str(item['row']))
  old=cell.findall('w:p',N)
  if cell.find('w:tbl',N) is not None:raise ValueError('Nested tables require separate mapping')
  new=[]
  for p in item['paragraphs']:
   proto=old[p.get('prototype',0)];el=copy.deepcopy(proto)
   for ch in list(el):
    if ch.tag!=q('pPr'):el.remove(ch)
   pp=el.find(q('pPr'))
   if pp is not None:
    pr=pp.find(q('rPr'))
    if pr is not None:pp.remove(pr)
   run=E.SubElement(el,q('r'));rp=E.SubElement(run,q('rPr'))
   fonts=E.SubElement(rp,q('rFonts'));fonts.set(q('eastAsia'),'宋体');fonts.set(q('ascii'),'Times New Roman');fonts.set(q('hAnsi'),'Times New Roman')
   E.SubElement(rp,q('color')).set(q('val'),'000000')
   # Filled placeholder text uses the template's 10.5pt body size.
   orig=proto.find('.//w:sz',N);size=orig.get(q('val')) if orig is not None else '21'
   E.SubElement(rp,q('sz')).set(q('val'),size);E.SubElement(rp,q('szCs')).set(q('val'),size)
   if p.get('bold'):E.SubElement(rp,q('b'))
   t=E.SubElement(run,q('t'));t.set('{http://www.w3.org/XML/1998/namespace}space','preserve');t.text=p['text'];new.append(el)
  for ch in list(cell):
   if ch.tag!=q('tcPr'):cell.remove(ch)
  cell.extend(new);changes.append({'table':item['table'],'row':item['row'],'cell':item['cell'],'paragraphs':len(new)})
 # The template's authoring note is not course content. Remove only an exact plan-authorized note.
 meta=json.loads(Path(o.plan).with_suffix('.notes.json').read_text(encoding='utf-8')) if Path(o.plan).with_suffix('.notes.json').exists() else []
 for txt in meta:
  matches=[p for p in root.findall('./w:body/w:p',N) if ''.join(p.xpath('.//w:t/text()',namespaces=N))==txt]
  if len(matches)!=1:raise ValueError('Exact note not found')
  matches[0].getparent().remove(matches[0])
 data=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
 dst.parent.mkdir(parents=True,exist_ok=True)
 with ZipFile(dst,'w',ZIP_DEFLATED) as z:
  for n,(info,b) in entries.items():z.writestr(info,data if n=='word/document.xml' else b)
 rpt.parent.mkdir(parents=True,exist_ok=True);rpt.write_text(json.dumps({'status':'CREATED_NOT_REVIEWED','source':str(src),'source_hash':hashlib.sha256(src.read_bytes()).hexdigest(),'output_hash':hashlib.sha256(dst.read_bytes()).hexdigest(),'changes':changes,'removed_notes':meta,'visual':'NOT_RUN'},ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
