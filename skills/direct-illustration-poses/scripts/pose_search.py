"""Interpretable local retrieval over website text metadata, not image embeddings."""
import re
import unicodedata
import json
from functools import lru_cache
from pathlib import Path

# (query synonyms, source-name patterns). Emotion mappings suggest poses, not facts.
CONCEPTS = {
 '앉기': ('앉|sitting|sit', r'座|座位'),
 '의자': ('의자|걸터|chair', r'椅子|腰掛|チェア'),
 '서기': ('서서|서있는|서있|선채|standing|stand', r'^立ち[・・]|^立って|立ち姿勢|S字立ち'),
 '고민': ('고민|생각|사색|머리복잡|머리가복잡|골똘|멍때|턱괴|뺨괴|난감|thinking', r'頬杖|顎|あご|頬に手|後頭部|髪に手'),
 '턱뺨받침': ('턱괴|턱을괴|뺨괴|뺨을괴|뺨받|턱받|뺨을받|턱을받|chinrest', r'頬杖|顎|あご|頬に手'),
 '피로': ('피곤|지친|지쳐|기운없|기운이없|축처|축늘어|힘이없|탈진|풀이죽|한숨|tired', r'腕をだらり|前かがみ.*膝に手|前屈み.*膝|あくび|片肩を落'),
 '웅크림': ('웅크|몸을말|몸말|구겨|위축|외로운|외로|불안|curl', r'体育座り|三角座り|膝を胸|膝を.*抱|脚を抱'),
 '휴식': ('쉬는|쉬고|쉬기|휴식|편하게|느긋|여유|뒹굴|relax|rest', r'寝|肘.*つ|寄りかか|もたれ|頬杖'),
 '눕기': ('누워|누운|눕|잠든|자는|잠자|sleep|lying', r'寝|仰向け|うつ伏せ'),
 '옆으로눕기': ('옆으로누|옆으로눕|모로누|모로눕', r'横寝|横向き寝|横向きに寝'),
 '엎드리기': ('엎드|배깔|배를깔|prone', r'うつ伏せ'),
 '쪼그리기': ('쪼그|쭈그|쭈구|crouch|squat', r'しゃが|ヤンキー座り'),
 '무릎꿇기': ('무릎꿇|무릎을꿇|정좌|꿇어|kneel', r'膝立|正座|片膝立ち'),
 '한무릎세움': ('한무릎|무릎세|무릎을세', r'片膝立て|片膝を立て'),
 '무릎안기': ('무릎안|무릎을안|무릎끌어|무릎을끌어|두무릎가슴', r'膝を胸|膝を.*抱|膝.*引き寄せ|体育座り'),
 '양반다리': ('양반다리|책상다리|가부좌|명상', r'あぐら'),
 '다리꼬기': ('다리꼬|다리를꼬|다리교차|crossedlegs', r'脚を交差|脚を組|足を組'),
 '다리뻗기': ('다리뻗|다리를뻗|다리펴|다리를펴', r'脚を伸ば|脚前方|脚を斜めに伸ば'),
 '팔짱': ('팔짱|팔교차|팔을교차|armscrossed', r'腕組|腕.*クロス'),
 '허리손': ('손허리|손을허리|허리에손|당당|자신감|거만', r'腰に手|手を腰|両手を腰'),
 '머리손': ('머리긁|머리를긁|뒷머리|머리감싸|머리에손|머쓱|쑥스', r'後頭部|頭の後ろ|髪に手|髪をかき'),
 '팔위로': ('만세|환호|기쁜|기뻐|해냈|승리|양팔위|팔을위|팔머리위|armsup', r'両腕.*上|両手.*頭上|両腕V字|背伸び'),
 '손앞으로': ('손내밀|손을내밀|손뻗|손을뻗|붙잡으|reach', r'腕を前|カメラを指差|手を前|両手を前'),
 '숙이기': ('숙이|숙인|숙여|고개떨|허리굽|몸을굽|구부|bend', r'前かがみ|前屈|前のめり'),
 '뒤기울임': ('뒤로기대|뒤로젖|뒤로기울|가슴펴|가슴을펴', r'反ら|反り|のけぞ|胸を張|仰け反'),
 '옆기울임': ('옆으로기울|옆으로굽|몸옆굽', r'傾|しなら|しなり'),
 '뒤돌기': ('뒤돌|돌아보|돌아본|뒤를보|振り返', r'振り返|振り向|肩越し'),
 '기대기': ('기대|받치|비스듬|recline', r'肘|支え|寄りかか|もたれ'),
 '바닥손': ('바닥짚|바닥을짚|손바닥바닥|바닥에손', r'床.*手|手.*床|前に手をつ|後ろに手をつ|片手をつ'),
 '줍기': ('줍|주워|물건집|떨어진|pick', r'前屈.*床|前かがみ|しゃがみ.*床'),
 '균형': ('균형|한발로|한발서|한쪽발로|외발|balance', r'片足を後ろ|片脚を.*上|つま先立ち|立ちV字|I字'),
 '기지개': ('기지개|스트레칭|뻐근|몸풀|stretch', r'背伸び|両腕を頭上|両腕を上に伸'),
 '포옹': ('포옹|껴안|끌어안|안아주|hug', r'抱き|抱かれ|抱いて|寄り添'),
 '속삭임': ('속삭|귓속말|whisper', r'ささや|耳元'),
 '손하트': ('손하트|하트|heart', r'ハート'),
 '기도': ('기도|합장|부탁|비는|prayer', r'お願い|両手を合わせ'),
 '경례': ('경례|salute', r'敬礼'),
 '손입': ('입가손|입에손|조용히|쉿|하품', r'口元|唇|あくび'),
 '브이': ('브이|브이자|피스|peace', r'ピース'),
 '걷기': ('걷|걸어|산책|떠나는|터벅|walk', r'歩|ウォーク'),
 '달리기': ('달리|달려|질주|뛰어가|도망|run|sprint', r'走|ランニング'),
 '요가': ('요가|yoga', r'ヨガ|テーブルポーズ|猫のポーズ|ブリッジ'),
 '나무자세': ('나무자세|트리포즈|treepose', r'木のポーズ|ツリーポーズ'),
 '휴대폰': ('휴대폰|스마트폰|핸드폰|문자|카톡|phone', r'スマホ|携帯|電話'),
 '검': ('검을|검쥔|칼|sword', r'剣|刀'),
}
INFERRED = {'고민','피로','휴식','웅크림','줍기','균형'}
ANGLE_WORDS = {'front':'정면|앞모습|frontview', 'high':'위에서|내려다|하이앵글|부감|topview',
 'low':'아래에서|올려다|로우앵글|앙각|lowangle', 'side':'측면|옆모습|옆에서|sideview',
 'diag':'사선|비스듬한시점|대각|diagonal'}
