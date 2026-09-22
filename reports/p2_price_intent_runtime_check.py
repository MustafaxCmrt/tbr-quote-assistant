"""Read-only demo preservation and deployed Python code verification; never POSTs."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import urllib.request

root = Path(__file__).resolve().parents[1]
state = root / '.git/p2-demo-before.json'
mobile = re.search(r'EXPO_PUBLIC_API_BASE_URL=(.+)', (root / 'apps/mobile/.env').read_text())
if not mobile:
    raise SystemExit('Mobile API setting not found; no network request made')
bases = ['http://localhost:8001', 'http://localhost:5173', mobile[1].strip().strip('\"\'')]
ids = [q['quote_id'] for q in json.loads((root / 'data/source/quotes.json').read_text())]
snapshots = []
for base in bases:
    snapshots.append({qid: json.load(urllib.request.urlopen(base.rstrip('/') + '/api/quotes/' + qid, timeout=10)) for qid in ids})
assert snapshots[0] == snapshots[1] == snapshots[2], 'API/web/mobile DTO mismatch'
print(f'PASS {len(ids)} quote DTOs equal across direct API, web proxy, configured mobile API')
if sys.argv[1] == 'before':
    state.write_text(json.dumps(snapshots[0], ensure_ascii=False))
    state.chmod(0o600)
    print('Saved private before snapshot; GET requests only')
else:
    assert snapshots[0] == json.loads(state.read_text()), 'Demo quote changed during rebuild'
    print('PASS all quote DTOs unchanged after rebuild, including Q-1001/Q-1004')
    code = 'import pathlib,hashlib,json; print(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path("app").rglob("*.py")}))'
    live = json.loads(subprocess.check_output(['docker','compose','exec','-T','api','python','-c',code],text=True))
    local = {str(p.relative_to(root / 'apps/api')): hashlib.sha256(p.read_bytes()).hexdigest() for p in (root / 'apps/api/app').rglob('*.py')}
    assert live == local, 'Runtime Python code differs from checkout'
    print(f'PASS all {len(local)} API Python file hashes equal checkout')
    print('normalization.py SHA256:', local['app/services/normalization.py'])
print(subprocess.check_output(['sysctl','vm.swapusage'],text=True).strip())
