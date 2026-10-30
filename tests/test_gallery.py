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
            custom = installed/'user-note.txt'
            custom.write_text('keep', encoding='utf-8')
            retry = subprocess.run(command, capture_output=True)
            self.assertEqual(retry.returncode, 2)
            self.assertEqual(custom.read_text(encoding='utf-8'), 'keep')


if __name__ == '__main__':
    unittest.main()