FIELDS={'posture','torso','arms','hands','legs','contact','props','action','mood','camera','uncertain','exclude','people'}

@lru_cache(maxsize=1)
def search_resources():
    folder=Path(__file__).resolve().parents[1]/'assets'
    aliases=json.loads((folder/'query-synonyms.json').read_text('utf-8')) if (folder/'query-synonyms.json').is_file() else {}
    index=json.loads((folder/'verified-web-poses.json').read_text('utf-8')) if (folder/'verified-web-poses.json').is_file() else {'poses':[]}
    return aliases,{p['id']:p for p in index['poses']}

def normalize(s):
    return re.sub(r'[^\w가-힣]', '',unicodedata.normalize('NFKC',s).casefold())

def detect(text):
    q=normalize(text)
    aliases,_=search_resources()
    return {k for k,(words,_) in CONCEPTS.items() if any(normalize(w) in q for w in [*words.split('|'),*aliases.get(k,[])])}

def validate_features(value):
    if not isinstance(value,dict) or set(value)-FIELDS:
        raise ValueError('Features must be an object using documented pose fields')
    for k,v in value.items():
        if k=='people':
            if type(v) is not int or v not in [1,2]: raise ValueError('people must be 1 or 2')
        elif not (isinstance(v,str) or isinstance(v,list) and all(isinstance(i,str) for i in v)):
            raise ValueError('Pose feature fields must contain text or lists of text')
    return value

