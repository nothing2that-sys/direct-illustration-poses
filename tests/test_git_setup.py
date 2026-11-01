import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class GitSetupTests(unittest.TestCase):
    def test_future_clone_inherits_guard_and_unrelated_repo_is_unchanged(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            profile = folder / 'profile'
            profile.mkdir()
            env = {key: value for key, value in os.environ.items()
                   if not key.startswith(('GIT_', 'HOMEDRIVE', 'HOMEPATH'))}
            env.update(HOME=str(profile), USERPROFILE=str(profile),
                       GIT_CONFIG_GLOBAL=str(profile / '.gitconfig'),
                       GIT_CONFIG_NOSYSTEM='1', PYTHONUTF8='1')

            def run(*args, cwd=folder, check=True, extra=None):
                return subprocess.run(args, cwd=cwd, env=env | (extra or {}), text=True,
                                      capture_output=True, check=check, encoding='utf-8')

            source = folder / 'source'
            run('git', 'init', '--template=', str(source))
            run('git', 'config', '--global', 'user.name', 'Other Name')
            run('git', 'config', '--global', 'user.email', 'other@example.invalid')
            url = 'https://github.com/nothing2that-sys/direct-illustration-poses.git'
            run('git', 'remote', 'add', 'origin', url, cwd=source)
            shutil.copy2(root / 'setup_git.py', source)
            (source / '.githooks').mkdir()
            shutil.copy2(root / '.githooks/pre-commit', source / '.githooks/pre-commit')
            for _ in range(2):
                run(sys.executable, 'setup_git.py', '--auto-clones', cwd=source)
            config = (profile / '.gitconfig').read_text()
            self.assertEqual(config.count('[includeIf '), 4)
            run('git', 'add', '.', cwd=source)
            run('git', 'commit', '-m', 'owner', cwd=source)
            clone = folder / 'fresh'
            run('git', '-c', f'url.{source.as_posix()}.insteadOf={url}',
                'clone', url, str(clone))
            self.assertEqual(run('git', 'config', 'user.name', cwd=clone).stdout.strip(), 'nothing2that-sys')
            self.assertEqual(run('git', 'config', 'user.email', cwd=clone).stdout.strip(), 'nothing2that@gmail.com')
            self.assertTrue(Path(run('git', 'config', 'core.hooksPath', cwd=clone).stdout.strip()).is_dir())
            blocked = run('git', 'commit', '--allow-empty', '-m', 'wrong', cwd=clone,
                          check=False, extra={'GIT_AUTHOR_NAME': 'Other Name'})
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn('Commit blocked:', blocked.stderr)
            run('git', 'commit', '--allow-empty', '-m', 'owner', cwd=clone)
            unrelated = folder / 'unrelated'
            run('git', 'init', '--template=', str(unrelated))
            run('git', 'remote', 'add', 'origin', 'https://github.com/other/repository.git', cwd=unrelated)
            self.assertEqual(run('git', 'config', 'user.name', cwd=unrelated).stdout.strip(), 'Other Name')
            self.assertEqual(run('git', 'config', 'core.hooksPath', cwd=unrelated, check=False).returncode, 1)
