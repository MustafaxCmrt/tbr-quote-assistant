"""Read-only scan of reachable Git history; never print matched credential values.

Checks recognizable key formats, current local secret values and private paths.
This bounded scanner is not a claim to detect every possible secret format.
"""

from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
KEY_PATTERNS = {
    'private-key': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'provider-key': re.compile(rb'sk-(?:proj-)?[A-Za-z0-9_-]{32,}'),
    'github-token': re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{40,})'),
    'aws-access-key': re.compile(rb'(?:AKIA|ASIA)[A-Z0-9]{16}'),
}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def known_local_values():
    values = []
    for path in (ROOT / '.env', ROOT / 'apps/mobile/.env'):
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            name, sep, value = line.partition('=')
            value = value.strip().strip('\"\'')
            if sep and re.search(r'PASSWORD|SECRET|TOKEN|API_KEY', name) and len(value) >= 12:
                values.append(('current-local-secret', value.encode()))
            if name.strip() == 'EXPO_PUBLIC_API_BASE_URL':
                address = re.search(r'https?://([^/:]+)', value)
                if address and address[1] not in {'localhost', '127.0.0.1', 'api.example.invalid'}:
                    values.append(('current-lan-address', address[1].encode()))
    return values


def findings(content, local_values):
    return [name for name, pattern in KEY_PATTERNS.items() if pattern.search(content)] + [
        name for name, value in local_values if value in content
    ]


def scan():
    # Values and findings never include raw matches in stdout/stderr.
    local_values = known_local_values()
    objects = [line.split(b' ', 1)[0] for line in git('rev-list', '--objects', '--all').splitlines()]
    process = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=ROOT,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    failures = []
    counts = {'blob': 0, 'commit': 0, 'tag': 0, 'tree': 0}
    try:
        for oid in objects:
            process.stdin.write(oid + b'\n')
            process.stdin.flush()
            header = process.stdout.readline().split()
            if len(header) != 3:
                raise RuntimeError('Cannot read history object; scan incomplete')
            kind, size = header[1].decode(), int(header[2])
            content = process.stdout.read(size)
            if len(content) != size or process.stdout.read(1) != b'\n':
                raise RuntimeError('Truncated history object; scan incomplete')
            counts[kind] = counts.get(kind, 0) + 1
            if kind in {'blob', 'commit', 'tag'}:
                for rule in findings(content, local_values):
                    failures.append((oid.decode(), rule))
        process.stdin.close()
        if process.wait() != 0:
            raise RuntimeError('git cat-file failed; scan incomplete')
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait()
    # Inspect every committed tree because rev-list paths can alias identical blobs.
    private_paths = set()
    for commit in git('rev-list', '--all').splitlines():
        for name in git('ls-tree', '-r', '--name-only', '-z', commit.decode()).split(b'\0'):
            if not name:
                continue
            leaf = name.rsplit(b'/', 1)[-1]
            if leaf in {b'AGENTS.md', b'CLAUDE.md'} or (
                leaf.startswith(b'.env') and leaf != b'.env.example'
            ):
                private_paths.add(name.decode(errors='replace'))
    print('Scanned reachable Git objects:', counts)
    print('Known local values checked without disclosure:', len(local_values))
    for oid, rule in failures:
        print(f'FAIL object {oid}: {rule} (value suppressed)')
    for name in sorted(private_paths):
        print(f'FAIL private path in history: {name}')
    if failures or private_paths:
        return 1
    print('PASS recognized key patterns, current local secrets/LAN address and private paths absent from reachable history')
    print('Scope excludes unreachable objects, unknown credential formats and remote refs not fetched locally.')
    return 0


if __name__ == '__main__':
    sys.exit(scan())
