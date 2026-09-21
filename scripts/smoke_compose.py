"""Check local Compose health through both API and web proxy, without secrets."""
import argparse
import json
from urllib.error import HTTPError
from urllib.request import urlopen

parser = argparse.ArgumentParser()
parser.add_argument("--fresh", action="store_true", help="Also check the separate fresh-start stack")
args = parser.parse_args()
for port in ((8001, 5173, 8002, 5174) if args.fresh else (8001, 5173)):
    with urlopen(f'http://127.0.0.1:{port}/health/ready', timeout=5) as response:
        assert response.status == 200
        assert json.load(response) == {'status': 'ready'}
    print(f'PASS loopback:{port} readiness')
try:
    urlopen('http://127.0.0.1:8001/api/debug/stream-smoke', timeout=5)
except HTTPError as error:
    assert error.code == 404
    print('PASS debug route absent in default Compose runtime')
else:
    raise AssertionError('Debug route unexpectedly exposed')
