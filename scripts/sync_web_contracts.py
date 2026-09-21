"""Backend-owned contract copies keep apps/web a self-contained Docker build context."""
import argparse
from hashlib import sha256
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--check', action='store_true')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
target = root / 'apps/web/src/contracts'
if not args.check:
    target.mkdir(parents=True, exist_ok=True)
for source in sorted((root / 'packages/contracts/src').glob('*.ts')):
    content = source.read_text()
    expected = ('// Generated from packages/contracts/src/' + source.name + '; SHA256 '
                + sha256(content.encode()).hexdigest() + '. Do not edit.\n' + content)
    destination = target / source.name
    if args.check:
        if not destination.exists() or destination.read_text() != expected:
            raise SystemExit('Contract copy out of date: ' + str(destination.relative_to(root)))
    else:
        destination.write_text(expected)
print('PASS shared contract copies match' if args.check else 'Synced shared contracts into the web build context')
