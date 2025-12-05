<div align="center">

# **Universal Agent Examples**

### *Real-world examples for [Universal Agent Nexus](https://github.com/mjdevaccount/universal_agent_nexus)*

**Learn by doing: content moderation, data pipelines, chatbots, research assistants, interactive playground, and migration guides.**

[![Examples](https://img.shields.io/badge/examples-6-blue.svg)](.)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 🎯 **Quick Start**

```bash
# Install Universal Agent Nexus
pip install universal-agent-nexus

# Clone examples
git clone https://github.com/mjdevaccount/universal_agent_nexus_examples.git
cd universal_agent_nexus_examples

# Run an example
cd 01-hello-world
nexus compile manifest.yaml --target langgraph --output agent.py
python agent.py
```

---

## 📚 **Examples**

### **1. Hello World** ([01-hello-world/](01-hello-world/))
**Zero to Production in 10 Minutes**

Your first agent: a simple greeting workflow.

- ✅ Basic graph structure
- ✅ Compile to LangGraph
- ✅ Deploy to AWS
- ✅ Test locally

**Perfect for:** First-time users, quick start

---

### **2. Content Moderation Pipeline** ([02-content-moderation/](02-content-moderation/))
**Production-Grade Content Moderation**

Multi-stage content moderation with AI risk assessment, policy checks, and human escalation.

- ✅ Router-based risk classification
- ✅ Policy validation tools
- ✅ Human review escalation
- ✅ Error handling & retries

**Perfect for:** Social platforms, UGC systems, compliance

---

### **3. Data Pipeline** ([03-data-pipeline/](03-data-pipeline/))
**ETL with LLM Enrichment**

Extract, transform, and load data with AI-powered enrichment.

- ✅ Data extraction from APIs
- ✅ LLM-based transformation
- ✅ Schema validation
- ✅ Batch processing

**Perfect for:** Data engineering, ETL workflows, ML pipelines

---

### **4. Support Chatbot** ([04-support-chatbot/](04-support-chatbot/))
**Multi-Step Customer Support**

Intelligent routing, knowledge base search, and escalation logic.

- ✅ Intent classification
- ✅ Knowledge base retrieval
- ✅ Multi-turn conversation
- ✅ Human agent handoff

**Perfect for:** Customer support, help desks, chatbots

---

### **5. Research Assistant** ([05-research-assistant/](05-research-assistant/))
**Document Analysis & Summarization**

Analyze documents, extract insights, and generate summaries.

- ✅ Document parsing
- ✅ Key point extraction
- ✅ Multi-document synthesis
- ✅ Citation tracking

**Perfect for:** Research, document processing, knowledge management

---

### **6. Interactive Agent Playground** ([06-playground-simulation/](06-playground-simulation/)) 🎮
**Watch Agents Interact in Real-Time**

Build agents with different personalities (bully, shy kid, mediator, joker, teacher) and watch them have conversations.

- ✅ 5 pre-built archetypes with personality traits
- ✅ Real-time conversation simulation
- ✅ Custom scenario support
- ✅ Visual personality bars
- ✅ WebSocket streaming

**Perfect for:** Learning multi-agent systems, LLM prompt engineering, educational demos

**Try it:**
```bash
cd 06-playground-simulation
export OPENAI_API_KEY=sk-...
uvicorn backend/main:app
# Open frontend/index.html
```

---

## 🔄 **Migration Guides**

### **Migrating from LangGraph** ([migration-guides/langgraph-to-uaa.md](migration-guides/langgraph-to-uaa.md))

Step-by-step guide to convert existing LangGraph agents to Universal Agent Architecture.

- Automatic conversion with `nexus translate`
- Manual migration patterns
- Common pitfalls
- Testing strategies

---

### **Migrating from AWS Step Functions** ([migration-guides/aws-to-uaa.md](migration-guides/aws-to-uaa.md))

Convert AWS Step Functions state machines to UAA manifests.

- ASL → UAA conversion
- Lambda function integration
- State management
- Deployment strategies

---

### **Building Custom Optimization Passes** ([migration-guides/custom-optimization-passes.md](migration-guides/custom-optimization-passes.md))

Extend Universal Agent Nexus with your own optimization passes.

- PassManager architecture
- Writing custom transforms
- Testing optimization passes
- Integration with compiler pipeline

---

## 🚀 **Getting Help**

- **Documentation:** [Universal Agent Nexus Docs](https://github.com/mjdevaccount/universal_agent_nexus)
- **Issues:** [Report a bug](https://github.com/mjdevaccount/universal_agent_nexus/issues)
- **Discussions:** [Ask questions](https://github.com/mjdevaccount/universal_agent_nexus/discussions)

---

## 🤝 **Contributing**

Want to add an example? Pull requests welcome!

1. Fork this repository
2. Add your example in a new directory
3. Submit a pull request

---

## 📄 **License**

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with [Universal Agent Nexus](https://github.com/mjdevaccount/universal_agent_nexus)**

⭐ **Star the main project** if these examples help you!

</div>
