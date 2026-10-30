"""Search AI Pose Gallery metadata; retrieve one selected reference at a time."""
import argparse
import hashlib
import json
import re
import shutil
import struct
import sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

SITE = 'https://ai-pose-gallery.pages.dev/'
DEFAULT_CACHE = Path.home() / '.cache' / 'direct-illustration-poses' / 'gallery.json'
LINES = {'standard': '全身1人・標準系', 'upper': '上半身1人',
         'pair': '2人絡み', 'sexy': '全身1人・セクシー系'}
ANGLES = {'front': '正面', 'high': '上から', 'low': '下から', 'side': '横', 'diag': '斜め'}
# These are search suggestions, not verified descriptions of every pose.
ALIASES = [
    (('앉', 'sitting', 'sit', '의자', 'chair'), ('座', '腰掛', '椅子')),
    (('고민', '생각', '턱', 'thinking', 'worried'), ('頬杖', '顎', '頬に手')),
    (('서서', '서있', 'standing'), ('立ち', '立って')),
    (('눕', '누워', 'lying'), ('寝', '仰向け', 'うつ伏せ')),
    (('무릎', 'kneel'), ('膝',)),
    (('달리', '뛰는', 'running'), ('走',)),
    (('걷', 'walking'), ('歩',)),
    (('검', 'sword'), ('剣',)),
    (('싸움', '격투', 'fight'), ('戦', 'パンチ', '格闘')),
    (('포옹', '껴안', 'hug'), ('抱', 'ハグ')),
    (('손', 'hand'), ('手',)),
]


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


def site_url(relative):
    url = urljoin(SITE, relative)
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.netloc != urlsplit(SITE).netloc:
        raise ValueError('External image URL rejected')
    if parsed.query or parsed.fragment or '..' in parsed.path.split('/'):
        raise ValueError('Unexpected image URL')
    return url


def request_bytes(url, limit):
    req = Request(url, headers={'User-Agent': 'direct-illustration-poses/1.0', 'Accept': '*/*'})
    with urlopen(req, timeout=30) as response:
        # Do not follow a site change to an unrelated host silently.
        site_url(response.url)
        data = response.read(limit + 1)
        if len(data) > limit:
            raise ValueError('Response too large')
        return data


def parse_catalog(html):
    match = re.search(r'\bconst\s+D\s*=\s*(\[.*?\]);', html, re.S)
    if not match:
        raise ValueError('Site catalogue format changed; use the website UI')
    rows = json.loads(match.group(1))  # Never execute site JavaScript.
    if not isinstance(rows, list) or not rows:
        raise ValueError('Empty or invalid catalogue')
    required = ('id', '系統', 'ポーズ番号', '分類', 'ポーズ名', 'アングル', 'サムネ', '原寸')
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or any(not isinstance(row.get(k), str) for k in required):
            raise ValueError('Unexpected catalogue entry')
        if not re.fullmatch(r'[A-Za-z0-9_-]+', row['id']) or row['id'] in seen:
            raise ValueError('Invalid or duplicate image ID')
        seen.add(row['id'])
        for key, prefix, suffix in [('サムネ', 'thumbs/', '.jpg'), ('原寸', 'img/', '.png')]:
            relative = row[key]
            if not re.fullmatch(re.escape(prefix) + r'[A-Za-z0-9_-]+' + re.escape(suffix), relative):
                raise ValueError('Unexpected asset path')
            site_url(relative)
    return rows


def catalogue(cache, refresh=False):
    if cache.is_file() and not refresh:
        stored = json.loads(cache.read_text(encoding='utf-8'))
        if stored.get('source') != SITE:
            raise ValueError('Wrong catalogue source; use --refresh')
        # Apply the same validation to cached metadata.
        return parse_catalog('const D=' + json.dumps(stored['rows']) + ';')
    rows = parse_catalog(request_bytes(SITE, 8_000_000).decode('utf-8'))
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({'source': SITE, 'rows': rows}, ensure_ascii=False), encoding='utf-8')
    return rows


def describe(row):
    return {'id': row['id'], 'name': row['ポーズ名'], 'line': row['系統'],
            'category': row['分類'], 'angle': row['アングル'], 'source_page': SITE,
            'preview_url': site_url(row['サムネ']), 'original_url': site_url(row['原寸'])}


def search_rows(rows, query, line=None, angle=None, limit=6):
    query = query.casefold()
    tokens = re.findall(r'[\w-]+', query)
    expansions = [targets for triggers, targets in ALIASES if any(t in query for t in triggers)]
    results = []
    for row in rows:
        if line and row['系統'] != LINES[line]:
            continue
        if angle and row['アングル'] != ANGLES[angle]:
            continue
        text = ' '.join(row[k] for k in ('id', 'ポーズ名', '分類')).casefold()
        score = sum(5 for token in tokens if token in text)
        score += sum(3 for terms in expansions if any(term in text for term in terms))
        if query and score == 0:
            continue
        results.append(dict(describe(row), score=score))
    results.sort(key=lambda r: (-r['score'], r['id']))
    return {'query': query, 'matches': len(results), 'results': results[:limit],
            'images_downloaded': 0,
            'notice': 'Keyword suggestions only. Open preview and original; verify props and pose visually.'}


