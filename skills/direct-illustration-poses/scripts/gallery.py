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
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pose_search import rank


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
    req = Request(url, headers={'User-Agent': 'direct-illustration-poses/1.2', 'Accept': '*/*'})
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


def search_rows(rows, query, line=None, angle=None, limit=5, features=None, exclude='', details=False):
    return rank(rows, query, line, angle, limit, describe, LINES, ANGLES, features, exclude, details)


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
    description = (getattr(args, 'pose_description', None) or '').strip()
    if bool(args.pose_file) == bool(description):
        raise ValueError('Choose exactly one pose image or pose description')
    source_kind = getattr(args, 'pose_source', None) or ('gallery' if args.pose_file else 'text')
    if (source_kind == 'text') != bool(description):
        raise ValueError('Text source requires --pose-description; image sources require --pose-file')
    if description and args.pose_id:
        raise ValueError('Description mode has no pose image ID; omit --pose-id')
    source_url = getattr(args, 'source_url', None)
    rights_note = getattr(args, 'rights_note', None)
    if source_kind == 'external' and (not source_url or not rights_note):
        raise ValueError('External images require --source-url and --rights-note')
    if source_url:
        parsed = urlsplit(source_url)
        if parsed.scheme not in ('https', 'http') or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError('Use a public source page URL without credentials')
    if args.pose_id and not re.fullmatch(r'[A-Za-z0-9_-]+', args.pose_id):
        raise ValueError('Invalid pose ID')
    if source_kind == 'gallery' and not args.pose_id:
        raise ValueError('Gallery images require --pose-id')
    source = args.pose_file.expanduser().resolve(strict=True) if args.pose_file else None
    info = image_info(source.read_bytes()) if source else None
    if source_kind == 'gallery' and info['type'] != 'png':
        raise ValueError('Use the original gallery PNG, not a preview')
    characters = [p.expanduser().resolve(strict=True) for p in args.character]
    for file in characters:
        image_info(file.read_bytes())
    out = args.out.expanduser().resolve()
    if out.exists():
        raise ValueError('Output exists; choose a new directory')
    out.mkdir(parents=True)
    pose = out / ((args.pose_id or 'pose-reference') + '.' + info['type']) if source else None
    if pose:
        shutil.copy2(source, pose)
    copies = []
    for index, file in enumerate(characters, 1):
        ext = image_info(file.read_bytes())['type']
        dest = out / ('character-%02d.' % index + ext)
        shutil.copy2(file, dest)
        copies.append(str(dest))
    pose_instruction = ('포즈 참조 이미지는 자세·카메라 구도만 결정하며 외형은 복제하지 않는다. '
                        if pose else '포즈 이미지는 사용하지 않는다. 자세 설명만 적용한다: ' + description + '\n')
    prompt = ('장면: ' + args.scene + '\n'
              '캐릭터 기준 이미지는 얼굴·외형·의상·장비·재질을 결정한다. '
              + pose_instruction + '작품의 인물 기준 좌우 손·장비 위치를 유지한다. '
              '손가락·관절·소품 접촉·바닥 접지·인원수를 확인한다.\n'
              '작품 제약: ' + (args.constraints or '작품 기준 자료로 확정 필요') + '\n')
    if not copies:
        prompt += '캐릭터 기준 이미지 미제공: 특정 외형 유지는 미확정이며 일반 인물은 장면 설명으로 디자인한다.\n'
    manifest = {'pose_id': args.pose_id, 'source_page': SITE if source_kind == 'gallery' else source_url,
                'pose_source': source_kind, 'pose_mode': 'image' if pose else 'description',
                'reference_mode': source_kind + '_image' if pose else 'description_only',
                'pose_description': description or None,
                'pose_file': str(pose) if pose else None, 'character_files': copies,
                'sha256': hashlib.sha256(pose.read_bytes()).hexdigest() if pose else None,
                'rights_note': rights_note,
                'fallback_reason': getattr(args, 'fallback_reason', None),
                'status': 'references_prepared' if copies else 'needs_character_reference',
                'visual_review': ('not_recorded; open actual input images' if pose else
                                  'no pose image used; caller must review any character/edit-target images'),
                'generation_executed': False,
                'redistribution_allowed': False if source_kind == 'gallery' else None}
    references = [*copies, *([str(pose)] if pose else [])]
    arguments = {'prompt': prompt, 'transparent_background': False}
    if references:
        arguments['referenced_image_paths'] = references
    request = {'ready': False, 'requires': ['actual input image review' if references else 'scene and pose review',
                                           'explicit generation request'], 'arguments': arguments}
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
    s.add_argument('query', nargs='?', default='')
    s.add_argument('--line', choices=LINES)
    s.add_argument('--angle', choices=ANGLES)
    s.add_argument('--limit', type=int, default=5)
    s.add_argument('--features', type=Path, help='Observed pose features JSON')
    s.add_argument('--exclude', default='')
    s.add_argument('--details', action='store_true')
    for name in ('show', 'fetch'):
        p = sub.add_parser(name)
        p.add_argument('image_id')
        if name == 'fetch':
            p.add_argument('--kind', choices=('preview', 'original'), required=True)
            p.add_argument('--out', type=Path, required=True)
    p = sub.add_parser('prepare', help='Prepare local references; never generates images')
    pose_input = p.add_mutually_exclusive_group(required=True)
    pose_input.add_argument('--pose-file', type=Path)
    pose_input.add_argument('--pose-description', help='Continue with a written pose; no pose image is used')
    p.add_argument('--pose-id')
    p.add_argument('--pose-source', choices=('gallery', 'external', 'user', 'text'))
    p.add_argument('--source-url', help='Public source page for an alternative pose image')
    p.add_argument('--rights-note', help='Observed permission/license and applicable use, not a new grant')
    p.add_argument('--fallback-reason', help='Why the original gallery was not used')
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
            features = json.loads(args.features.read_text(encoding='utf-8-sig')) if args.features else None
            if not args.query.strip() and not features:
                raise ValueError('Provide query or --features')
            output(search_rows(rows, args.query, args.line, args.angle, args.limit, features, args.exclude, args.details))
        elif args.command == 'show':
            output(describe(select(rows, args.image_id)))
        else:
            output(download_one(select(rows, args.image_id), args.kind, args.out.expanduser()))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(2, str(error) + '\n')


if __name__ == '__main__':
    main()
