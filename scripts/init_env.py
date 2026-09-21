"""Create local Compose settings without printing credentials or replacing existing values."""
from pathlib import Path
import secrets

path = Path(__file__).resolve().parents[1] / '.env'
if path.exists():
    print('Existing .env preserved. Required keys: POSTGRES_PASSWORD, APP_DB_PASSWORD.')
else:
    path.write_text('POSTGRES_PASSWORD='+secrets.token_hex(24)+'\nAPP_DB_PASSWORD='+secrets.token_hex(24)+'\nAPI_BIND_HOST=127.0.0.1\nAPI_PORT=8001\nDEBUG_STREAM_SMOKE=0\n')
    path.chmod(0o600)
    print('Created ignored .env with generated local credentials. Values not printed.')
