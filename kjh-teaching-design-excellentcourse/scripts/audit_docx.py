"""Read-only structural audit. Human content and final-page checks remain mandatory."""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import argparse,hashlib,json,re,posixpath
from check_intake import review_intake
N={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
PAGE_LOCATOR = re.compile(r'(?:第\s*[0-9０-９一二三四五六七八九十百]+\s*(?:(?:至|到|[-—–~～、，,])\s*[0-9０-９一二三四五六七八九十百]+)*\s*页|[0-9０-９]+\s*(?:(?:至|到|[-—–~～、，,])\s*[0-9０-９]+)*\s*页|(?<![A-Za-z])[PpＰｐ]\.?\s*[0-9０-９]+(?:\s*[-—–~～至到]\s*[0-9０-９]+)?)')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tree(e):
    if e is None:return None
    return (e.tag,sorted(e.attrib.items()),e.text,tuple(tree(c) for c in e))
def package(p):
    with ZipFile(p) as z:
        if z.testzip() is not None:raise ValueError('Bad DOCX ZIP')
        return {n:z.read(n) for n in z.namelist()}

def delivery_review(document,filename,course_type='subject'):
    """Find default-rule issues; context/user overrides still require human review."""
    findings=[]
    for i,p in enumerate(document.findall('.//w:p',N),1):
        text=''.join(p.xpath('.//w:t/text()',namespaces=N))
        patterns={
            'textbook_page_locator':PAGE_LOCATOR,
            'stage_duration_placeholder':r'(?i)中学\s*[/／]\s*小学|小学\s*[/／]\s*中学|x{2,}\s*(?:[-—–~～至到]\s*x{2,})?\s*分钟',
            'teaching_time':r'[（(]\s*\d+(?:\s*(?:至|到|[-—–~～])\s*\d+)?\s*(?:分钟|秒钟|秒)\s*[）)]|(?:授课时长|总时长|用时|耗时)\s*[:：]?\s*\d+|(?:作答|思考|讨论|提问|播放|停顿|本课用|用)\s*(?:约)?\d+\s*(?:分钟|秒钟|秒)',
            'unicode_sup_sub':r'[\u00b2\u00b3\u00b9\u2070-\u209f]',
            'non_chinese_double_quote':r'["＂〝〞]',
        }
        for category,pattern in patterns.items():
            if re.search(pattern,text):findings.append({'category':category,'paragraph':i,'text':text})
    # Locate the textbook row by its label, not by a fixed row number.
    textbook_rows=[]
    for row in document.findall('.//w:tr',N):
        cells=row.findall('w:tc',N)
        if cells and ''.join(cells[0].xpath('.//w:t/text()',namespaces=N)).strip()=='教科书':
            textbook_rows.append(''.join(row.xpath('.//w:t/text()',namespaces=N)))
    if not textbook_rows:
        findings.append({'category':'textbook_block_not_found','text':'需按实际模板人工确认'+'教科书'+'板块'})
    for text in textbook_rows:
        for label,pattern in [('书名',r'书\s*名\s*[:：]'),('出版社',r'出版社\s*[:：]'),('出版日期',r'出版日期\s*[:：]')]:
            if not re.search(pattern,text):findings.append({'category':'textbook_field_missing','field':label,'text':text})
        if re.search(r'(?:内容|页码|授课时长|课时|教学时长|教学范围)\s*[:：]',text):
            findings.append({'category':'textbook_extra_metadata','text':text})
    text=''.join(document.xpath('.//w:t/text()',namespaces=N))
    if text.count('“')!=text.count('”'):
        findings.append({'category':'unbalanced_chinese_quotes','text':'中文双引号数量不配对，须逐处检查'})
    if Path(filename).name!='教学设计.docx':
        findings.append({'category':'default_filename','text':Path(filename).name})
    native=document.findall('.//w:vertAlign',N)
    return {'candidates':findings,'native_superscript_runs':sum(x.get('{'+N['w']+'}val')=='superscript' for x in native),'native_subscript_runs':sum(x.get('{'+N['w']+'}val')=='subscript' for x in native),'not_final_acceptance':True}
def audit(task,docx,template):
    task=Path(task).resolve(strict=True)
    docx=Path(docx).resolve(strict=True);template=Path(template).resolve(strict=True)
    if not docx.is_relative_to(task) or not template.is_relative_to(task):
        raise ValueError('Audit inputs must be inside the task')
    A=package(template);B=package(docx)
    a=E.fromstring(A['word/document.xml']);b=E.fromstring(B['word/document.xml'])
    text='\n'.join(''.join(p.xpath('.//w:t/text()',namespaces=N)) for p in b.findall('.//w:p',N))
    checks={}
    for tag in ['sectPr','tblPr','tblGrid','trPr','tcPr']:
        checks[tag+'_preserved']=[tree(x) for x in a.findall('.//w:'+tag,N)]==[tree(x) for x in b.findall('.//w:'+tag,N)]
    preserve=[n for n in A if n.startswith(('word/header','word/footer')) or n in ['word/styles.xml','word/settings.xml','word/numbering.xml','word/fontTable.xml','word/theme/theme1.xml']]
    checks['preserve_parts_identical']=all(B.get(n)==A[n] for n in preserve)
    prototypes=[tree(x) for x in a.findall('.//w:pPr',N)]
    checks['paragraph_properties_from_template']=all(tree(x) in prototypes for x in b.findall('.//w:pPr',N))
    checks['editable_text_present']=bool(text.strip())
    settings=E.fromstring(B['word/settings.xml'])
    checks['editing_protection_not_enforced']=all(x.get('{'+N['w']+'}enforcement','0') in ('0','false','off') for x in settings.findall('w:documentProtection',N))
    checks['no_replacement_glyph']='\ufffd' not in text
    rels=E.fromstring(B['word/_rels/document.xml.rels'])
    checks['internal_image_targets_exist']=all(posixpath.normpath('word/'+x.get('Target')) in B for x in rels if x.get('Type','').endswith('/image') and x.get('TargetMode')!='External')
    manifest_path=task/'work/manifest.json'
    checks['manifest_exists']=manifest_path.is_file()
    source_checks=[]
    if manifest_path.is_file():
        for m in json.loads(manifest_path.read_text(encoding='utf-8-sig')):
            c=Path(m['copy']);s=Path(m['source'])
            source_checks.append({'copy':str(c),'copy_unchanged':c.is_file() and sha(c)==m['sha256'],'source_available':s.is_file(),'source_unchanged':s.is_file() and sha(s)==m['sha256']})
        checks['input_copies_unchanged']=all(x['copy_unchanged'] for x in source_checks)
        checks['available_originals_unchanged']=all(x['source_unchanged'] for x in source_checks if x['source_available'])
    candidates=[]
    patterns={'dash':r'[—–]','percent':r'\d+(?:\.\d+)?\s*[%％]','stock_word':r'绝大多数|普通人|一般人|令人恐慌|令人震惊|绝望地发现|成倍长|不再套','contrast':r'不是.{0,80}而是','live_activity':r'小组|同桌|巡视|请一组|刚才这位|全班都','placeholder':r'XXX|\[h[123]\]|\[img\]'}
    for i,line in enumerate(text.splitlines(),1):
        for category,pattern in patterns.items():
            if re.search(pattern,line):candidates.append({'paragraph':i,'category':category,'text':line})
    cfgpath=task/'work/intake.json'
    cfg=json.loads(cfgpath.read_text(encoding='utf-8-sig')) if cfgpath.exists() else {}
    timing_review=review_intake(cfg)
    checks['stage_duration_and_timing_ready']=timing_review['timing_ready']
    checks['course_route_ready']=timing_review['course_ready']
    checks['image_source_record_exists']=(task/'work/image_sources.md').is_file()
    delivery_defaults=delivery_review(b,docx,cfg.get('course_type','subject'))
    checks['no_textbook_page_locators']=not any(x['category']=='textbook_page_locator' for x in delivery_defaults['candidates'])
    result={'machine_checks':checks,'machine_checks_pass':all(checks.values()),'not_final_acceptance':True,'docx_sha256':sha(docx),'template_sha256':sha(template),'text_characters':len(text),'source_checks':source_checks,'language_candidates_for_context_review':candidates,'mode':cfg.get('classroom','unknown'),'changed_original_parts':[n for n in A if B.get(n)!=A[n]],'new_parts':sorted(set(B)-set(A)),'manual_required':[('Actual viewing of selected original AI education cases and whole-design tutorial' if cfg.get('course_type')=='ai_education' else 'Actual viewing of eight subject cases'),'Verified textbook edition and facts','Teaching mode and AI scope','Seven language rules and textbook-page locator review in context','Fonts and sizes against user requirements','Open Word and inspect every page of the latest render','Media playback if required']}
    if cfg.get('course_type')=='ai_education':
        result['manual_required'].extend(['AI01-AI16 acceptance with source evidence', 'Separate course content from AI empowerment switch', 'Validate analogies, data provenance, training versus retrieval and actual system capabilities'])
    result['course_type']=cfg.get('course_type','subject')
    result['delivery_defaults_review']=delivery_defaults
    result['intake_timing_review']=timing_review
    result['image_source_review']={'record_exists':checks['image_source_record_exists'],'not_verified_by_machine':True}
    result['manual_required'].extend(['Compare every lesson image with its original textbook page, including headers, footers and floating objects; exclude self-created shapes and AI screenshots', 'Check image_sources.md against the final Word; zero-image lessons need a pedagogical reason', 'Verify notice, school stage and actual timing source; reconcile all timing stages'])
    (task/'work').mkdir(exist_ok=True)
    (task/'work/machine_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--task',required=True);p.add_argument('--docx',required=True);p.add_argument('--template',required=True)
    x=p.parse_args();r=audit(x.task,x.docx,x.template)
    print(json.dumps({'machine_checks_pass':r['machine_checks_pass'],'manual_acceptance_still_required':True,'language_candidate_count':len(r['language_candidates_for_context_review'])},ensure_ascii=False))
    raise SystemExit(0 if r['machine_checks_pass'] else 1)
