"""Quick stats check."""
import json
from pathlib import Path

state = json.load(open('sync_state.json'))

for repo, data in state['repos'].items():
    files = data.get('files', {})
    
    by_ext = {}
    for f in files:
        ext = Path(f).suffix or 'no_ext'
        by_ext[ext] = by_ext.get(ext, 0) + 1
    
    total_chunks = sum(f['chunks'] for f in files.values())
    
    print(f"\n📦 {repo}")
    print(f"   Files by type:")
    for ext, count in sorted(by_ext.items()):
        print(f"      {ext}: {count}")
    print(f"   Total files: {len(files)}")
    print(f"   Total chunks: {total_chunks}")

