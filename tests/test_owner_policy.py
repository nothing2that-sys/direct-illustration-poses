import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import textwrap
import unittest
from unittest.mock import patch


class OwnerPolicyTests(unittest.TestCase):
    def run_policy(self, login, user_id):
        workflow = (Path(__file__).resolve().parents[1] / '.github/workflows/owner-only-pr.yml').read_text()
        source = textwrap.dedent(workflow.split("python3 - <<'PY'\n", 1)[1].rsplit('\n          PY', 1)[0])
        with tempfile.TemporaryDirectory() as folder:
            event = Path(folder) / 'event.json'
            event.write_text(json.dumps({'pull_request': {
                'user': {'login': login, 'id': user_id},
                'url': 'https://api.github.com/repos/example/repo/pulls/1',
            }}))
            response = io.BytesIO(b'{"state":"closed"}')
            with patch.dict(os.environ, {'GITHUB_EVENT_PATH': str(event), 'GH_TOKEN': 'test-token'}):
                with patch('urllib.request.urlopen', return_value=response) as request:
                    with contextlib.redirect_stdout(io.StringIO()):
                        try:
                            exec(compile(source, '<owner-policy>', 'exec'), {})
                        except SystemExit:
                            pass
                    return request.call_args

    def test_owner_is_allowed_without_mutation(self):
        self.assertIsNone(self.run_policy('nothing2that-sys', 331910699))

    def test_other_accounts_are_closed(self):
        for login, user_id in [('other', 1), ('nothing2that-sys', 1), ('other', 331910699)]:
            with self.subTest(login=login, user_id=user_id):
                call = self.run_policy(login, user_id)
                self.assertIsNotNone(call)
                request = call.args[0]
                self.assertEqual(request.method, 'PATCH')
                self.assertEqual(json.loads(request.data), {'state': 'closed'})
