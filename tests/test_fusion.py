import copy
import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from test_gallery import PNG,row
spec=importlib.util.spec_from_file_location('fusion',ROOT/'skills/fuse-pose-references/scripts/prepare_fusion.py')
fusion=importlib.util.module_from_spec(spec);spec.loader.exec_module(fusion)

class FusionTests(unittest.TestCase):
    def make_plan(self,tmp):
        a=tmp/'a.png';b=tmp/'b.png';a.write_bytes(PNG);b.write_bytes(PNG)
        return {'scene':'앉아서 턱을 괴는 새 자세','camera':'정면','people':1,
          'references':[{'image_id':'a_front','file':str(a),'roles':['base','legs'],'use':'다리와 지지점'},
                        {'image_id':'b_front','file':str(b),'roles':['arms','hands'],'use':'턱을 괴는 손'}]}
    def test_prepare_real_files_and_separate_part_roles(self):
        with tempfile.TemporaryDirectory() as d:
            tmp=pathlib.Path(d);plan=self.make_plan(tmp)
            result=fusion.prepare(plan,tmp/'out',[row('a_front'),row('b_front')])
            request=json.loads((tmp/'out/imagegen-request.json').read_text('utf-8'))
            self.assertFalse(result['generation_executed']);self.assertIsNone(result['generated_pose_file'])
            self.assertEqual(len(request['arguments']['referenced_image_paths']),2)
            self.assertTrue(all(pathlib.Path(p).read_bytes()==PNG for p in request['arguments']['referenced_image_paths']))
            self.assertIn('base, legs',request['arguments']['prompt'])
            self.assertIn('arms, hands',request['arguments']['prompt'])
            self.assertIn('not a collage',request['arguments']['prompt'])
            with self.assertRaises(ValueError):fusion.prepare(plan,tmp/'out',[row('a_front'),row('b_front')])
    def test_ambiguous_roles_and_missing_base_do_not_create_output(self):
        with tempfile.TemporaryDirectory() as d:
            tmp=pathlib.Path(d);plan=self.make_plan(tmp);rows=[row('a_front'),row('b_front')]
            bad=copy.deepcopy(plan);bad['references'][1]['roles']=['legs']
            with self.assertRaises(ValueError):fusion.prepare(bad,tmp/'out',rows)
            self.assertFalse((tmp/'out').exists())
            bad=copy.deepcopy(plan);bad['references'][0]['roles']=['legs']
            with self.assertRaises(ValueError):fusion.prepare(bad,tmp/'out',rows)
            self.assertFalse((tmp/'out').exists())
    def test_unknown_source_missing_file_and_duplicate_input_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            tmp=pathlib.Path(d);plan=self.make_plan(tmp);rows=[row('a_front'),row('b_front')]
            for change in ['unknown','missing','duplicate']:
                bad=copy.deepcopy(plan)
                if change=='unknown':bad['references'][1]['image_id']='not-in-gallery'
                if change=='missing':bad['references'][1]['file']=str(tmp/'missing.png')
                if change=='duplicate':bad['references'][1]['file']=bad['references'][0]['file']
                with self.assertRaises((ValueError,OSError)):fusion.prepare(bad,tmp/'out',rows)
                self.assertFalse((tmp/'out').exists())
    def test_single_reference_is_not_fusion(self):
        with tempfile.TemporaryDirectory() as d:
            tmp=pathlib.Path(d);plan=self.make_plan(tmp);plan['references']=plan['references'][:1]
            with self.assertRaises(ValueError):fusion.prepare(plan,tmp/'out',[row('a_front')])
            self.assertFalse((tmp/'out').exists())
