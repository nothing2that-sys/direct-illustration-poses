"""Prepare actual gallery PNGs and a role-specific fusion request; never generates."""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

SEARCH=Path(__file__).resolve().parents[2]/'direct-illustration-poses/scripts'
sys.path.insert(0,str(SEARCH))
import gallery

ROLES={'base','torso','arms','hands','legs','support','camera'}

def prepare(plan,out,rows):
    if not isinstance(plan,dict):raise ValueError('Plan must be an object')
    if not all(isinstance(plan.get(k),str) and plan[k].strip() for k in ['scene','camera']):
        raise ValueError('scene and camera are required text')
    if type(plan.get('people',1)) is not int or plan.get('people',1) not in [1,2]:
        raise ValueError('people must be 1 or 2')
    if not isinstance(plan.get('constraints',''),str):raise ValueError('constraints must be text')
    refs=plan.get('references')
    if not isinstance(refs,list) or not 2<=len(refs)<=4:raise ValueError('Choose 2 to 4 references')
    checked=[];seen_ids=set();seen_files=set();assigned=set()
    for ref in refs:
        if not isinstance(ref,dict):raise ValueError('Reference must be an object')
        row=gallery.select(rows,ref.get('image_id'))
        if row['id'] in seen_ids:raise ValueError('Duplicate reference ID')
        roles=ref.get('roles')
        if not isinstance(roles,list) or not roles or any(not isinstance(r,str) or r not in ROLES for r in roles):
            raise ValueError('Use supported reference roles')
        if len(set(roles))!=len(roles) or assigned & set(roles):raise ValueError('Assign each role once')
        if not isinstance(ref.get('use'),str) or not ref['use'].strip():raise ValueError('Describe what to use from each image')
        file=Path(ref['file']).expanduser().resolve(strict=True)
        info=gallery.image_info(file.read_bytes())
        if file.suffix.lower()!='.png' or info['type']!='png':raise ValueError('Use original PNG references')
        if file in seen_files:raise ValueError('Duplicate reference file')
        seen_files.add(file);seen_ids.add(row['id']);assigned.update(roles)
        checked.append({'image_id':row['id'],'source_page':gallery.SITE,
          'original_url':gallery.describe(row)['original_url'],'roles':roles,'use':ref['use'],
          'source_file':str(file),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
    if 'base' not in assigned:raise ValueError('Assign exactly one base reference')
    out=Path(out).expanduser().resolve()
    if out.exists():raise ValueError('Output exists; choose a new directory')
    out.mkdir(parents=True)
    files=[]
    for ref in checked:
        dest=out/(ref['image_id']+'.png')
        shutil.copy2(ref['source_file'],dest);ref['file']=str(dest);files.append(str(dest))
    prompt=('Create ONE new coherent pose-reference image, not a collage.\n'
      'Use a neutral faceless grayscale anatomical mannequin with a simple background. '
      'Show the full body and support contacts. Do not transfer character identity, clothing, or style.\n'
      f"People: {plan.get('people',1)}. Camera: {plan['camera']}.\nScene: {plan['scene']}\n")
    for i,ref in enumerate(checked,1):
        prompt+=f"Reference {i}: use ONLY {', '.join(ref['roles'])}: {ref['use']}\n"
    prompt+=('The base determines overall support and balance. Reconcile different input views into the ONE output camera. '
      'Maintain coherent shoulders/elbows/wrists and pelvis/knees/ankles, correct limb count and ground contact. '
      'Do not mirror anatomical left/right without instruction.\nConstraints: '+plan.get('constraints','')+'\n')
    manifest={'schema_version':1,'source_page':gallery.SITE,'stage':'fusion_inputs_prepared',
      'references':checked,'scene':plan['scene'],'camera':plan['camera'],'people':plan.get('people',1),
      'constraints':plan.get('constraints',''),'generated_pose_file':None,
      'visual_review':'not_recorded; caller must open all inputs and generated result',
      'generation_executed':False,'reference_mode':'gallery_inputs_for_synthesis'}
    request={'ready':False,'requires':['actual input review','reference synthesis request'],
      'arguments':{'prompt':prompt,'referenced_image_paths':files,'transparent_background':False}}
    (out/'prompt.txt').write_text(prompt,'utf-8')
    for name,value in [('fusion-manifest.json',manifest),('imagegen-request.json',request)]:
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),'utf-8')
    return manifest

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--plan',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--cache',type=Path,default=gallery.DEFAULT_CACHE)
    args=ap.parse_args()
    try:
        plan=json.loads(args.plan.read_text('utf-8-sig'))
        result=prepare(plan,args.out,gallery.catalogue(args.cache))
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,OSError,KeyError,TypeError) as e:ap.exit(2,str(e)+'\n')

if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    main()
