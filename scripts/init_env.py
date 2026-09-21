"""Create local Compose settings without printing credentials or replacing existing values."""
from pathlib import Path
import secrets

path = Path(__file__).resolve().parents[1] / '.env'
if path.exists():
    lines = path.read_text().splitlines()
    if not any(line.startswith('ADMIN_API_KEY=') and line.split('=', 1)[1].strip() for line in lines):
        # Older local files predate the admin key; add only the missing value.
        lines = [line for line in lines if not line.startswith('ADMIN_API_KEY=')]
        path.write_text('\n'.join(lines + ['ADMIN_API_KEY=' + secrets.token_hex(24)]) + '\n')
        path.chmod(0o600)
        print('Existing .env preserved; generated missing ADMIN_API_KEY. Values not printed.')
    else:
        print('Existing .env preserved. Required keys: POSTGRES_PASSWORD, APP_DB_PASSWORD, ADMIN_API_KEY.')
else:
    path.write_text('POSTGRES_PASSWORD='+secrets.token_hex(24)+'\nAPP_DB_PASSWORD='+secrets.token_hex(24)+'\nADMIN_API_KEY='+secrets.token_hex(24)+'\nAPI_BIND_HOST=127.0.0.1\nAPI_PORT=8001\nDEBUG_STREAM_SMOKE=0\n')
    path.chmod(0o600)
    print('Created ignored .env with generated local credentials. Values not printed.')
