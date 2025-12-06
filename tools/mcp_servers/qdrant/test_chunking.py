"""Test Python file chunking."""
from server import chunk_python_file
import json

# Test with a Python file
import sys
from pathlib import Path
base_path = Path(__file__).parent.parent.parent.parent
test_file = str(base_path / "08-local-agent-runtime" / "runtime" / "agent_runtime.py")

print("Testing Python chunking...")
chunks = chunk_python_file(test_file, max_chunk_size=2000)

print(f"\n✅ Created {len(chunks)} chunks:")
for i, chunk in enumerate(chunks[:5], 1):
    print(f"\nChunk {i}:")
    print(f"  Type: {chunk.get('type')}")
    print(f"  Name: {chunk.get('name', 'N/A')}")
    print(f"  Lines: {chunk.get('line_start')}-{chunk.get('line_end')}")
    print(f"  Size: {len(chunk.get('text', ''))} chars")
    print(f"  Preview: {chunk.get('text', '')[:100]}...")

