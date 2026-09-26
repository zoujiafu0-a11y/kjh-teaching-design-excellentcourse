"""Create a fresh task and preserve sources. Does not author or approve a lesson."""
from pathlib import Path
import argparse, hashlib, json, re, shutil
SKILL=Path(__file__).resolve().parents[1]
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def normalize(cfg):
    out=dict(cfg)
    modes={'live':'live','有生':'live','有生课堂':'live','no_students':'no_students','无生':'no_students','无生课堂':'no_students'}
    mode=out.get('classroom','live')
    if mode not in modes:
        raise ValueError('classroom must be live or no_students')
    out['classroom']=modes[mode]
    ai=out.get('ai_enabled',True)
    if type(ai) is not bool:
        raise ValueError('ai_enabled must be a JSON boolean')
    out['ai_enabled']=ai
    style=out.get('ai_style')
    if not ai and style not in (None,'','none'):
        raise ValueError('AI style conflicts with ai_enabled=false')
    out['ai_style']=(style or 'auto') if ai else None
    photos=out.get('textbook_photos',[])
    if not isinstance(photos,list):
        raise ValueError('textbook_photos must be a list')
    out['textbook_policy']='provided_photos' if photos else 'search_revised'
    out['template_policy']='user_template' if out.get('template') else 'bundled_template'
    return out
def initialize(workspace, task, cfg):
    workspace=Path(workspace).resolve(strict=True)
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}',task):
        raise ValueError('Use a lowercase task slug without separators')
    root=(workspace/'output'/task).resolve()
    if not root.is_relative_to(workspace):
        raise ValueError('Task escaped workspace')
    if root.exists():
        raise FileExistsError('Existing task will not be overwritten: '+str(root))
    config=normalize(cfg)
    template=Path(config.get('template') or SKILL/'assets/templates/excellent_course_template.docx').resolve(strict=True)
    sources=[('template',template,'template.docx')]
    for i in range(1,9):
        p=SKILL/'assets/cases'/f'case_{i:02}.png'
        sources.append(('case',p.resolve(strict=True),p.name))
    for role,key in [('textbook','textbook_photos'),('material','materials')]:
        entries=config.get(key,[])
        if not isinstance(entries,list):
            raise ValueError(key+' must be a list')
        for i,s in enumerate(entries,1):
            p=Path(s).resolve(strict=True)
            sources.append((role,p,f'{role}_{i:03}{p.suffix.lower()}'))
    if any(not p.is_file() for _,p,_ in sources):
        raise ValueError('All inputs must be files')
    root.mkdir(parents=True,exist_ok=False)
    for name in ['input','work','final']:
        (root/name).mkdir()
    (root/'input/audio').mkdir()
    manifest=[]
    for role,source,name in sources:
        target=root/'input'/name
        shutil.copy2(source,target)
        assert digest(source)==digest(target)
        manifest.append({'role':role,'source':str(source),'copy':str(target),'sha256':digest(source),'size':source.stat().st_size})
    (root/'work/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (root/'work/intake.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
    (root/'work/progress.md').write_text('# Progress\n\nInput copies prepared. Actual source/case viewing, writing, Word authoring and all acceptance checks are pending. No system goal has been registered by this script.\n',encoding='utf-8')
    return root
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--workspace',required=True);p.add_argument('--task',required=True);p.add_argument('--config',required=True)
    a=p.parse_args()
    cfg=json.loads(Path(a.config).read_text(encoding='utf-8-sig'))
    print(initialize(a.workspace,a.task,cfg))
