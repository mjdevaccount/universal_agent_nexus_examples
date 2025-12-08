"""
Innovation Waves - Technology Adoption Simulator API

Backend for the multi-runtime technology adoption demo.
Serves market simulation state via WebSocket and REST endpoints.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import json
import sys
from pathlib import Path

# Add parent directories for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from market_engine import MarketSimulator, CompanyType

# Setup observability
try:
    from universal_agent_tools.observability import setup_observability
    setup_observability("innovation-waves")
except ImportError:
    pass

app = FastAPI(
    title="Innovation Waves API",
    description="Technology Adoption Simulator - One YAML → 5 Runtimes",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global simulator instance
simulator: Optional[MarketSimulator] = None
connected_clients: List[WebSocket] = []
simulation_running = False


# ===== MODELS =====

class TechDropRequest(BaseModel):
    name: str
    value_multiplier: float = 1.5
    diffusion_speed: float = 0.1


class RegulationRequest(BaseModel):
    regulation_type: str  # anti_monopoly, innovation_subsidy


class ScaleRequest(BaseModel):
    num_companies: int


class SimulationConfig(BaseModel):
    num_companies: int = 300
    tick_interval_ms: int = 100


# ===== WEBSOCKET BROADCAST =====

async def broadcast_state():
    """Broadcast current state to all connected clients."""
    if simulator is None:
        return
    
    state = simulator.get_state()
    message = json.dumps({"type": "state", "data": state})
    
    for client in connected_clients[:]:
        try:
            await client.send_text(message)
        except:
            connected_clients.remove(client)


async def broadcast_event(event_type: str, data: Dict):
    """Broadcast a specific event to all clients."""
    message = json.dumps({"type": event_type, "data": data})
    
    for client in connected_clients[:]:
        try:
            await client.send_text(message)
        except:
            connected_clients.remove(client)


# ===== SIMULATION LOOP =====

async def simulation_loop(tick_interval_ms: int = 100):
    """Main simulation loop."""
    global simulation_running
    
    while simulation_running and simulator is not None:
        simulator.tick_simulation()
        await broadcast_state()
        await asyncio.sleep(tick_interval_ms / 1000)


# ===== WEBSOCKET ENDPOINT =====

@app.websocket("/ws/market")
async def market_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time market updates."""
    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        # Send initial state
        if simulator:
            await websocket.send_json({
                "type": "init",
                "data": simulator.get_state()
            })
        
        # Keep connection alive and handle commands
        while True:
            data = await websocket.receive_json()
            
            if data.get("command") == "drop_tech":
                if simulator:
                    tech = simulator.drop_technology(
                        data.get("name", "AI Breakthrough"),
                        data.get("value_multiplier", 1.5),
                        data.get("diffusion_speed", 0.1)
                    )
                    await broadcast_event("tech_dropped", {
                        "tech_id": tech.id,
                        "name": tech.name
                    })
            
            elif data.get("command") == "regulate":
                if simulator:
                    result = simulator.apply_regulation(data.get("type", "anti_monopoly"))
                    await broadcast_event("regulation", result)
            
            elif data.get("command") == "scale":
                if simulator:
                    simulator.scale_to(data.get("count", 300))
                    await broadcast_state()
    
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in connected_clients:
            connected_clients.remove(websocket)


# ===== REST ENDPOINTS =====

@app.post("/simulation/start")
async def start_simulation(config: SimulationConfig):
    """Start a new market simulation."""
    global simulator, simulation_running
    
    simulator = MarketSimulator(num_companies=config.num_companies)
    simulation_running = True
    
    # Start simulation loop in background
    asyncio.create_task(simulation_loop(config.tick_interval_ms))
    
    return {
        "status": "started",
        "num_companies": config.num_companies,
        "tick_interval_ms": config.tick_interval_ms
    }


@app.post("/simulation/stop")
async def stop_simulation():
    """Stop the running simulation."""
    global simulation_running
    simulation_running = False
    return {"status": "stopped"}


@app.get("/simulation/state")
async def get_state():
    """Get current simulation state."""
    if simulator is None:
        return {"error": "No simulation running"}
    return simulator.get_state()


@app.post("/god/drop-tech")
async def god_drop_tech(request: TechDropRequest):
    """GOD MODE: Drop a new technology into the market."""
    if simulator is None:
        return {"error": "No simulation running"}
    
    tech = simulator.drop_technology(
        request.name,
        request.value_multiplier,
        request.diffusion_speed
    )
    
    await broadcast_event("tech_dropped", {
        "tech_id": tech.id,
        "name": tech.name,
        "value_multiplier": tech.value_multiplier
    })
    
    return {"status": "dropped", "tech_id": tech.id, "name": tech.name}


@app.post("/god/regulation")
async def god_regulation(request: RegulationRequest):
    """GOD MODE: Apply market regulation."""
    if simulator is None:
        return {"error": "No simulation running"}
    
    result = simulator.apply_regulation(request.regulation_type)
    
    await broadcast_event("regulation", result)
    
    return {"status": "applied", "result": result}


@app.post("/god/scale")
async def god_scale(request: ScaleRequest):
    """GOD MODE: Scale to N companies."""
    if simulator is None:
        return {"error": "No simulation running"}
    
    simulator.scale_to(request.num_companies)
    
    await broadcast_event("scaled", {"num_companies": request.num_companies})
    
    return {"status": "scaled", "num_companies": request.num_companies}


@app.get("/archetypes")
async def get_archetypes():
    """Get available company archetypes."""
    return {
        "archetypes": {
            "innovator": {
                "name": "Innovator",
                "description": "Early adopter, high risk tolerance",
                "adoption_threshold": 0.02,
                "color": "#22c55e"
            },
            "fast_follower": {
                "name": "Fast Follower",
                "description": "Quick to adopt proven tech",
                "adoption_threshold": 0.15,
                "color": "#3b82f6"
            },
            "conservative_corp": {
                "name": "Conservative Corp",
                "description": "Late adopter, stability focused",
                "adoption_threshold": 0.40,
                "color": "#6b7280"
            },
            "regulator": {
                "name": "Regulator",
                "description": "Market overseer, policy enforcer",
                "adoption_threshold": 1.0,
                "color": "#ef4444"
            }
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "innovation-waves",
        "simulation_running": simulation_running,
        "connected_clients": len(connected_clients),
        "companies": len(simulator.companies) if simulator else 0
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8889)

