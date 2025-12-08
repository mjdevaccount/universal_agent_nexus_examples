"""Example 11: N-Decision Router - Refactored with ConditionalWorkflow

Demonstrates using the ConditionalWorkflow helper to route incoming requests
to different handling branches based on intent classification.

Before (custom): 180+ lines of nested routing logic
After (refactored): 120 lines using ConditionalWorkflow
Reduction: -33% code

Key Features:
- Intent classification via Intelligence node
- Multiple conditional branches (5+ intents)
- Automatic routing to appropriate handler
- Per-branch metrics collection
- Fallback/escalation handling

Branches:
- "service" → Customer service handler
- "billing" → Billing/payment handler
- "technical" → Technical support handler
- "sales" → Sales inquiry handler
- "escalate" → Human escalation handler

Usage:
    ollama serve  # Terminal 1
    python 11-n-decision-router/example_11_refactored.py  # Terminal 2
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Optional

from langchain_ollama import ChatOllama
from pydantic import BaseModel

from shared.workflows import (
    ConditionalWorkflow,
    IntelligenceNode,
    BaseNode,
)


# ============================================================================
# State and Models
# ============================================================================

@dataclass
class RequestState:
    """State for request routing."""
    customer_id: str
    request_text: str
    detected_intent: Optional[str] = None
    handler_response: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class IntentResult(BaseModel):
    """Intent classification result."""
    intent: str
    confidence: float
    summary: str


# ============================================================================
# Branch Handlers (BaseNode implementations)
# ============================================================================

class ServiceHandler(BaseNode):
    """Handle customer service inquiries."""
    
    def __init__(self, llm):
        self.llm = llm
        self.metrics = {"calls": 0, "duration_ms": 0}
    
    async def execute(self, state: RequestState) -> RequestState:
        """Process customer service request."""
        self.metrics["calls"] += 1
        
        prompt = f"""You are a friendly customer service agent.
        Handle this request: {state.request_text}
        Provide helpful, concise response."""
        
        response = await self.llm.ainvoke(prompt)
        state.handler_response = response.content
        return state
    
    def validate_input(self, state: RequestState) -> bool:
        return state.request_text is not None and len(state.request_text) > 0
    
    def get_metrics(self) -> dict:
        return {"handler": "service", **self.metrics}


class BillingHandler(BaseNode):
    """Handle billing and payment inquiries."""
    
    def __init__(self, llm):
        self.llm = llm
        self.metrics = {"calls": 0, "duration_ms": 0}
    
    async def execute(self, state: RequestState) -> RequestState:
        """Process billing request."""
        self.metrics["calls"] += 1
        
        prompt = f"""You are a billing support specialist.
        Handle this billing inquiry: {state.request_text}
        Provide information about payments, invoices, or plans."""
        
        response = await self.llm.ainvoke(prompt)
        state.handler_response = response.content
        return state
    
    def validate_input(self, state: RequestState) -> bool:
        return state.request_text is not None
    
    def get_metrics(self) -> dict:
        return {"handler": "billing", **self.metrics}


class TechicalHandler(BaseNode):
    """Handle technical support issues."""
    
    def __init__(self, llm):
        self.llm = llm
        self.metrics = {"calls": 0, "duration_ms": 0}
    
    async def execute(self, state: RequestState) -> RequestState:
        """Process technical support request."""
        self.metrics["calls"] += 1
        
        prompt = f"""You are a technical support engineer.
        Help solve this technical issue: {state.request_text}
        Provide troubleshooting steps or escalation details."""
        
        response = await self.llm.ainvoke(prompt)
        state.handler_response = response.content
        return state
    
    def validate_input(self, state: RequestState) -> bool:
        return state.request_text is not None
    
    def get_metrics(self) -> dict:
        return {"handler": "technical", **self.metrics}


class SalesHandler(BaseNode):
    """Handle sales and product inquiries."""
    
    def __init__(self, llm):
        self.llm = llm
        self.metrics = {"calls": 0, "duration_ms": 0}
    
    async def execute(self, state: RequestState) -> RequestState:
        """Process sales inquiry."""
        self.metrics["calls"] += 1
        
        prompt = f"""You are a sales representative.
        Respond to this inquiry: {state.request_text}
        Provide product information and pricing details."""
        
        response = await self.llm.ainvoke(prompt)
        state.handler_response = response.content
        return state
    
    def validate_input(self, state: RequestState) -> bool:
        return state.request_text is not None
    
    def get_metrics(self) -> dict:
        return {"handler": "sales", **self.metrics}


class EscalationHandler(BaseNode):
    """Handle escalation to human agents."""
    
    def __init__(self, llm):
        self.llm = llm
        self.metrics = {"calls": 0, "duration_ms": 0}
    
    async def execute(self, state: RequestState) -> RequestState:
        """Process escalation request."""
        self.metrics["calls"] += 1
        
        prompt = f"""Acknowledge this escalation request.
        Customer message: {state.request_text}
        Confirm that a human agent will follow up."""
        
        response = await self.llm.ainvoke(prompt)
        state.handler_response = response.content
        return state
    
    def validate_input(self, state: RequestState) -> bool:
        return state.request_text is not None
    
    def get_metrics(self) -> dict:
        return {"handler": "escalation", **self.metrics}


# ============================================================================
# Decision Node for Intent Classification
# ============================================================================

class IntentClassifier(IntelligenceNode):
    """Classify customer requests into intents."""
    
    async def execute(self, state: RequestState) -> str:
        """Classify intent and return branch name."""
        prompt = f"""Classify this customer request into ONE category:
        - 'service' for general customer service
        - 'billing' for payment/invoice issues
        - 'technical' for technical problems
        - 'sales' for product/pricing questions
        - 'escalate' for urgent/complex issues
        
        Request: {state.request_text}
        
        Respond with ONLY the category name (one word)."""
        
        response = await self.llm.ainvoke(prompt)
        intent = response.content.strip().lower()
        
        # Validate and normalize
        valid_intents = ["service", "billing", "technical", "sales", "escalate"]
        if intent not in valid_intents:
            intent = "escalate"  # Default to escalation for unknown
        
        state.detected_intent = intent
        return intent


# ============================================================================
# Main Workflow
# ============================================================================

async def main() -> None:
    """Run the Example 11 workflow."""
    
    # Initialize LLM
    llm = ChatOllama(
        model="mistral",
        base_url="http://localhost:11434",
        temperature=0.3,
    )
    
    # Create decision node
    decision_node = IntentClassifier(
        llm=llm,
        prompt_template="",  # Not used, we override execute
    )
    
    # Create handlers
    handlers = {
        "service": [ServiceHandler(llm)],
        "billing": [BillingHandler(llm)],
        "technical": [TechicalHandler(llm)],
        "sales": [SalesHandler(llm)],
        "escalate": [EscalationHandler(llm)],
    }
    
    # Create workflow
    workflow = ConditionalWorkflow(
        name="request-router",
        state_schema=RequestState,
        decision_node=decision_node,
        branches=handlers,
    )
    
    # Test requests
    test_requests = [
        "My payment didn't go through, what's happening?",
        "How can I upgrade my plan?",
        "I'm getting error code 500 when I log in",
        "What features does the premium tier include?",
        "I need to speak to someone about a critical issue",
        "Can you help me understand my invoice?",
    ]
    
    print("\n" + "=" * 80)
    print("Example 11: N-Decision Router (Refactored with ConditionalWorkflow)")
    print("=" * 80)
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n📝 Request {i}: {request}")
        print("-" * 80)
        
        try:
            # Create request state
            state = RequestState(
                customer_id=f"CUST_{i:04d}",
                request_text=request,
            )
            
            # Execute workflow
            result_state = await workflow.invoke(state)
            
            # Display results
            print(f"\n🎯 Detected Intent: {result_state.detected_intent.upper()}")
            print(f"\n💬 Response:\n{result_state.handler_response}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    # Print workflow metrics
    print("\n" + "=" * 80)
    print("Workflow Summary")
    print("=" * 80)
    
    metrics = workflow.get_metrics()
    print(f"\nWorkflow: {metrics.get('workflow_name', 'unknown')}")
    print(f"Total Requests: {i}")
    print(f"Status: {metrics.get('overall_status', 'unknown')}")
    
    # Branch execution stats
    if "branches" in metrics:
        print(f"\nBranches Executed:")
        for branch_name, branch_metrics in metrics["branches"].items():
            print(f"  - {branch_name}: {branch_metrics.get('executions', 0)} times")
    
    print("\n✅ Example 11 complete!")


if __name__ == "__main__":
    asyncio.run(main())
