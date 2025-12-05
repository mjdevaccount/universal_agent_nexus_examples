"""
Interactive Multi-Agent Playground

Watch agents with different personalities interact in real-time.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import asyncio
import json
import os

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

# ===== AGENT ARCHETYPES =====

ARCHETYPES = {
    "bully": {
        "name": "The Bully",
        "role": "Dominant, aggressive",
        "personality": {"aggression": 9, "empathy": 2, "confidence": 10},
        "prompt": """You are a playground bully. You dominate conversations, interrupt others, 
use intimidation and put-downs. Show little empathy. Assert dominance constantly.
Keep responses VERY SHORT (1-2 sentences max). Be confrontational."""
    },
    "shy_kid": {
        "name": "The Shy Kid",  
        "role": "Timid, anxious",
        "personality": {"aggression": 1, "empathy": 9, "confidence": 2},
        "prompt": """You are shy and anxious. Speak hesitantly with "um" and "uh". 
Apologize frequently. Avoid conflict. Get flustered easily.
Keep responses VERY SHORT (1-2 sentences max). Show uncertainty."""
    },
    "mediator": {
        "name": "The Mediator",
        "role": "Diplomatic, problem-solver",
        "personality": {"aggression": 3, "empathy": 9, "confidence": 7},
        "prompt": """You are diplomatic. Try to understand all perspectives. 
Suggest compromises. Calm heated situations. Speak reasonably.
Keep responses VERY SHORT (1-2 sentences max). Be diplomatic."""
    },
    "joker": {
        "name": "The Joker",
        "role": "Humorous, class clown",
        "personality": {"aggression": 4, "empathy": 6, "confidence": 8, "humor": 10},
        "prompt": """You are the class clown. Make jokes and puns constantly. 
Use humor to defuse tension. Don't take things seriously. Use emojis.
Keep responses VERY SHORT (1-2 sentences max). Be funny."""
    },
    "teacher": {
        "name": "The Teacher",
        "role": "Authoritative, instructive",
        "personality": {"aggression": 4, "empathy": 7, "confidence": 9},
        "prompt": """You are a patient but firm teacher. Maintain order. 
Guide children toward good behavior. Set clear expectations.
Keep responses VERY SHORT (1-2 sentences max). Be authoritative but kind."""
    },
}

# ===== SIMULATION ENGINE =====

class Simulation:
    def __init__(self, agents: List[AgentConfig], scenario: str):
        self.agents = agents
        self.scenario = scenario
        self.history = []
        
    async def run_turn(self, agent: AgentConfig) -> Dict:
        """Run one agent's turn using OpenAI."""
        archetype = ARCHETYPES[agent.archetype]
        
        # Build context
        context = "\n".join([
            f"{t['agent']}: {t['message']}"
            for t in self.history[-5:]  # Last 5 turns
        ]) if self.history else "You are the first to speak."
        
        # Call OpenAI (you'll need OPENAI_API_KEY env var)
        from openai import OpenAI
        
        try:
            client = OpenAI()
            response = await asyncio.to_thread(
                lambda: client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": archetype["prompt"]},
                        {"role": "user", "content": f"Scenario: {self.scenario}\n\nConversation:\n{context}\n\nYou say:"}
                    ],
                    max_tokens=60,
                    temperature=0.9
                )
            )
            
            message = response.choices[0].message.content.strip()
        except Exception as e:
            # Fallback if OpenAI fails
            message = f"[{agent.name} thinking...] {str(e)[:50]}"
        
        turn = {
            "agent": agent.name,
            "archetype": agent.archetype,
            "message": message,
            "personality": archetype["personality"]
        }
        
        self.history.append(turn)
        return turn

# ===== WEBSOCKET =====

@app.websocket("/ws/simulate")
async def simulate(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Get config
        config = await websocket.receive_json()
        req = SimulationRequest(**config)
        
        # Start simulation
        sim = Simulation(req.agents, req.scenario)
        
        await websocket.send_json({
            "type": "start",
            "scenario": req.scenario
        })
        
        # Run turns
        for turn_num in range(req.max_turns):
            for agent in req.agents:
                turn = await sim.run_turn(agent)
                
                await websocket.send_json({
                    "type": "turn",
                    "data": turn,
                    "turn_number": turn_num
                })
                
                await asyncio.sleep(1.5)  # Pause between turns
        
        await websocket.send_json({"type": "complete"})
        
    except WebSocketDisconnect:
        pass

# ===== REST ENDPOINTS =====

@app.get("/archetypes")
async def get_archetypes():
    return {"archetypes": ARCHETYPES}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

