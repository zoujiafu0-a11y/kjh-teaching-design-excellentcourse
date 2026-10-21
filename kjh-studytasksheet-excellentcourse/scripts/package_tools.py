"""Inspect or narrowly patch editable OOXML text without overwriting an input.
Python 3 + lxml. No rendering or pedagogical pass is implied by structural checks.
"""
import argparse, copy, hashlib, json, re, sys
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as E

W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def parts(z):
    return [n for n in z.namelist() if (re.fullmatch(r'word/(document|header\d+|footer\d+)\.xml',n) or re.fullmatch(r'ppt/(slides/slide|notesSlides/notesSlide)\d+\.xml',n))]
def paragraphs(x): return x.xpath('//*[local-name()="p" and (namespace-uri()=$w or namespace-uri()=$a)]',w=W,a=A)
def text_nodes(p): return p.xpath('.//*[local-name()="t" and (namespace-uri()=$w or namespace-uri()=$a)]',w=W,a=A)
def ptext(p): return ''.join(t.text or '' for t in text_nodes(p))
def stripped(data):
    x=E.fromstring(data)
    for t in x.xpath('//*[local-name()="t" and (namespace-uri()=$w or namespace-uri()=$a)]',w=W,a=A):t.text=''
    return E.tostring(x,method='c14n')
def inspect(path):
    with ZipFile(path) as z:
        bad=z.testzip()
        if bad:raise ValueError('Corrupt ZIP entry: '+bad)
        result={'file':str(Path(path).resolve()),'sha256':digest(path),'paragraphs':[],'visual_check':'NOT_RUN'}
        for n in parts(z):
            for i,p in enumerate(paragraphs(E.fromstring(z.read(n)))):
                if ptext(p):result['paragraphs'].append({'part':n,'index':i,'text':ptext(p)})
        return result
def compare(src,dst):
    with ZipFile(src) as a,ZipFile(dst) as b:
        namesa=set(a.namelist()); namesb=set(b.namelist())
        changed=[n for n in sorted(namesa&namesb) if a.read(n)!=b.read(n)]
        unexpected=[]
        for n in changed:
            if n not in parts(a) or stripped(a.read(n))!=stripped(b.read(n)):unexpected.append(n)
        return {'source_sha256':digest(src),'output_sha256':digest(dst),'changed_parts':changed,'added':sorted(namesb-namesa),'removed':sorted(namesa-namesb),'nontext_changes':unexpected,'text_only_structure_preserved':not(unexpected or namesa!=namesb),'visual_check':'NOT_RUN','content_check':'NOT_RUN'}
def patch(src,dst,changes):
    src=Path(src).resolve();dst=Path(dst).resolve()
    if src==dst or dst.exists():raise ValueError('Output must be a new file, different from source')
    before=digest(src)
    with ZipFile(src) as z:
        data={n:z.read(n) for n in z.namelist()};roots={n:E.fromstring(data[n]) for n in parts(z)}
        changed=set()
        for item in changes:
            old,new=item['old'],item['new'];matches=[]
            if not old or old==new:raise ValueError('Patch must make a nonempty substantive change')
            for n,x in roots.items():
                if item.get('part') and item['part']!=n:continue
                for i,p in enumerate(paragraphs(x)):
                    if item.get('index') is not None and i!=item['index']:continue
                    if ptext(p)==old:matches.append((n,p))
            if len(matches)!=1:raise ValueError(f'Expected unique paragraph, found {len(matches)}: {old[:70]}')
            n,p=matches[0]
            if p.xpath('.//*[local-name()="fldChar" or local-name()="instrText" or local-name()="del" or local-name()="ins" or local-name()="hyperlink"]'):raise ValueError('Complex field/revision/link paragraph requires specialized editing')
            if '\n' in new:raise ValueError('Paragraph patch cannot insert newlines')
            nodes=text_nodes(p);offset=0
            for j,t in enumerate(nodes):
                count=len(t.text or '')
                t.text=new[offset:] if j==len(nodes)-1 else new[offset:offset+count]
                offset+=count
            changed.add(n)
        for n in changed:data[n]=E.tostring(roots[n],xml_declaration=True,encoding='UTF-8',standalone=True)
        dst.parent.mkdir(parents=True,exist_ok=True)
        # Exclusive creation prevents overwrite on races; failed writes remain visible for diagnosis.
        with dst.open('xb') as stream:
            with ZipFile(stream,'w',ZIP_DEFLATED) as out:
                for info in z.infolist():out.writestr(info,data[info.filename])
    if digest(src)!=before:raise RuntimeError('Source changed while patching')
    report=compare(src,dst)
    if not report['text_only_structure_preserved']:raise RuntimeError('Unexpected structural change')
    report['patch_count']=len(changes)
    return report
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
    i=sub.add_parser('inspect');i.add_argument('input');i.add_argument('--report',required=True)
    p=sub.add_parser('patch');p.add_argument('input');p.add_argument('output');p.add_argument('--changes',required=True);p.add_argument('--report',required=True)
    c=sub.add_parser('compare');c.add_argument('input');c.add_argument('output');c.add_argument('--report',required=True)
    args=ap.parse_args(); rp=Path(args.report)
    protected=[Path(args.input).resolve()]
    if hasattr(args,'output'):protected.append(Path(args.output).resolve())
    if rp.resolve() in protected:raise ValueError('Report path cannot overwrite a document')
    if rp.exists():raise ValueError('Use a new report path for each verification')
    rp.parent.mkdir(parents=True,exist_ok=True)
    try:
        if args.cmd=='inspect':result=inspect(args.input)
        elif args.cmd=='patch':result=patch(args.input,args.output,json.loads(Path(args.changes).read_text(encoding='utf-8-sig')))
        else:result=compare(args.input,args.output)
        rp.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({k:v for k,v in result.items() if k!='paragraphs'},ensure_ascii=False))
        if args.cmd=='compare' and not result['text_only_structure_preserved']:return 2
        return 0
    except Exception as exc:
        rp.write_text(json.dumps({'status':'FAIL','error':str(exc),'visual_check':'NOT_RUN'},ensure_ascii=False,indent=2),encoding='utf-8')
        print(str(exc),file=sys.stderr);return 1
if __name__=='__main__':sys.exit(main())
