"""Run the data pipeline agent using NexusRuntime - Reduced from 152 to 45 lines."""

import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from universal_agent_nexus.runtime import NexusRuntime, JSONExtractor


async def main():
    # Create runtime with JSON extractor
    runtime = NexusRuntime(
        manifest_path=Path(__file__).parent / "manifest.yaml",
        graph_name="etl_pipeline",
        service_name="data-pipeline",
        extractor=JSONExtractor(),
    )
    
    await runtime.setup()
    
    # Load sample data
    sample_data_path = Path(__file__).parent / "sample_data.csv"
    if sample_data_path.exists():
        with open(sample_data_path) as f:
            lines = f.readlines()
            if len(lines) > 1:
                header = lines[0].strip().split(',')
                first_row = lines[1].strip().split(',')
                record = dict(zip(header, first_row))
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
    
    # Execute
    input_data = runtime.create_input(
        input_text,
        input_path=str(sample_data_path) if sample_data_path.exists() else "sample_data.csv",
        output_path="enriched_data.json",
    )
    
    result = await runtime.execute("pipeline-001", input_data)
    
    # Display results
    print(f"\n[OK] Pipeline Complete")
    print(f"[PATH] Execution Path: {' -> '.join(result['execution_path'])}")
    
    if result.get("parsed_json"):
        enriched_data = result["parsed_json"]
        print(f"\n[DATA] Enriched Data:")
        print(json.dumps(enriched_data, indent=2))
        print(f"\n[SUMMARY]:")
        print(f"  [OK] Sentiment: {enriched_data.get('sentiment', 'unknown').upper()}")
        print(f"  [OK] Category: {enriched_data.get('category', 'unknown').upper()}")
        entities = enriched_data.get('entities', [])
        if entities:
            print(f"  [OK] Entities: {', '.join(entities)}")
        confidence = enriched_data.get('confidence', 0)
        print(f"  [OK] Confidence: {confidence:.1%}")
    elif result.get("last_content"):
        print(f"\n[OUTPUT] Output: {result['last_content'][:400]}...")


if __name__ == "__main__":
    asyncio.run(main())
