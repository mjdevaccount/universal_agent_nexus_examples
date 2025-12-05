# 🎮 Interactive Agent Playground

**Watch agents with different personalities interact in real-time.**

## 💰 100% FREE - No API Keys Needed!

This playground runs **completely free** using [Ollama](https://ollama.com) for local LLM inference. No OpenAI. No paid services. Runs offline on your laptop.

---

## 🚀 Quick Start (2 Minutes)

### 1. Install Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: Download from https://ollama.com/download
```

### 2. Pull a Model (4GB)

```bash
ollama pull llama3.2:3b    # Best quality/speed balance
```

### 3. Install Fabric CLI

```bash
pip install fabric
fabric --setup             # Select Ollama
```

### 4. Run the Playground

```bash
cd 06-playground-simulation/backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 5. Open Frontend

Open `frontend/index.html` in your browser.

**Select agents → Click "Run Simulation" → Watch them talk! 🎉**

```
Bully: "This is MY swing! Get lost!"
Shy Kid: "um... okay... sorry..."
Mediator: "Hey, maybe we can take turns?"
Joker: "Why did the swing break up with the slide? Too much drama! 😂"
Teacher: "Everyone gets a turn. Let's be kind."
```

**Zero API costs. Zero vendor lock-in. Runs on any laptop.**

---

## 🏗️ Architecture

```
Universal Agent Fabric (Role Definitions)
    ├─ fabric_archetypes/*.yaml
    ├─ ontology/capabilities/
    ├─ ontology/domains/
    └─ policy/rules/
         ↓
Playground Backend (FastAPI + WebSocket)
         ↓
danielmiessler Fabric CLI
         ↓
Ollama (Local LLM) ← 100% FREE!
```

---

## 📊 Performance (Local Ollama)

| Model | VRAM | Speed | Quality |
|-------|------|-------|---------|
| `llama3.2:1b` | 1GB | 80 t/s | Good for demos |
| `llama3.2:3b` | 2GB | 50 t/s | ✅ **Recommended** |
| `phi3:mini` | 2GB | 60 t/s | Excellent reasoning |
| `gemma2:2b` | 1.5GB | 70 t/s | Runs on Raspberry Pi |

**Response time:** ~1-2 seconds per agent turn

---

## 🎭 Agent Archetypes

| Archetype | Personality | Base Template |
|-----------|-------------|---------------|
| **The Bully** 💪 | Aggressive, dominant | react_loop |
| **The Shy Kid** 😰 | Timid, apologetic | simple_response |
| **The Mediator** 🤝 | Diplomatic, problem-solver | planning_loop |
| **The Joker** 😄 | Humorous, defuses tension | simple_response |
| **The Teacher** 👨‍🏫 | Authoritative, kind | react_loop |

---

## 🔧 Configuration

### Switch Models

```bash
# Faster (lower quality)
fabric --set-default-model llama3.2:1b

# Better quality
fabric --set-default-model llama3.2:3b

# Best reasoning
fabric --set-default-model phi3:mini
```

### Run Offline

```bash
# After initial setup, no internet needed
ollama serve  # Runs locally
```

---

## 📁 Project Structure

```
06-playground-simulation/
├── fabric_archetypes/           # Role definitions (YOUR Fabric)
│   ├── bully.yaml
│   ├── shy_kid.yaml
│   ├── mediator.yaml
│   ├── joker.yaml
│   └── teacher.yaml
├── ontology/
│   ├── capabilities/            # What agents can do
│   └── domains/                 # Capability groupings
├── policy/
│   └── rules/                   # Safety guardrails
├── backend/
│   ├── main.py                  # FastAPI server
│   ├── llm_provider.py          # Ollama/Fabric integration
│   ├── fabric_compiler.py       # FabricBuilder integration
│   └── schemas.py               # Pydantic models
├── frontend/
│   └── index.html               # Interactive UI
└── tests/
    └── test_fabric_integration.py  # 16 passing tests
```

---

## 🛠️ Customization

### Add Your Own Archetype

```yaml
# fabric_archetypes/inventor.yaml
name: "The Inventor"
base_template: "planning_loop"
system_prompt_template: |
  You are creative and curious. Propose novel solutions.
  Think outside the box. Keep responses SHORT.
default_capabilities:
  - "speak"
  - "brainstorm"
```

Then add to `ARCHETYPES` dict in `backend/main.py`.

### Change Scenarios

Try:
- "Group project where one person isn't working"
- "Choosing teams for kickball"
- "A new kid trying to join the group"

---

## 🔄 Fallback Options

The `llm_provider.py` automatically detects available backends:

1. **danielmiessler Fabric CLI** → Uses Ollama (FREE) ✅
2. **Direct OpenAI** → Fallback if Fabric not installed (requires API key)

```python
# From llm_provider.py
if self.fabric_available:
    return await self._complete_with_fabric(...)  # FREE with Ollama
else:
    return await self._complete_with_openai(...)  # Paid fallback
```

---

## 🧪 Run Tests

```bash
cd 06-playground-simulation
pytest tests/ -v  # 16 tests, all passing
```

---

## 📚 More Documentation

- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - How to extend the playground
- [UPSTREAM_GAPS.md](UPSTREAM_GAPS.md) - Library improvement opportunities

---

## 🤝 Contributing

Want to add a cool archetype? Submit a PR!

Ideas:
- The Inventor (creative, curious)
- The Athlete (competitive, energetic)
- The Artist (expressive, emotional)
- The Scientist (analytical, logical)

---

**Built with:**
- [Universal Agent Fabric](https://github.com/mjdevaccount/universal_agent_fabric)
- [danielmiessler Fabric](https://github.com/danielmiessler/fabric)
- [Ollama](https://ollama.com) - **FREE local inference**

**Try other examples:** [01-hello-world](../01-hello-world/) • [02-content-moderation](../02-content-moderation/)
