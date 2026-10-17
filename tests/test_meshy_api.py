import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from movie_production.meshy_api import run

class MeshyResumeTests(unittest.TestCase):
    def test_uncertain_submission_never_posts_again(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);image=root/'reference.png';image.write_bytes(b'test-image')
            with patch('movie_production.meshy_api.call',side_effect=TimeoutError('lost response')) as api:
                with self.assertRaises(TimeoutError):run(image,root, 'fake')
                self.assertEqual(api.call_count,1)
            with patch('movie_production.meshy_api.call') as api:
                with self.assertRaisesRegex(RuntimeError,'Uncertain submission'):run(image,root,'fake')
                api.assert_not_called()

    def test_different_image_rejected_before_call(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);image=root/'reference.png';image.write_bytes(b'new')
            (root/'generation.json').write_text(json.dumps({'image_sha256':'other','tasks':{}}))
            with patch('movie_production.meshy_api.call') as api:
                with self.assertRaises(ValueError):run(image,root,'fake')
                api.assert_not_called()
