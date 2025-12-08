"""Research Assistant - December 2025 Multi-Stage Pipeline.

Demonstrates:
- IntelligenceNode: Analyze documents
- ExtractionNode: Extract key findings
- ValidationNode: Validate research quality
- Pipeline composition across stages

Code Reduction:
- Before: ~280 LOC
- After: ~210 LOC (-25%)
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.workflows.nodes import NodeState
from shared.workflows.common_nodes import (
    IntelligenceNode,
    ExtractionNode,
    ValidationNode,
)
from shared.workflows.workflow import Workflow


class ResearchState(NodeState):
    """Workflow state."""
    query: str
    analysis: str = ""
    extracted: Dict[str, Any] = {}
    validated: Dict[str, Any] = {}


class ResearchFindings(BaseModel):
    """Research output schema."""
    key_points: List[str] = Field(description="Main findings")
    entities: List[str] = Field(description="People, orgs, technologies mentioned")
    themes: List[str] = Field(description="Main research themes")
    summary: str = Field(description="Executive summary")
    confidence: float = Field(description="Research quality 0.0-1.0")


class ResearchWorkflow(Workflow):
    """Multi-stage research pipeline."""
    
    def __init__(self, llm_reasoning, llm_extraction):
        intelligence = IntelligenceNode(
            llm=llm_reasoning,
            prompt_template=(
                "Conduct research analysis on:\n\n{query}\n\n"
                "Provide:\n1. Key findings\n2. Entities mentioned\n3. Main themes\n4. Summary"
            ),
            required_state_keys=["query"],
            name="research_analysis",
        )
        
        extraction = ExtractionNode(
            llm=llm_extraction,
            prompt_template=(
                "Extract structured findings from:\n{analysis}\n\n"
                "Return JSON with key_points, entities, themes, summary, confidence."
            ),
            output_schema=ResearchFindings,
            name="findings_extraction",
        )
        
        def valid_points_count(data):
            return len(data.get("key_points", [])) >= 2
        
        def valid_summary_length(data):
            return len(data.get("summary", "")) > 20
        
        validation = ValidationNode(
            output_schema=ResearchFindings,
            validation_rules={
                "min_points": valid_points_count,
                "summary_quality": valid_summary_length,
            },
            name="research_validation",
        )
        
        super().__init__(
            name="research-assistant",
            state_schema=ResearchState,
            nodes=[intelligence, extraction, validation],
            edges=[
                ("analysis", "extraction"),
                ("extraction", "validation"),
            ],
        )
    
    async def invoke(self, query: str) -> Dict[str, Any]:
        start = datetime.now()
        result = await self.execute({"query": query})
        duration = (datetime.now() - start).total_seconds() * 1000
        
        validated = result.get("validated", {})
        return {
            "query": query[:80] + "..." if len(query) > 80 else query,
            "key_points": validated.get("key_points", []),
            "entities": validated.get("entities", []),
            "themes": validated.get("themes", []),
            "summary": validated.get("summary", ""),
            "confidence": validated.get("confidence", 0.0),
            "metrics": {"duration_ms": duration, "success": "validated" in result},
        }


async def main():
    print("\n" + "="*70)
    print("Example 05: Research Assistant - December 2025 Pattern")
    print("="*70 + "\n")
    
    # Initialize LLMs (local qwen3 via Ollama)
    llm_reasoning = ChatOllama(
        model="qwen3:8b",
        base_url="http://localhost:11434",
        temperature=0.8,  # Creative reasoning
        num_predict=600,
    )
    llm_extraction = ChatOllama(
        model="qwen3:8b",
        base_url="http://localhost:11434",
        temperature=0.1,  # Deterministic extraction
        num_predict=400,
    )
    
    workflow = ResearchWorkflow(llm_reasoning, llm_extraction)
    
    queries = [
        "Impact of AI on software development: key trends and future outlook",
        "Machine learning in financial markets: risks and opportunities",
    ]
    
    for i, query in enumerate(queries, 1):
        try:
            result = await workflow.invoke(query)
            print(f"[{i}] Query: {result['query']}")
            print(f"    Key Points: {len(result['key_points'])} found")
            print(f"    Entities: {len(result['entities'])} identified")
            print(f"    Themes: {', '.join(result['themes'][:2]) if result['themes'] else 'None'}")
            print(f"    Confidence: {result['confidence']:.1%}\n")
        except Exception as e:
            print(f"[{i}] Error: {e}\n")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
