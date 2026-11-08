"""Generate a commit message from staged addon package changes."""

from pathlib import Path
import re
import subprocess
import sys


def staged_message(repository):
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=repository, text=True)

    paths = git('diff', '--cached', '--name-only', '-z', '--diff-filter=M',
                '--', ':(glob)addons/**/package.nix').split('\0')
    changes = []
    for path in filter(None, paths):
        before = git('show', f'HEAD:{path}')
        after = git('show', f':{path}')
        name = re.search(r'\bpname = "([^"\n]+)";', after)
        old = re.search(r'\bversion = "([^"\n]+)";', before)
        new = re.search(r'\bversion = "([^"\n]+)";', after)
        if name is None or old is None or new is None:
            raise ValueError(f'Cannot read package name and versions from {path}')
        changes.append((name[1], old[1], new[1]))
    if not changes:
        raise ValueError('No staged addon package updates')

    changes.sort()
    subject = 'addons: update ' + ', '.join(name for name, _, _ in changes)
    if len(subject) > 72:
        subject = f'addons: update {len(changes)} addon releases'
    details = [f'- {name}: {old} -> {new}' if old != new else
               f'- {name}: refresh source pins ({new})'
               for name, old, new in changes]
    return subject + '\n\n' + '\n'.join(details) + '\n'


if __name__ == '__main__':
    try:
        print(staged_message(Path.cwd()), end='')
    except (ValueError, subprocess.CalledProcessError) as error:
        print(f'error: {error}', file=sys.stderr)
        sys.exit(1)
