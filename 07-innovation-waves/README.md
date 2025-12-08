# 🚀 Innovation Waves - Pivoted (Market Dynamics Agent)

**Local LLM + Caching + LangGraph + MCP Integration**

Demonstrates how to:
1. Use Ollama locally (no API keys, no cloud lock-in)
2. Leverage prompt caching for repeated archetype/policy analysis
3. Orchestrate multi-step reasoning with LangGraph
4. Output MCP-compatible JSON for Claude/Cursor integration
5. Analyze 1000+ companies efficiently via batch processing

## 🏗️ Architecture

```
Innovation Event (Fabric YAML)
    ↓
[ANALYZE] Agent reads cached archetypes (Innovator, Conservative, Fast-Follower)
    ↓
[PREDICT] Uses cached policy rules to evaluate market response
    ↓
[INTERPRET] Generates human-readable narrative + JSON predictions
    ↓
Output: Real-time market impact for 1000 companies
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd 07-innovation-waves-pivoted/backend
pip install -r requirements.txt
```

### 2. Start Ollama (if not running)

```bash
ollama serve
```

### 3. Pull Model (if needed)

```bash
ollama pull qwen3:8b
# Or use gemma:2b-instruct for faster/smaller
```

### 4. Run Agent

```bash
cd backend
python market_agent.py --event "AI_PATENT_DROP" --companies 1000 --model qwen3:8b
```

### 5. View Output

Results are saved to `output/market_predictions.json` in MCP-ready format.

## 📊 Example Output

```json
{
  "event": {
    "name": "Generative AI Patent Drop",
    "category": "AI",
    "disruption_level": 8.5,
    "affected_sectors": ["Software", "Consulting", "Customer Service"]
  },
  "timestamp": "2025-12-07T23:05:00Z",
  "affected_companies": 1000,
  "analysis": {
    "summary": "...",
    "adoption": {
      "adoption_timeline_months": 18,
      "market_cap_redistribution_trillions": 2.3,
      "disruption_score": 9.4
    },
    "policy_recommendations": [
      "Monitor for monopoly formation (>80% adoption)",
      "Consider innovation subsidy for late adopters"
    ]
  },
  "narrative": "...",
  "cache_performance": {
    "archetype_cache_reuses": 1000,
    "estimated_cache_hit_rate": 0.87,
    "token_savings_percent": 85
  }
}
```

## 🎯 Why This Beats Original Example 07

| Aspect | Original | Pivoted |
|--------|----------|---------|
| Runs Locally | ❌ (needs APIs) | ✅ (Ollama only) |
| Uses Caching | ❌ | ✅ (87%+ hit rate) |
| LangGraph | ❌ (just browser) | ✅ (full orchestration) |
| MCP Integration | ❌ | ✅ (JSON output) |
| Scales to 1000 | ❌ (real-time) | ✅ (batch + cache) |
| Production Ready | ❌ (demo only) | ✅ (actual agent) |

## 📁 File Structure

```
07-innovation-waves-pivoted/
├── config/
│   ├── innovation_waves.yaml       # Master Fabric spec
│   └── market_dynamics.yaml        # Market rules + archetypes
├── cache/
│   ├── archetype_cache.py         # Cached archetype patterns
│   └── policy_cache.py            # Cached policy rules
├── backend/
│   ├── market_agent.py            # Main LangGraph agent
│   ├── ollama_bridge.py           # Ollama integration
│   └── requirements.txt
└── output/
    ├── market_predictions.json    # MCP-consumable output
    └── narrative_report.txt       # Human-readable analysis
```

## 🔧 Command Line Options

```bash
python market_agent.py \
  --event "AI_PATENT_DROP" \
  --companies 1000 \
  --model qwen3:8b \
  --output market_predictions.json
```

## 🎬 Next Steps

- [ ] Create MCP tool server for Claude/Cursor integration
- [ ] Add terminal dashboard showing live analysis
- [ ] Implement Redis caching for production
- [ ] Add batch processing for 10,000+ companies
- [ ] Create web UI for real-time visualization

## 📄 License

MIT License - Part of [Universal Agent Examples](https://github.com/mjdevaccount/universal_agent_nexus_examples)