def field_text(features,field):
    v=features.get(field,'')
    return ' '.join(v) if isinstance(v,list) else str(v)

def rank(rows,query,line,angle,limit,describe,lines,angles,features=None,exclude='',details=False):
    features=validate_features(features or {})
    observed=' '.join(field_text(features,k) for k in ['posture','torso','arms','hands','legs','contact','props','action'])
    # Uncertain visual traits are never converted into required query facts.
    text=query+' '+observed+' '+field_text(features,'mood')
    negatives=exclude+' '+field_text(features,'exclude')
    for match in re.finditer(r'(의자|팔짱|엎드린|누운|쪼그린|고민)\s*(?:말고|제외|빼고)',text):
        negatives+=' '+match.group(1); text=text.replace(match.group(0),' ')
    wanted=detect(text); unwanted=detect(negatives)
    camera=normalize(field_text(features,'camera')+' '+query)
    if not angle:
        angle=next((a for a,words in ANGLE_WORDS.items() if any(normalize(w) in camera for w in words.split('|'))),None)
    if not line:
        line='pair' if features.get('people')==2 or re.search(r'두\s*사람|2\s*인|둘이|커플|two people',query) else 'standard'
    terms=[normalize(t) for t in re.findall(r'[\w-]+',text) if len(normalize(t))>=2]
    candidates=[]
    _,verified=search_resources()
    for row in rows:
        if row['系統']!=lines[line] or angle and row['アングル']!=angles[angle]:continue
        label=row['ポーズ名']+' '+row['分類']
        tags={k for k,(_,pattern) in CONCEPTS.items() if re.search(pattern,label)}
        annotation=verified.get(row['id'])
        if annotation:
            # Only this exact web image ID receives visually checked tags.
            tags.update(annotation['concepts'])
            label+=' '+' '.join(annotation['observed_tags'])
        if unwanted & tags:continue
        hits=wanted & tags; missing=wanted-tags
        direct=normalize(row['id']+' '+label)
        literal=sum(min(len(t),10) for t in terms if t in direct)
        if not hits and not literal and normalize(text):continue
        score=sum(5 if k in INFERRED else 8 for k in hits)+5*len(hits)**2+literal
        score-=3*len(missing)
        # Prefer known posture agreement when other semantics tie.
        score+=4*len(detect(observed)&tags)
        item=describe(row) if details else {'id':row['id'],'name':row['ポーズ名'],'angle':row['アングル']}
        item.update(score=score,matched=sorted(hits),missing=sorted(missing),
          scene_inferences=sorted(hits & INFERRED),image_verified=False,
          annotation_level=annotation['review_level'] if annotation else 'website_metadata',
          observed_tags=annotation['observed_tags'] if annotation else [])
        candidates.append((score,row,item))
    candidates.sort(key=lambda x:(-x[0],0 if x[1]['アングル']==angles['front'] else 1,x[1]['id']))
    # One pose per result unless a specific angle was requested; show retrieves URLs.
    result=[]; seen=set()
    for _,row,item in candidates:
        key=(row['系統'],row['ポーズ番号'])
        if key in seen:continue
        seen.add(key);result.append(item)
    return {'query':query,'interpreted':sorted(wanted),'line':line,'angle_filter':angle,
      'matches':len(result),'results':result[:limit],'images_downloaded':0,
      'notice':'Website-name metadata candidates, not visual matches. Missing traits are unconfirmed. Open selected preview and original; use show ID for URLs.'}
