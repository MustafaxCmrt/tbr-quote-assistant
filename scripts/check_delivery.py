"""Read-only checks for original source integrity and accidental delivery of local data."""

from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parents[1]
baseline = "adc921df1d5f2ad4622b6eac329d13a9fa5c06b1"
source_files = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", baseline, "data/source"], text=True).splitlines()
for name in source_files:
    original = subprocess.check_output(["git", "show", f"{baseline}:{name}"])
    assert (root / name).read_bytes() == original, f"Source changed: {name}"
print(f"PASS original source bytes unchanged: {len(source_files)} files")

files = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard"], text=True).splitlines()
local_env = root / "apps/mobile/.env"
address = re.search(r"http://([^:]+):", local_env.read_text()).group(1) if local_env.exists() else None
for name in set(files):
    path = root / name
    assert path.name not in {"AGENTS.md", "CLAUDE.md", ".env"}, f"Private file stageable: {name}"
    if path.is_file():
        content = path.read_bytes()
        assert not address or address.encode() not in content, f"LAN address outside local env: {name}"
        assert not re.search(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", content), f"Private key: {name}"
        assert not re.search(rb"sk-(?:proj-)?[A-Za-z0-9_-]{32,}", content), f"Possible provider key: {name}"
print("PASS stageable files exclude local instructions, env, actual LAN address and scanned key patterns")
for path in (root / "apps/mobile/dist").rglob("*.hbc"):
    content = path.read_bytes()
    assert not address or address.encode() not in content
    assert not re.search(rb"sk-(?:proj-)?[A-Za-z0-9_-]{32,}", content)
    print("PASS iOS verification bundle uses placeholder address and contains no scanned provider key pattern")
