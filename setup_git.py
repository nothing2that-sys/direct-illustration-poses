"""Configure this checkout; --auto-clones also configures future clones on this PC."""
import argparse
from pathlib import Path
import subprocess

URLS = [
    'https://github.com/nothing2that-sys/direct-illustration-poses.git',
    'https://github.com/nothing2that-sys/direct-illustration-poses',
    'git@github.com:nothing2that-sys/direct-illustration-poses.git',
    'ssh://git@github.com/nothing2that-sys/direct-illustration-poses.git',
]
ROOT = Path(__file__).resolve().parent
MARKER = '# Managed by direct-illustration-poses/setup_git.py\n'


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, check=True, text=True,
                          capture_output=True, encoding='utf-8').stdout.strip()


def setup(auto_clones=False):
    if git('remote', 'get-url', 'origin') not in URLS:
        raise RuntimeError('Origin is not the supported owner repository; no settings changed.')
    if auto_clones:
        folder = Path.home() / '.config' / 'git' / 'direct-illustration-owner'
        config = folder / 'identity.gitconfig'
        hook = folder / 'hooks' / 'pre-commit'
        if config.exists() and not config.read_text(encoding='utf-8').startswith(MARKER):
            raise RuntimeError('Unrecognized existing config preserved: ' + str(config))
        source_hook = ROOT / '.githooks' / 'pre-commit'
        hook_text = source_hook.read_text(encoding='utf-8')
        if hook.exists() and hook.read_text(encoding='utf-8') != hook_text:
            raise RuntimeError('Existing different hook preserved: ' + str(hook))
        hook.parent.mkdir(parents=True, exist_ok=True)
        hook.write_text(hook_text, encoding='utf-8', newline='\n')
        hook.chmod(0o755)
        # Git's quoted config paths use forward slashes on Windows too.
        hook_path = hook.parent.as_posix().replace('"', '\\"')
        config.write_text(MARKER + '[user]\n\tname = nothing2that-sys\n'
                          '\temail = nothing2that@gmail.com\n'
                          '[credential "https://github.com"]\n\tusername = nothing2that-sys\n'
                          f'[core]\n\thooksPath = "{hook_path}"\n',
                          encoding='utf-8', newline='\n')
        for url in URLS:
            key = f'includeIf.hasconfig:remote.*.url:{url}.path'
            result = subprocess.run(['git', 'config', '--global', '--get-all', key],
                                    text=True, capture_output=True, encoding='utf-8')
            if result.returncode not in (0, 1):
                raise RuntimeError('Unable to read global include settings')
            if config.as_posix() not in result.stdout.splitlines():
                git('config', '--global', '--add', key, config.as_posix())
    for key, value in [('user.name', 'nothing2that-sys'),
                       ('user.email', 'nothing2that@gmail.com'),
                       ('credential.https://github.com.username', 'nothing2that-sys'),
                       ('core.hooksPath', '.githooks')]:
        git('config', '--local', key, value)
    print('Configured this checkout for nothing2that-sys.')
    if auto_clones:
        print('Future clones of this exact repository on this PC now inherit identity and commit guard.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--auto-clones', action='store_true',
                        help='Add repository-URL conditional includes to user Git config (Git 2.36+).')
    setup(parser.parse_args().auto_clones)
