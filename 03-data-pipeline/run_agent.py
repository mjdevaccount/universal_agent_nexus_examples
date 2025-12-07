"""Run the data pipeline agent using LangGraphRuntime with v3.0.1 patterns."""

import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_core.messages import HumanMessage
from universal_agent_nexus.compiler import parse
from universal_agent_nexus.ir.pass_manager import create_default_pass_manager, OptimizationLevel
from universal_agent_nexus.adapters.langgraph import LangGraphRuntime
from universal_agent_tools.observability_helper import setup_observability, trace_runtime_execution


async def main():
    # Setup observability
    obs_enabled = setup_observability("data-pipeline")
    
    # Use proper Nexus compiler pipeline: parse → optimize → execute
    print("📦 Parsing manifest.yaml...")
    ir = parse("manifest.yaml")
    
    print("⚡ Running optimization passes...")
    manager = create_default_pass_manager(OptimizationLevel.DEFAULT)
    ir_optimized = manager.run(ir)
    
    # Log optimization stats
    stats = manager.get_statistics()
    if stats:
        total_time = sum(s.elapsed_ms for s in stats.values())
        print(f"✅ Applied {len(stats)} passes in {total_time:.2f}ms")
    
    runtime = LangGraphRuntime(
        postgres_url=None,
        enable_checkpointing=False,
    )
    await runtime.initialize(ir_optimized, graph_name="etl_pipeline")

    # Load sample data
    sample_data_path = Path(__file__).parent / "sample_data.csv"
    if sample_data_path.exists():
        # Read first record for demo
        with open(sample_data_path) as f:
            lines = f.readlines()
            if len(lines) > 1:
                # Parse CSV header and first row
                header = lines[0].strip().split(',')
                first_row = lines[1].strip().split(',')
                record = dict(zip(header, first_row))
                
                # Format as input for pipeline
                input_text = f"""Process this data record:
                
Record ID: {record.get('id', 'unknown')}
Text: {record.get('text', '')}
Source: {record.get('source', 'unknown')}
Timestamp: {record.get('timestamp', 'unknown')}

Extract and enrich this record with sentiment, entities, and category."""
            else:
                input_text = "Process sample data record for enrichment."
    else:
        input_text = "Process data record: Customer loves the new feature. Extract sentiment, entities, and category."
    
    # v3.0.0 uses MessagesState - provide input as messages
    input_data = {
        "messages": [
            HumanMessage(content=input_text)
        ],
        "input_path": str(sample_data_path) if sample_data_path.exists() else "sample_data.csv",
        "output_path": "enriched_data.json",
    }

    # Execute with tracing
    if obs_enabled:
        async with trace_runtime_execution("pipeline-001", graph_name="etl_pipeline"):
            result = await runtime.execute(
                execution_id="pipeline-001",
                input_data=input_data,
            )
    else:
        result = await runtime.execute(
            execution_id="pipeline-001",
            input_data=input_data,
        )
    
    # Extract results from messages
    messages = result.get("messages", [])
    executed_nodes = [k for k in result.keys() if k != "messages"]
    
    print(f"\n✅ Pipeline Complete")
    print(f"📝 Execution Path: {' → '.join(executed_nodes)}")
    
    if messages:
        # Find enrichment result (AIMessage from router)
        enriched_data = None
        for msg in messages:
            if hasattr(msg, 'content'):
                content = str(msg.content)
                # Look for JSON structure with sentiment field
                if "sentiment" in content and "{" in content:
                    try:
                        # Extract JSON from message (handle newlines)
                        json_start = content.find("{")
                        json_end = content.rfind("}") + 1
                        if json_end > json_start:
                            json_str = content[json_start:json_end]
                            # Clean up JSON string (remove newlines, normalize whitespace)
                            import re
                            json_str = re.sub(r'\s+', ' ', json_str.strip())
                            enriched_data = json.loads(json_str)
                            break
                    except (json.JSONDecodeError, ValueError):
                        # Try parsing with ast.literal_eval as fallback
                        try:
                            import ast
                            # Extract just the dict part
                            dict_str = content[json_start:json_end]
                            enriched_data = ast.literal_eval(dict_str)
                            break
                        except:
                            pass
        
        if enriched_data:
            print(f"\n📋 Enriched Data:")
            print(json.dumps(enriched_data, indent=2))
            print(f"\n📊 Summary:")
            print(f"  ✅ Sentiment: {enriched_data.get('sentiment', 'unknown').upper()}")
            print(f"  ✅ Category: {enriched_data.get('category', 'unknown').upper()}")
            entities = enriched_data.get('entities', [])
            if entities:
                print(f"  ✅ Entities: {', '.join(entities)}")
            else:
                print(f"  ✅ Entities: None")
            confidence = enriched_data.get('confidence', 0)
            print(f"  ✅ Confidence: {confidence:.1%}")
        else:
            # Fallback: show last message
            last_message = messages[-1]
            content = getattr(last_message, "content", "")
            print(f"\n📊 Output: {content[:400]}...")
    else:
        print(f"✅ Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())

