"""Install the skill for the current user without overwriting an existing skill."""
import argparse
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skills-dir', type=Path, default=Path.home() / '.agents' / 'skills')
    args = parser.parse_args()
    source = Path(__file__).resolve().parent / 'skills' / 'direct-illustration-poses'
    target = args.skills_dir.expanduser().resolve() / source.name
    if target.exists() or target.is_symlink():
        parser.exit(2, 'Existing skill preserved; choose another --skills-dir or back it up manually: ' + str(target) + '\n')
    shutil.copytree(source, target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    print('Installed:', target)
    print('Invoke: $direct-illustration-poses')


if __name__ == '__main__':
    main()
