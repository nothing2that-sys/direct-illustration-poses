import argparse
import base64
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/direct-illustration-poses/scripts/gallery.py'
spec = importlib.util.spec_from_file_location('gallery', SCRIPT)
gallery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gallery)

# Synthetic fixture, not a downloaded site image or catalogue dump.
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aB9sAAAAASUVORK5CYII=')


def row(image_id='example_P001_front', name='座り・頬杖'):
    return {'id': image_id, '系統': gallery.LINES['standard'], 'ポーズ番号': 'P001',
            '分類': '座り', 'ポーズ名': name, 'アングル': '正面',
            'サムネ': 'thumbs/' + image_id + '.jpg', '原寸': 'img/' + image_id + '.png'}


class GalleryTests(unittest.TestCase):
    def test_gallery_only_scope_and_vocabulary(self):
        from pose_search import CONCEPTS, search_resources
        aliases,_=search_resources()
        self.assertEqual(aliases,{k:v[0].split('|') for k,v in CONCEPTS.items()})
        for name in ['direct-illustration-poses','create-pose-illustration']:
            text=(ROOT/'skills'/name/'SKILL.md').read_text('utf-8')
            self.assertIn('전체 웹 검색이나 다른',text)
            self.assertIn('https://ai-pose-gallery.pages.dev/',text)
    def test_registered_web_tags_are_loaded_by_exact_id(self):
        from pose_search import search_resources
        aliases,index=search_resources()
        self.assertEqual(len(index),6)
        self.assertTrue(aliases)
        p=row('full_single_P012_front','座り・頬杖')
        p['ポーズ番号']='P012'
        r=gallery.search_rows([p], '바닥 짚고 한쪽 다리 뻗기')
        self.assertEqual(r['results'][0]['annotation_level'],'original_observed')
        self.assertIn('바닥손',r['results'][0]['matched'])
        self.assertIn('다리뻗기',r['results'][0]['matched'])
        self.assertFalse(r['results'][0]['image_verified'])
        p['id']='full_single_P012_side'
        r=gallery.search_rows([p],'앉기')
        self.assertEqual(r['results'][0]['observed_tags'],[])

    def test_two_skills_have_distinct_roles_and_share_search(self):
        search=(ROOT/'skills/direct-illustration-poses/SKILL.md').read_text('utf-8')
        create=(ROOT/'skills/create-pose-illustration/SKILL.md').read_text('utf-8')
        self.assertIn('이 검색 스킬은 생성 도구를 직접 호출하지 않는다',search)
        self.assertIn('<검색스킬>/scripts/gallery.py',create)
        self.assertFalse((ROOT/'skills/create-pose-illustration/scripts/gallery.py').exists())
    def test_vague_queries_rank_posture_combinations(self):
        r=gallery.search_rows([row('a_front','前かがみ・腕をだらりと下げる'),row('b_front','座り・頬杖')], '기운 없이 축 처진')
        self.assertEqual(r['results'][0]['id'],'a_front')
        self.assertIn('피로',r['results'][0]['scene_inferences'])
        self.assertFalse(r['results'][0]['image_verified'])
        r=gallery.search_rows([row()], '의자에 앉아서 머리가 복잡한 느낌')
        self.assertIn('의자',r['results'][0]['missing'])
        self.assertIn('고민',r['results'][0]['matched'])

    def test_image_features_exclude_uncertain_traits_and_support_filters(self):
        features={'posture':'앉기','hands':'뺨 괴기','camera':'정면','people':1,'uncertain':['의자'],'exclude':['팔짱']}
        r=gallery.search_rows([row(),row('b_side','腕組み・座り')], '',features=features)
        self.assertEqual(r['angle_filter'],'front')
        self.assertNotIn('의자',r['interpreted'])
        self.assertEqual(len(r['results']),1)
        with self.assertRaises(ValueError): gallery.search_rows([row()], '',features={'people':3})
        with self.assertRaises(ValueError): gallery.search_rows([row()], '',features={'image_path':'not-a-vision-model.png'})

    def test_default_standard_grouping_compact_and_pair_routing(self):
        duplicate=row('same_side');duplicate['アングル']='横'
        adult=row('adult_front');adult['系統']=gallery.LINES['sexy']
        pair=row('pair_front','抱き合う');pair['系統']=gallery.LINES['pair']
        r=gallery.search_rows([row(),duplicate,adult,pair],'앉기')
        self.assertEqual(r['matches'],1)
        self.assertNotIn('original_url',r['results'][0])
        r=gallery.search_rows([pair],'둘이 포옹')
        self.assertEqual(r['line'],'pair')
        self.assertEqual(r['results'][0]['id'],'pair_front')

    def test_parse_site_data_without_executing_javascript(self):
        data = [row()]
        html = '<script>const D=' + json.dumps(data) + ';throw new Error("do not execute");</script>'
        self.assertEqual(gallery.parse_catalog(html), data)
        with self.assertRaises(ValueError):
            gallery.parse_catalog('site structure changed')

    def test_external_urls_and_paths_rejected(self):
        for value in ['https://example.org/a.png', '//example.org/a.png']:
            with self.assertRaises(ValueError):
                gallery.site_url(value)
        bad = row()
        bad['原寸'] = 'img/../../private.png'
        with self.assertRaises(ValueError):
            gallery.parse_catalog('const D=' + json.dumps([bad]) + ';')

    def test_korean_scene_search_does_not_download_images(self):
        with patch.object(gallery, 'request_bytes') as request:
            result = gallery.search_rows([row(), row('example_P002_front', '立ち')], '앉아서 고민', 'standard', 'front')
        request.assert_not_called()
        self.assertEqual(result['results'][0]['id'], 'example_P001_front')
        self.assertEqual(result['images_downloaded'], 0)
        self.assertEqual(gallery.search_rows([row()], 'unknown-zz')['matches'], 0)

    def test_fetch_one_and_preserve_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / 'pose.png'
            with patch.object(gallery, 'request_bytes', return_value=PNG) as request:
                result = gallery.download_one(row(), 'original', target)
                request.assert_called_once_with(gallery.SITE + 'img/example_P001_front.png', 25_000_000)
                self.assertEqual(result['width'], 1)
                with self.assertRaises(ValueError):
                    gallery.download_one(row(), 'original', target)
                self.assertEqual(request.call_count, 1)
            self.assertEqual(target.read_bytes(), PNG)

    def test_html_download_is_not_accepted_as_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / 'pose.png'
            with patch.object(gallery, 'request_bytes', return_value=b'<html>Access denied</html>'):
                with self.assertRaises(ValueError):
                    gallery.download_one(row(), 'original', target)
            self.assertFalse(target.exists())

    def test_prepare_actual_files_and_roles_without_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp = pathlib.Path(tmp)
            pose = temp / 'pose.png'
            character = temp / 'character.png'
            pose.write_bytes(PNG)
            character.write_bytes(PNG)
            args = argparse.Namespace(pose_file=pose, pose_id='example_P001_front', character=[character],
                                      scene='고민하는 장면', constraints='인물 왼손에 장비', out=temp/'prepared')
            result = gallery.prepare(args)
            self.assertFalse(result['generation_executed'])
            request = json.loads((args.out/'imagegen-request.json').read_text(encoding='utf-8'))
            self.assertFalse(request['ready'])
            self.assertEqual(len(request['arguments']['referenced_image_paths']), 2)
            for file in request['arguments']['referenced_image_paths']:
                self.assertTrue(pathlib.Path(file).is_file())
            with self.assertRaises(ValueError):
                gallery.prepare(args)

    def test_install_to_different_folder_and_preserve_user_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            command = [sys.executable, str(ROOT/'install.py'), '--skills-dir', tmp]
            result = subprocess.run(command, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            installed = pathlib.Path(tmp)/'direct-illustration-poses'
            self.assertTrue((installed/'SKILL.md').is_file())
            self.assertTrue((pathlib.Path(tmp)/'create-pose-illustration/SKILL.md').is_file())
            self.assertTrue((pathlib.Path(tmp)/'fuse-pose-references/SKILL.md').is_file())
            custom = installed/'user-note.txt'
            custom.write_text('keep', encoding='utf-8')
            retry = subprocess.run(command, capture_output=True)
            self.assertEqual(retry.returncode, 2)
            self.assertEqual(custom.read_text(encoding='utf-8'), 'keep')

    def test_description_fallback_keeps_only_actual_character_and_uses_no_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp = pathlib.Path(tmp)
            target = temp/'statue.png'
            target.write_bytes(PNG)
            args = argparse.Namespace(pose_file=None, pose_id=None, pose_description='한 발로 서서 두 손을 모은다',
                                      character=[target], scene='청동 동상의 나무 자세', constraints='청동 질감 유지',
                                      fallback_reason='갤러리 조건 불일치', out=temp/'prepared')
            with patch.object(gallery, 'request_bytes') as request:
                result = gallery.prepare(args)
                request.assert_not_called()
            self.assertEqual(result['reference_mode'], 'description_only')
            self.assertIsNone(result['pose_file'])
            self.assertIsNone(result['pose_id'])
            self.assertIsNone(result['source_page'])
            self.assertFalse(result['generation_executed'])
            call = json.loads((args.out/'imagegen-request.json').read_text(encoding='utf-8'))
            paths = call['arguments']['referenced_image_paths']
            self.assertEqual(len(paths), 1)
            self.assertEqual(pathlib.Path(paths[0]).read_bytes(), PNG)
            self.assertIn(args.pose_description, call['arguments']['prompt'])

    def test_description_without_any_images_does_not_invent_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = argparse.Namespace(pose_file=None, pose_id=None, pose_description='나무 자세', character=[],
                                      scene='자세 설명', constraints='', out=pathlib.Path(tmp)/'prepared')
            result = gallery.prepare(args)
            call = json.loads((args.out/'imagegen-request.json').read_text(encoding='utf-8'))
            self.assertNotIn('referenced_image_paths', call['arguments'])
            self.assertEqual(result['status'], 'needs_character_reference')

    def test_external_jpeg_records_actual_source_not_gallery(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp = pathlib.Path(tmp)
            image = temp/'external.jpg'
            image.write_bytes(b'\xff\xd8\xff' + b'synthetic-jpeg-fixture')
            args = argparse.Namespace(pose_file=image, pose_id=None, pose_source='external',
                                      source_url='https://example.org/permitted-pose', rights_note='Test permission fixture',
                                      character=[], scene='앉은 자세', constraints='', out=temp/'prepared')
            with patch.object(gallery, 'request_bytes') as request:
                result = gallery.prepare(args)
                request.assert_not_called()
            self.assertEqual(result['reference_mode'], 'external_image')
            self.assertEqual(result['source_page'], args.source_url)
            self.assertEqual(result['rights_note'], args.rights_note)
            self.assertTrue(result['pose_file'].endswith('.jpg'))
            self.assertIsNone(result['redistribution_allowed'])

    def test_missing_external_permission_and_ambiguous_inputs_preserve_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp = pathlib.Path(tmp)
            image = temp/'pose.png'
            image.write_bytes(PNG)
            args = argparse.Namespace(pose_file=image, pose_id=None, pose_source='external',
                                      character=[], scene='자세', constraints='', out=temp/'prepared')
            with self.assertRaises(ValueError):
                gallery.prepare(args)
            self.assertFalse(args.out.exists())
            args.pose_description = 'both an image and text'
            with self.assertRaises(ValueError):
                gallery.prepare(args)
            self.assertFalse(args.out.exists())

    def test_user_pose_and_description_cli_can_prepare_without_catalogue(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp = pathlib.Path(tmp)
            image = temp/'pose.png'
            image.write_bytes(PNG)
            args = argparse.Namespace(pose_file=image, pose_id=None, pose_source='user',
                                      character=[], scene='사용자 포즈', constraints='', out=temp/'user-pose')
            self.assertEqual(gallery.prepare(args)['reference_mode'], 'user_image')
            command = [sys.executable, str(SCRIPT), '--cache', str(temp/'absent.json'), 'prepare',
                       '--pose-description', '나무 자세', '--character', str(image),
                       '--scene', '동상 자세 편집', '--out', str(temp/'text-pose')]
            result = subprocess.run(command, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((temp/'absent.json').exists())
            manifest = json.loads(result.stdout.decode('utf-8'))
            self.assertEqual(manifest['reference_mode'], 'description_only')


if __name__ == '__main__':
    unittest.main()
