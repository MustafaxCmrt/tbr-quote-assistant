"""User-authorized cleanup: only disposable tbr_test_* DBs on test-db."""
import subprocess

base = ['docker', 'compose', '--profile', 'test', 'exec', '-T', 'test-db',
        'psql', '-U', 'tbr_owner', '-d', 'tbr_test', '-v', 'ON_ERROR_STOP=1']

def query(sql):
    return subprocess.check_output([*base, '-tAc', sql], text=True).strip()

selector = "datname LIKE 'tbr\\_test\\_%'"
before = int(query(f'SELECT count(*) FROM pg_database WHERE {selector}'))
preserved = query(f'SELECT datname FROM pg_database WHERE NOT ({selector}) ORDER BY datname')
print('Target service: test-db; literal disposable prefix: tbr_test_', flush=True)
print('Before disposable DB count:', before, flush=True)
print('Preserved DB names:', preserved.splitlines(), flush=True)
commands = query(f"SELECT format('DROP DATABASE %I;', datname) FROM pg_database WHERE {selector} ORDER BY datname")
# Same scoped DROP generation as README; ON_ERROR_STOP prevents hiding partial failures.
subprocess.run([*base, '-q'], input=commands, text=True, check=True)
after = int(query(f'SELECT count(*) FROM pg_database WHERE {selector}'))
assert after == 0, f'Disposable DBs remain: {after}'
assert query(f'SELECT datname FROM pg_database WHERE NOT ({selector}) ORDER BY datname') == preserved
print('After disposable DB count:', after)
print('PASS non-target database list unchanged; db service and volumes never targeted')
