# 🎮 Interactive Agent Playground

**Watch agents with different personalities interact in real-time.**

Uses [Universal Agent Fabric](https://github.com/mjdevaccount/universal_agent_fabric) for role composition + [danielmiessler Fabric](https://github.com/danielmiessler/fabric) for LLM provider abstraction.

---

## 🏗️ **Architecture**

```
Universal Agent Nexus (Compiler)
         ↓
Universal Agent Fabric (Composition - YOUR CONNECTOR!)
    ├─ Roles (archetypes)
    ├─ Domains (capabilities)
    └─ Policies (governance)
         ↓
Runtime (Kernel)
         ↓
danielmiessler Fabric (LLM Abstraction)
         ↓
Providers (OpenAI, Ollama, Anthropic...)
```

**Two Fabrics, One System:**
1. **YOUR Fabric** - Defines agent roles, capabilities, governance
2. **danielmiessler Fabric** - Handles LLM provider abstraction

---

## 🚀 Quick Start

### 1. Install danielmiessler Fabric (Optional - for multi-provider support)

```bash
curl -fsSL https://raw.githubusercontent.com/danielmiessler/fabric/main/scripts/installer/install.sh | bash
fabric --setup
```

### 2. Install YOUR Universal Agent Fabric

```bash
pip install universal-agent-fabric
```

### 3. Start Playground

```bash
cd backend
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...  # If not using danielmiessler Fabric
uvicorn main:app --reload
```

### 4. Open Frontend

```bash
cd ../frontend
# Open index.html in browser
# Or: python -m http.server 8080
```

---

## 🎭 **Agent Archetypes (YOUR Fabric)**

Archetypes are defined in `fabric_archetypes/*.yaml`:

```yaml
# fabric_archetypes/bully.yaml
name: "Playground Bully"
base_template: "react_loop"
system_prompt_template: |
  You are a playground bully...
default_capabilities:
  - "speak"
```

### Available Archetypes

| Archetype | Role | Base Template | Capabilities |
|-----------|------|---------------|--------------|
| **bully** | Dominant, aggressive | react_loop | speak |
| **shy_kid** | Timid, anxious | simple_response | speak |
| **mediator** | Diplomatic, problem-solver | planning_loop | speak, analyze_situation |
| **joker** | Humorous, class clown | simple_response | speak |
| **teacher** | Authoritative, instructive | react_loop | speak, observe_situation |

### Create New Archetypes

```bash
# Copy existing
cp fabric_archetypes/bully.yaml fabric_archetypes/inventor.yaml

# Edit system_prompt_template
```

---

## 🔧 **LLM Provider Configuration**

### Option A: danielmiessler Fabric (Recommended)

Configure once, use everywhere:

```bash
# OpenAI (default)
fabric --setup  # Select OpenAI

# Ollama (local, free)
fabric --setup  # Select Ollama

# Anthropic
fabric --setup  # Select Anthropic
```

Check current config:
```bash
fabric --listmodels
curl http://localhost:8000/health
```

### Option B: Direct OpenAI (Fallback)

If danielmiessler Fabric is not installed, the playground automatically falls back to direct OpenAI API calls:

```bash
export OPENAI_API_KEY=sk-...
uvicorn main:app --reload
```

---

## 🎯 **Why Two Fabrics?**

| Fabric | Purpose | Your Benefit |
|--------|---------|--------------|
| **YOUR Universal Agent Fabric** | Agent composition, roles, governance | DRY agent definitions, policy enforcement |
| **danielmiessler Fabric** | LLM provider abstraction | 100+ providers, zero vendor lock-in |

**Together:** Composable agents + flexible LLM backends

---

## 📁 **Project Structure**

```
06-playground-simulation/
├── README.md
├── fabric_archetypes/           # YOUR Fabric role definitions
│   ├── bully.yaml
│   ├── shy_kid.yaml
│   ├── mediator.yaml
│   ├── joker.yaml
│   └── teacher.yaml
├── backend/
│   ├── main.py                  # FastAPI server
│   ├── llm_provider.py          # Fabric integration
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/
    └── index.html               # Interactive UI
```

---

## 🎓 Learning Objectives

This example teaches:
- **Multi-agent orchestration** - Coordinating multiple LLM agents
- **Role composition** - Using YOUR Fabric for agent definitions
- **Provider abstraction** - Using danielmiessler Fabric for LLM calls
- **Real-time streaming** - WebSocket for live updates

---

## 📊 Performance

- **Latency**: ~1-2 seconds per turn (LLM API call)
- **Cost**: ~$0.0001 per turn (GPT-4o-mini pricing)
- **Scalability**: Can run 100+ concurrent simulations

---

## 🚀 Next Steps

1. **Add More Archetypes** - Create your own in `fabric_archetypes/`
2. **Switch Providers** - Use Ollama for free local inference
3. **Add Capabilities** - Extend archetypes with new tools
4. **Compile to UAA** - Export archetypes as UAA manifests

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
- [Universal Agent Nexus](https://github.com/mjdevaccount/universal_agent_nexus)

**Try other examples:** [01-hello-world](../01-hello-world/) • [02-content-moderation](../02-content-moderation/)
