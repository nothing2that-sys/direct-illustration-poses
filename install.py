"""Install the skill for the current user without overwriting an existing skill."""
import argparse
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skills-dir', type=Path, default=Path.home() / '.agents' / 'skills')
    args = parser.parse_args()
    sources = [Path(__file__).resolve().parent / 'skills' / name for name in
               ['direct-illustration-poses','create-pose-illustration','fuse-pose-references']]
    targets = [args.skills_dir.expanduser().resolve() / source.name for source in sources]
    for target in targets:
        if target.exists() or target.is_symlink():
            parser.exit(2, 'Existing skill preserved; back up existing skills before updating: ' + str(target) + '\n')
    installed=[]
    try:
        for source,target in zip(sources,targets):
            shutil.copytree(source,target,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            installed.append(target)
    except OSError:
        # Only newly created destinations from this install may be rolled back.
        for target in installed:
            assert target.parent==args.skills_dir.expanduser().resolve()
            shutil.rmtree(target)
        raise
    for target in targets:print('Installed:',target)
    print('Find: $direct-illustration-poses; Fuse: $fuse-pose-references; Create: $create-pose-illustration')


if __name__ == '__main__':
    main()
