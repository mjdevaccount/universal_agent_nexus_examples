# 🚀 Innovation Waves - Technology Adoption Simulator

**Watch technology adoption cascade through business networks. One YAML → 5 Production Runtimes.**

## 🎬 The Demo (45 seconds)

```
[Canvas: 300 blue/green dots = companies, sized by market cap]

1s:  "300 companies. Competing in tech markets."
5s:  [GOD] Drop 'AI Patent' → Yellow shockwave spreads
10s: "Innovators adopt first → Competitive advantage → Market share growth"
15s: [TOGGLE] Same simulation → AWS Bedrock AgentCore
20s: [TOGGLE] LangGraph Platform → Identical dynamics
25s: [GOD] Drop 'Regulation' → Fabric policy blocks monopolies
30s: [TOGGLE] MCP → Claude analyzes market live
35s: "Scale to 1000 companies → Still real-time"
40s: "YOUR stack: One YAML → 5 production runtimes"
```

---

## 💰 100% FREE - Runs Locally with Ollama

No API keys needed. Uses Gemma 2B (2GB) for 1000-agent simulations at 60fps.

---

## 🚀 Quick Start (2 Minutes)

### 1. Install Ollama & Pull Model
```bash
# Install Ollama (if not installed)
curl -fsSL https://ollama.com/install.sh | sh

# Pull Gemma 2B (2GB)
ollama pull gemma:2b-instruct
```

### 2. Start Backend
```bash
cd 07-innovation-waves/backend
pip install -r requirements.txt
python main.py
```

### 3. Open Frontend
```
Open frontend/index.html in your browser
# Or for 5-runtime demo matrix:
Open frontend/demo-matrix.html
```

---

## 🏗️ Architecture

```
Browser Canvas (60fps Market Visualization)
├── 300-1000 Company Agents (market_cap, tech_stack, innovation_score)
├── Market Physics (rich-get-richer + network effects)
├── Patent Particles (spreading innovations)
├── God Controls (patents, subsidies, regulations)
└── 5 Runtime Tabs (live sync)

Backend (FastAPI + WebSocket)
├── Market Simulation Engine
├── Technology Diffusion Model
├── Policy Enforcement
└── Real-time State Broadcasting

SAME Fabric YAML → ALL 5 runtimes
├── Browser (Gemma 2B, 1000 agents)
├── AWS Bedrock AgentCore (serverless)
├── LangGraph Platform (managed)
├── MCP Tool (Claude/Cursor)
└── Local Ollama (edge demo)
```

---

## 🌟 God Mode Controls

| Control | Effect |
|---------|--------|
| 🚀 **AI Patent Drop** | Release new AI technology into market |
| ⚛️ **Quantum Breakthrough** | Drop quantum computing patent |
| 🌱 **Green Tech** | Environmental technology wave |
| ⚖️ **Antitrust Law** | Force divestiture of monopolies (>80% share) |
| 💰 **Innovation Subsidy** | Boost small innovative companies |
| 📈 **Scale to 1000** | Expand to 1000 company agents |

---

## 👥 Company Archetypes

| Type | Adoption Threshold | Strategy |
|------|-------------------|----------|
| **Innovator** | 2% | Early adopter, high risk, disruption |
| **Fast Follower** | 15% | Quick adoption of proven tech |
| **Conservative Corp** | 40% | Late adopter, stability focused |
| **Regulator** | N/A | Policy enforcement, market oversight |

---

## 📊 Market Dynamics

### Rich-Get-Richer
```
Large market cap → More resources → Faster growth
Network effects → Connected to winners → Shared success
```

### Technology Diffusion (S-Curve)
```
1. Innovators adopt (2% threshold)
2. Fast followers see proof (15% threshold)  
3. Conservatives wait for safety (40% threshold)
4. Market saturation
```

### Policy Enforcement
```yaml
governance:
  - name: anti_monopoly
    target_pattern: "acquire_market_share>80%"
    action: deny
    
  - name: innovation_subsidy
    target_pattern: "adopt_new_tech"
    action: allow
    conditions: {company_size: "<1000"}
```

---

## 🎯 Why This Demo

### ✅ Universal Business Language
Everyone understands "tech adoption" and market competition.

### ✅ Your Unique Value
Same YAML → Browser + AWS + LangGraph + MCP + Ollama

### ✅ Scales to 1000
Real market dynamics with 1000 agents at 60fps.

### ✅ Fabric Policies
Block monopolies, enforce regulations across ALL runtimes.

---

## 📁 File Structure

```
07-innovation-waves/
├── innovation_waves.yaml      # Master Fabric spec
├── fabric_archetypes/         # Agent role definitions
│   ├── innovator.yaml
│   ├── conservative_corp.yaml
│   ├── fast_follower.yaml
│   └── regulator.yaml
├── ontology/
│   └── capabilities/          # Market capabilities
├── policy/
│   └── rules/                 # Governance rules
├── backend/
│   ├── main.py               # FastAPI server
│   ├── market_engine.py      # Simulation engine
│   └── requirements.txt
├── frontend/
│   ├── index.html            # Main visualization
│   └── demo-matrix.html      # 5-runtime dashboard
└── runtimes/                  # Target-specific outputs
    ├── browser/
    ├── bedrock/
    ├── langgraph/
    ├── mcp/
    └── ollama-local/
```

---

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/simulation/start` | POST | Start new simulation |
| `/simulation/stop` | POST | Stop simulation |
| `/simulation/state` | GET | Get current state |
| `/god/drop-tech` | POST | Drop new technology |
| `/god/regulation` | POST | Apply regulation |
| `/god/scale` | POST | Scale to N companies |
| `/archetypes` | GET | Get archetype metadata |
| `/ws/market` | WS | Real-time market updates |

---

## 🎬 Demo Script for Presentations

```markdown
1. "300 companies competing in technology markets"
   → Show visualization, explain colors

2. "Watch what happens when AI disrupts the market"
   → Click 'AI Patent Drop'
   → Yellow shockwave, innovators adopt first

3. "But here's the magic - same simulation, 5 runtimes"
   → Open demo-matrix.html
   → Show all 5 panes

4. "Drop another patent - ALL runtimes react simultaneously"
   → Click patent in god mode
   → Highlight sync across panes

5. "And Fabric policies work everywhere"
   → Click 'Antitrust Law'
   → Show monopoly getting broken up

6. "Scale to 1000 companies - still 60fps"
   → Click scale button
   → Show performance

7. "One YAML. Five production deployments. Zero lock-in."
```

---

## 📄 License

MIT License - Part of [Universal Agent Examples](https://github.com/mjdevaccount/universal_agent_nexus_examples)

