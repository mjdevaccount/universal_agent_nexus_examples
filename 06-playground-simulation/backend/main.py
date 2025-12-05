"""
Interactive Multi-Agent Playground

Uses YOUR Universal Agent Fabric for role definitions
+ danielmiessler Fabric for LLM provider abstraction.

Architecture:
- Agent archetypes defined in fabric_archetypes/*.yaml (YOUR Fabric)
- LLM calls delegated to danielmiessler Fabric CLI
- Multi-provider support (OpenAI, Ollama, Anthropic, etc.)
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import asyncio

from llm_provider import create_provider

app = FastAPI(title="Agent Playground API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== MODELS =====

class AgentConfig(BaseModel):
    archetype: str
    name: str

class SimulationRequest(BaseModel):
    agents: List[AgentConfig]
    scenario: str
    max_turns: int = 15

# ===== AGENT ARCHETYPES (metadata only - definitions in fabric_archetypes/) =====

ARCHETYPES = {
    "bully": {
        "name": "The Bully",
        "role": "Dominant, aggressive",
        "personality": {"aggression": 9, "empathy": 2, "confidence": 10},
    },
    "shy_kid": {
        "name": "The Shy Kid",  
        "role": "Timid, anxious",
        "personality": {"aggression": 1, "empathy": 9, "confidence": 2},
    },
    "mediator": {
        "name": "The Mediator",
        "role": "Diplomatic, problem-solver",
        "personality": {"aggression": 3, "empathy": 9, "confidence": 7},
    },
    "joker": {
        "name": "The Joker",
        "role": "Humorous, class clown",
        "personality": {"aggression": 4, "empathy": 6, "confidence": 8, "humor": 10},
    },
    "teacher": {
        "name": "The Teacher",
        "role": "Authoritative, instructive",
        "personality": {"aggression": 4, "empathy": 7, "confidence": 9},
    },
}

# ===== SIMULATION ENGINE =====

class Simulation:
    def __init__(self, agents: List[AgentConfig], scenario: str):
        self.agents = agents
        self.scenario = scenario
        self.history = []
        
        # Create providers using YOUR Fabric
        self.providers = {
            agent.archetype: create_provider(agent.archetype)
            for agent in agents
        }
        
    async def run_turn(self, agent: AgentConfig) -> Dict:
        """Run one agent's turn using YOUR Fabric + danielmiessler Fabric."""
        
        # Build context
        context = "\n".join([
            f"{t['agent']}: {t['message']}"
            for t in self.history[-5:]
        ]) if self.history else "You are the first to speak."
        
        # Get provider (loads role from YOUR Fabric)
        provider = self.providers[agent.archetype]
        
        # Generate response (LLM call via danielmiessler Fabric)
        message = await provider.complete(context, self.scenario)
        
        turn = {
            "agent": agent.name,
            "archetype": agent.archetype,
            "message": message,
            "personality": ARCHETYPES[agent.archetype]["personality"]
        }
        
        self.history.append(turn)
        return turn

# ===== WEBSOCKET =====

@app.websocket("/ws/simulate")
async def simulate(websocket: WebSocket):
    await websocket.accept()
    
    try:
        config = await websocket.receive_json()
        req = SimulationRequest(**config)
        
        sim = Simulation(req.agents, req.scenario)
        
        await websocket.send_json({
            "type": "start",
            "scenario": req.scenario
        })
        
        for turn_num in range(req.max_turns):
            for agent in req.agents:
                turn = await sim.run_turn(agent)
                
                await websocket.send_json({
                    "type": "turn",
                    "data": turn,
                    "turn_number": turn_num
                })
                
                await asyncio.sleep(1.5)
        
        await websocket.send_json({"type": "complete"})
        
    except WebSocketDisconnect:
        pass

# ===== REST ENDPOINTS =====

@app.get("/archetypes")
async def get_archetypes():
    """Get archetype metadata (full definitions in fabric_archetypes/)."""
    return {"archetypes": ARCHETYPES}

@app.get("/health")
async def health():
    """Health check - shows YOUR Fabric + danielmiessler Fabric status."""
    try:
        provider = create_provider("mediator")
        info = provider.get_info()
        return {
            "status": "ok",
            "fabric_integration": info["provider"],
            "sample_archetype": info
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
