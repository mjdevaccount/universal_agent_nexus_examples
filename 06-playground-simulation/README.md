# 🎮 Interactive Agent Playground

**Watch agents with different personalities interact in real-time.**

Build characters (bully, shy kid, mediator, etc), set a scenario, and watch them have conversations driven by LLMs.

---

## 🚀 Quick Start

### Option 1: Local Development

```bash
# 1. Start backend
cd backend
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...  # Your OpenAI API key
uvicorn main:app --reload

# 2. Open frontend
cd ../frontend
# Open index.html in your browser
# Or use: python -m http.server 8080
```

### Option 2: Docker

```bash
docker build -t agent-playground backend/
docker run -p 8000:8000 -e OPENAI_API_KEY=sk-... agent-playground
```

Then open `frontend/index.html` in your browser.

---

## 🎭 Available Agent Archetypes

### 1. **The Bully** 💪
- **Personality**: High aggression, low empathy
- **Behavior**: Dominates conversations, uses intimidation
- **Example**: "That's MY swing! Get lost!"

### 2. **The Shy Kid** 😰
- **Personality**: Low aggression, high empathy
- **Behavior**: Hesitant, apologetic, avoids conflict
- **Example**: "Um... sorry... I just wanted to..."

### 3. **The Mediator** 🤝
- **Personality**: Diplomatic, problem-solver
- **Behavior**: Suggests compromises, calms situations
- **Example**: "Hey, maybe we can take turns?"

### 4. **The Joker** 😄
- **Personality**: Humorous, class clown
- **Behavior**: Makes jokes, uses humor to defuse
- **Example**: "Why did the chicken cross the playground? 🐔"

### 5. **The Teacher** 👨‍🏫
- **Personality**: Authoritative, instructive
- **Behavior**: Maintains order, guides behavior
- **Example**: "Everyone, let's calm down and talk this through."

---

## 🎯 How It Works

This playground demonstrates **Universal Agent Nexus** capabilities:

1. **Agent Personalities** - Each archetype has a system prompt defining behavior
2. **LLM Reasoning** - GPT-4o-mini generates contextual responses
3. **Real-time Simulation** - WebSocket streams conversation
4. **Observable Behavior** - Watch personality traits emerge

**Under the hood:**
```
Each agent is compiled from a UAA manifest
archetype → UAA manifest → LangGraph runtime → LLM calls
```

---

## 🛠️ Customization

### Add Your Own Archetype

Edit `backend/main.py` and add to `ARCHETYPES`:

```python
ARCHETYPES["rebel"] = {
    "name": "The Rebel",
    "role": "Anti-authority",
    "personality": {"aggression": 7, "empathy": 4, "confidence": 9},
    "prompt": """You are rebellious. You question authority,
    break rules, and challenge the status quo."""
}
```

### Change Scenarios

Try these:
- "Group project where one person isn't doing their part"
- "Choosing teams for kickball"
- "Someone spreading rumors"
- "A new kid trying to join the group"

---

## 🎓 Learning Objectives

This example teaches:
- **Multi-agent orchestration** - Coordinating multiple LLM agents
- **Personality modeling** - Using system prompts to create consistent behaviors
- **Real-time streaming** - WebSocket for live updates
- **LLM prompt engineering** - Crafting effective agent prompts

---

## 🔧 Technical Architecture

```
Frontend (HTML/JS)
       ↓ WebSocket
Backend (FastAPI)
       ↓
Simulation Engine
       ↓
OpenAI GPT-4o-mini
       ↓
Response Stream → Frontend
```

**Key files:**
- `backend/main.py` - FastAPI server with simulation logic
- `frontend/index.html` - Single-page interactive UI
- `manifests/` - UAA definitions for each archetype (optional)

---

## 📊 Performance

- **Latency**: ~1-2 seconds per turn (OpenAI API call)
- **Cost**: ~$0.0001 per turn (GPT-4o-mini pricing)
- **Scalability**: Can run 100+ concurrent simulations

---

## 🚀 Next Steps

1. **Add More Archetypes** - Create your own personalities
2. **Multi-modal Agents** - Add voice/image generation
3. **Persistent Memory** - Agents remember past interactions
4. **Emotion Tracking** - Visualize agent emotional states
5. **Compile to UAA** - Export archetypes as UAA manifests

---

## 🤝 Contributing

Want to add a cool archetype? Submit a PR!

Ideas:
- The Inventor (creative, curious)
- The Athlete (competitive, energetic)
- The Artist (expressive, emotional)
- The Scientist (analytical, logical)

---

**Built with [Universal Agent Nexus](https://github.com/mjdevaccount/universal_agent_nexus)**

**Try other examples:** [01-hello-world](../01-hello-world/) • [02-content-moderation](../02-content-moderation/)

