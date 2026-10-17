import unittest
from pathlib import Path
from movie_production.body import smooth_activity,load_body_profile
from movie_production.catalog import resolve_character
ROOT=Path(__file__).resolve().parents[1]
class BodyTests(unittest.TestCase):
    def test_speaking_fades_at_boundaries(self):
        self.assertEqual(smooth_activity(0,[(0,4)]),0)
        self.assertEqual(smooth_activity(4,[(0,4)]),0)
        self.assertEqual(smooth_activity(2,[(0,4)]),1)
        self.assertGreater(smooth_activity(.1,[(0,4)]),0)
        self.assertLess(smooth_activity(.1,[(0,4)]),1)
        self.assertEqual(smooth_activity(2,[]),0)
    def test_profiles_leave_face_root_and_feet_unmapped(self):
        for name in ('snow','jacob'):
            profile=load_body_profile(ROOT/'movie_production/profiles'/f'{name}-body.json')
            self.assertFalse(set(profile['mapping'])&{'Hips','Head','LeftFoot','RightFoot'})
            self.assertTrue({'LeftArm','RightArm','LeftForeArm','RightForeArm'}<=set(profile['mapping']))
    def test_anatomy_must_be_explicit(self):
        import tempfile,json
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'profile.json';p.write_text(json.dumps({'schema':'body-retarget/1','anatomy':'quadruped','mapping':{'LeftArm':'test'}}))
            with self.assertRaisesRegex(ValueError,'biped'):load_body_profile(p)
    def test_catalog_rejects_untested_motion(self):
        for name in ('snow','jacob'):
            self.assertEqual(resolve_character(name,['talk','listen'])['anatomy'],'biped')
            with self.assertRaisesRegex(ValueError,'not verified'):resolve_character(name,['walk'])
        with self.assertRaisesRegex(ValueError,'registered'):resolve_character('unknown')
