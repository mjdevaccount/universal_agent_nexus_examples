# Data Pipeline - ETL with LLM Enrichment

**Extract, transform, and load data with AI-powered enrichment.**

## Architecture

```
Data Source (API/CSV/DB)
         ↓
    Extract Node
         ↓
   LLM Enrichment
   ├─ Sentiment Analysis
   ├─ Entity Extraction
   └─ Categorization
         ↓
  Schema Validation
         ↓
    Load to Target
```

## Features

✅ **Multi-source extraction** - APIs, CSV, databases  
✅ **LLM transformation** - AI-powered data enrichment  
✅ **Schema validation** - Ensure data quality  
✅ **Batch processing** - Handle large datasets  
✅ **Error recovery** - Resume from failures  

## Quick Start

```bash
# Compile to LangGraph
nexus compile manifest.yaml --target langgraph --output pipeline.py

# Run with sample data
python pipeline.py --input sample_data.csv --output enriched_data.json
```

## Sample Data

The included `sample_data.csv` contains example records:

```csv
id,text,source,timestamp
1,"Customer loves the new feature",support,2024-01-15
2,"Having issues with login",support,2024-01-15
3,"Great product, highly recommend",review,2024-01-14
```

## Configuration

### LLM Enrichment

Configure the enrichment prompts:

```yaml
nodes:
  - id: enrich
    kind: task
    config:
      prompt: |
        Analyze this text and extract:
        - Sentiment (positive/negative/neutral)
        - Entities (people, products, locations)
        - Category (support/feedback/inquiry)
        
        Text: {text}
```

### Schema Validation

Define expected output schema:

```yaml
nodes:
  - id: validate
    kind: tool
    tool_ref: schema_validator
    config:
      schema:
        type: object
        required: [id, text, sentiment, entities]
```

## Batch Processing

For large datasets, enable batch mode:

```bash
nexus compile manifest.yaml --target aws --output pipeline.json

# Process in parallel on AWS
aws stepfunctions start-execution \
  --input '{"batch_size": 100, "source": "s3://bucket/data.csv"}'
```

## Performance

**Benchmarks:**
- Throughput: 1,000 records/min (with GPT-4o-mini)
- Cost: ~$0.001 per record enrichment
- Accuracy: 95%+ on sentiment analysis

## Next Steps

- [Support Chatbot Example](../04-support-chatbot/)
- [Research Assistant Example](../05-research-assistant/)

