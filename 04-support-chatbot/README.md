# Support Chatbot - Multi-Step Customer Support

**Intelligent routing, knowledge base search, and escalation logic.**

## Architecture

```
User Message
      ↓
Intent Classifier (Router)
├─ FAQ → Knowledge Base Search → Response
├─ Technical → Troubleshoot Flow → Resolution/Escalate
├─ Billing → Account Lookup → Handle/Escalate
├─ Complaint → Sentiment Check → Prioritize/Escalate
└─ Other → General Assistant → Response
      ↓
Response Generation
      ↓
User (Loop)
```

## Features

✅ **Intent classification** - Route to appropriate handler  
✅ **Knowledge base retrieval** - Search docs and FAQs  
✅ **Multi-turn conversation** - Maintain context  
✅ **Human agent handoff** - Seamless escalation  
✅ **Sentiment monitoring** - Detect frustrated users  

## Quick Start

```bash
# Compile to LangGraph
nexus compile manifest.yaml --target langgraph --output chatbot.py

# Run interactive session
python chatbot.py --interactive
```

## Configuration

### Intent Categories

Customize intent routing:

```yaml
routers:
  - name: intent_classifier
    strategy: llm
    config:
      intents:
        - faq: "General questions about products/services"
        - technical: "Technical issues, bugs, errors"
        - billing: "Payment, invoices, subscriptions"
        - complaint: "Negative feedback, frustration"
        - other: "Anything else"
```

### Knowledge Base

Connect to your knowledge base:

```yaml
tools:
  - name: knowledge_search
    protocol: http
    config:
      endpoint: "https://your-kb.com/search"
      # Or use vector search
      # endpoint: "https://pinecone.io/query"
```

### Escalation Rules

Define when to escalate to humans:

```yaml
policies:
  - name: escalation_policy
    rules:
      - condition: "sentiment_score < 0.3"
        action: "escalate_immediately"
      - condition: "turn_count > 5"
        action: "offer_human_agent"
      - condition: "topic == 'refund' and amount > 100"
        action: "escalate_to_supervisor"
```

## Multi-Turn Example

```
User: I can't log in to my account
Bot: I'm sorry to hear that. Let me help you troubleshoot.
     What error message are you seeing?

User: It says "Invalid credentials"
Bot: I see. Have you tried resetting your password?
     [Reset Password] [Try Different Browser] [Contact Support]

User: I already tried that
Bot: Let me check your account status...
     I found an issue - your account was locked due to multiple 
     failed attempts. I've unlocked it now. Please try again.

User: It works now, thanks!
Bot: Great! Is there anything else I can help you with?
```

## Deployment

### Local Development

```bash
nexus compile manifest.yaml --target langgraph --output chatbot.py
python chatbot.py --port 8000
```

### Production (AWS)

```bash
nexus compile manifest.yaml --target aws --output state_machine.json
# Deploy with API Gateway for WebSocket support
```

### MCP Integration

```bash
nexus serve manifest.yaml --protocol mcp --transport stdio
# Now available in Claude Desktop, Cursor, etc.
```

## Next Steps

- [Research Assistant Example](../05-research-assistant/)
- [Migration Guide](../migration-guides/langgraph-to-uaa.md)