def select(rows, image_id):
    found = [row for row in rows if row['id'] == image_id]
    if len(found) != 1:
        raise ValueError('Image ID not found; search current site metadata')
    return found[0]


def image_info(data):
    if data.startswith(b'\x89PNG\r\n\x1a\n') and len(data) >= 24:
        return {'type': 'png', 'width': struct.unpack('>I', data[16:20])[0],
                'height': struct.unpack('>I', data[20:24])[0]}
    if data.startswith(b'\xff\xd8\xff'):
        return {'type': 'jpg'}
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return {'type': 'webp'}
    raise ValueError('Expected an image; HTML or unsupported data rejected')


def download_one(row, kind, out):
    if out.exists():
        raise ValueError('Output exists; refusing overwrite')
    key = '原寸' if kind == 'original' else 'サムネ'
    data = request_bytes(site_url(row[key]), 25_000_000)
    info = image_info(data)
    expected = 'png' if kind == 'original' else 'jpg'
    if info['type'] != expected or out.suffix.lower() != '.' + expected:
        raise ValueError('Unexpected image type or output extension')
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('xb') as handle:
        handle.write(data)
    return dict(describe(row), file=str(out.resolve()), kind=kind,
                sha256=hashlib.sha256(data).hexdigest(), **info,
                redistribution_allowed=False)


def prepare(args):
    source = args.pose_file.expanduser().resolve(strict=True)
    info = image_info(source.read_bytes())
    if info['type'] != 'png':
        raise ValueError('Use the original PNG, not a preview')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.pose_id):
        raise ValueError('Invalid pose ID')
    characters = [p.expanduser().resolve(strict=True) for p in args.character]
    for file in characters:
        image_info(file.read_bytes())
    out = args.out.expanduser().resolve()
    if out.exists():
        raise ValueError('Output exists; choose a new directory')
    out.mkdir(parents=True)
    pose = out / (args.pose_id + '.png')
    shutil.copy2(source, pose)
    copies = []
    for index, file in enumerate(characters, 1):
        ext = image_info(file.read_bytes())['type']
        dest = out / ('character-%02d.' % index + ext)
        shutil.copy2(file, dest)
        copies.append(str(dest))
    prompt = ('장면: ' + args.scene + '\n'
              '캐릭터 기준 이미지는 얼굴·외형·의상·장비를 결정한다. '
              '포즈 ' + args.pose_id + '는 자세·카메라 구도만 결정한다. '
              '포즈 마네킹의 외형은 복제하지 않는다. 작품의 인물 기준 좌우 손·장비 위치를 유지한다. '
              '손가락·관절·소품 접촉·바닥 접지·인원수를 확인한다.\n'
              '작품 제약: ' + (args.constraints or '작품 기준 자료로 확정 필요') + '\n')
    if not copies:
        prompt += '캐릭터 기준 이미지 미제공: 외형·의상·장비 확정 전 생성 대기.\n'
    manifest = {'pose_id': args.pose_id, 'source_page': SITE,
                'pose_file': str(pose), 'character_files': copies,
                'sha256': hashlib.sha256(pose.read_bytes()).hexdigest(),
                'status': 'references_prepared' if copies else 'needs_character_reference',
                'visual_review': 'not_recorded; caller must actually open both reference roles',
                'generation_executed': False, 'redistribution_allowed': False}
    request = {'ready': False, 'requires': ['actual visual review', 'explicit generation request'],
               'arguments': {'prompt': prompt, 'referenced_image_paths': [*copies, str(pose)],
                             'transparent_background': False}}
    for name, value in [('reference-manifest.json', manifest), ('imagegen-request.json', request)]:
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'prompt.txt').write_text(prompt, encoding='utf-8')
    return manifest


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=DEFAULT_CACHE)
    parser.add_argument('--refresh', action='store_true')
    sub = parser.add_subparsers(dest='command', required=True)
    s = sub.add_parser('search', help='Search text metadata; downloads no images')
    s.add_argument('query')
    s.add_argument('--line', choices=LINES)
    s.add_argument('--angle', choices=ANGLES)
    s.add_argument('--limit', type=int, default=6)
    for name in ('show', 'fetch'):
        p = sub.add_parser(name)
        p.add_argument('image_id')
        if name == 'fetch':
            p.add_argument('--kind', choices=('preview', 'original'), required=True)
            p.add_argument('--out', type=Path, required=True)
    p = sub.add_parser('prepare', help='Prepare local references; never generates images')
    p.add_argument('--pose-file', type=Path, required=True)
    p.add_argument('--pose-id', required=True)
    p.add_argument('--character', type=Path, action='append', default=[])
    p.add_argument('--scene', required=True)
    p.add_argument('--constraints', default='')
    p.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            output(prepare(args))
            return
        rows = catalogue(args.cache.expanduser(), args.refresh)
        if args.command == 'search':
            if not 1 <= args.limit <= 30:
                raise ValueError('--limit must be between 1 and 30')
            output(search_rows(rows, args.query, args.line, args.angle, args.limit))
        elif args.command == 'show':
            output(describe(select(rows, args.image_id)))
        else:
            output(download_one(select(rows, args.image_id), args.kind, args.out.expanduser()))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(2, str(error) + '\n')


if __name__ == '__main__':
    main()
