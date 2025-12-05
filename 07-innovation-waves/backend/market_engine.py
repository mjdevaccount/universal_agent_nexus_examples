"""
Market Simulation Engine - Innovation Waves

Simulates technology adoption dynamics across 300-1000 companies.
Uses network effects, rich-get-richer dynamics, and innovation diffusion.
"""

import random
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np


class CompanyType(str, Enum):
    INNOVATOR = "innovator"
    CONSERVATIVE = "conservative_corp"
    FAST_FOLLOWER = "fast_follower"
    REGULATOR = "regulator"


@dataclass
class Technology:
    """A technology/patent that can spread through the market."""
    id: str
    name: str
    adoption_rate: float = 0.0  # 0-1, % of market adopted
    value_multiplier: float = 1.5  # Competitive advantage
    diffusion_speed: float = 0.1  # How fast it spreads
    origin_time: int = 0
    adopters: set = field(default_factory=set)


@dataclass
class Company:
    """A company agent in the market simulation."""
    id: int
    name: str
    company_type: CompanyType
    
    # Market position
    market_cap: float = 100.0
    market_share: float = 0.01
    
    # Innovation metrics
    innovation_score: float = 0.5
    tech_stack: List[str] = field(default_factory=list)
    
    # Position for visualization
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    
    # Network
    connections: List[int] = field(default_factory=list)
    
    def adoption_threshold(self) -> float:
        """When will this company adopt new tech?"""
        if self.company_type == CompanyType.INNOVATOR:
            return 0.02  # Adopt at 2% market adoption
        elif self.company_type == CompanyType.FAST_FOLLOWER:
            return 0.15  # Adopt at 15% market adoption
        elif self.company_type == CompanyType.CONSERVATIVE:
            return 0.40  # Adopt at 40% market adoption
        else:
            return 1.0  # Regulators don't adopt
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.company_type.value,
            "market_cap": self.market_cap,
            "market_share": self.market_share,
            "innovation_score": self.innovation_score,
            "tech_stack": self.tech_stack,
            "x": self.x,
            "y": self.y,
            "connections": self.connections[:5],  # Limit for JSON
        }


class MarketSimulator:
    """
    Core market simulation engine.
    
    Dynamics:
    - Rich-get-richer: Market cap affects competition outcomes
    - Network effects: Connected companies spread tech faster
    - Innovation diffusion: S-curve adoption patterns
    - Policy enforcement: Regulators can intervene
    """
    
    def __init__(self, num_companies: int = 300, width: float = 1000, height: float = 800):
        self.width = width
        self.height = height
        self.companies: Dict[int, Company] = {}
        self.technologies: Dict[str, Technology] = {}
        self.tick = 0
        self.events: List[Dict] = []
        
        # Market metrics
        self.total_market_cap = 0.0
        self.concentration_index = 0.0  # HHI
        
        self._initialize_companies(num_companies)
        self._build_network()
    
    def _initialize_companies(self, num_companies: int):
        """Create companies with realistic distribution."""
        # Distribution: 15% innovators, 20% fast followers, 60% conservatives, 5% regulators
        type_distribution = [
            (CompanyType.INNOVATOR, 0.15),
            (CompanyType.FAST_FOLLOWER, 0.20),
            (CompanyType.CONSERVATIVE, 0.60),
            (CompanyType.REGULATOR, 0.05),
        ]
        
        # Power law distribution for market cap
        for i in range(num_companies):
            # Determine company type
            r = random.random()
            cumulative = 0
            company_type = CompanyType.CONSERVATIVE
            for ctype, prob in type_distribution:
                cumulative += prob
                if r < cumulative:
                    company_type = ctype
                    break
            
            # Power law market cap (few big, many small)
            market_cap = 100 * (1 + random.paretovariate(1.5))
            
            # Innovation score based on type
            if company_type == CompanyType.INNOVATOR:
                innovation_score = 0.7 + random.random() * 0.3
            elif company_type == CompanyType.FAST_FOLLOWER:
                innovation_score = 0.4 + random.random() * 0.3
            else:
                innovation_score = 0.1 + random.random() * 0.3
            
            # Random position with clustering by type
            angle = random.random() * 2 * math.pi
            radius = random.random() * min(self.width, self.height) * 0.4
            
            # Cluster by type
            type_offset = {
                CompanyType.INNOVATOR: (0.2, 0.3),
                CompanyType.FAST_FOLLOWER: (0.5, 0.5),
                CompanyType.CONSERVATIVE: (0.7, 0.6),
                CompanyType.REGULATOR: (0.5, 0.8),
            }
            ox, oy = type_offset[company_type]
            
            company = Company(
                id=i,
                name=f"{company_type.value[:3].upper()}-{i:03d}",
                company_type=company_type,
                market_cap=market_cap,
                market_share=0.0,  # Calculated later
                innovation_score=innovation_score,
                x=ox * self.width + (random.random() - 0.5) * self.width * 0.3,
                y=oy * self.height + (random.random() - 0.5) * self.height * 0.3,
            )
            
            self.companies[i] = company
        
        self._recalculate_market_shares()
    
    def _build_network(self):
        """Build company network connections (preferential attachment)."""
        company_ids = list(self.companies.keys())
        
        for company in self.companies.values():
            # Number of connections based on market cap
            num_connections = min(10, max(2, int(math.log(company.market_cap))))
            
            # Preferential attachment - connect to larger companies more often
            weights = [self.companies[cid].market_cap for cid in company_ids if cid != company.id]
            total_weight = sum(weights)
            probs = [w / total_weight for w in weights]
            
            candidates = [cid for cid in company_ids if cid != company.id]
            if candidates and len(candidates) >= num_connections:
                connections = np.random.choice(
                    candidates, 
                    size=min(num_connections, len(candidates)), 
                    replace=False,
                    p=probs if len(probs) == len(candidates) else None
                )
                company.connections = list(connections)
    
    def _recalculate_market_shares(self):
        """Recalculate market shares from market caps."""
        self.total_market_cap = sum(c.market_cap for c in self.companies.values())
        
        for company in self.companies.values():
            company.market_share = company.market_cap / self.total_market_cap if self.total_market_cap > 0 else 0
        
        # Calculate HHI (concentration index)
        self.concentration_index = sum(c.market_share ** 2 for c in self.companies.values())
    
    def drop_technology(self, name: str, value_multiplier: float = 1.5, diffusion_speed: float = 0.1) -> Technology:
        """Drop a new technology/patent into the market."""
        tech_id = f"tech_{len(self.technologies)}_{name.lower().replace(' ', '_')}"
        
        tech = Technology(
            id=tech_id,
            name=name,
            value_multiplier=value_multiplier,
            diffusion_speed=diffusion_speed,
            origin_time=self.tick,
        )
        
        self.technologies[tech_id] = tech
        
        # Find initial adopter (random innovator)
        innovators = [c for c in self.companies.values() if c.company_type == CompanyType.INNOVATOR]
        if innovators:
            first_adopter = random.choice(innovators)
            self._adopt_technology(first_adopter, tech)
        
        self.events.append({
            "type": "tech_drop",
            "tick": self.tick,
            "tech": tech_id,
            "name": name,
        })
        
        return tech
    
    def _adopt_technology(self, company: Company, tech: Technology):
        """Have a company adopt a technology."""
        if tech.id in company.tech_stack:
            return  # Already adopted
        
        company.tech_stack.append(tech.id)
        tech.adopters.add(company.id)
        tech.adoption_rate = len(tech.adopters) / len(self.companies)
        
        # Boost from adoption
        boost = tech.value_multiplier * company.innovation_score
        company.market_cap *= (1 + boost * 0.1)
        
        self.events.append({
            "type": "adoption",
            "tick": self.tick,
            "company": company.id,
            "tech": tech.id,
        })
    
    def apply_regulation(self, regulation_type: str) -> Dict:
        """Apply a market regulation."""
        result = {"type": regulation_type, "affected": []}
        
        if regulation_type == "anti_monopoly":
            # Find companies with >80% market share
            for company in self.companies.values():
                if company.market_share > 0.8:
                    # Force divestiture
                    company.market_cap *= 0.5
                    result["affected"].append(company.id)
        
        elif regulation_type == "innovation_subsidy":
            # Boost small innovative companies
            for company in self.companies.values():
                if company.market_cap < 500 and company.innovation_score > 0.5:
                    company.market_cap *= 1.2
                    result["affected"].append(company.id)
        
        self._recalculate_market_shares()
        
        self.events.append({
            "type": "regulation",
            "tick": self.tick,
            "regulation": regulation_type,
            "affected": result["affected"],
        })
        
        return result
    
    def tick_simulation(self) -> Dict:
        """Advance simulation by one tick."""
        self.tick += 1
        
        # 1. Technology diffusion
        for tech in self.technologies.values():
            self._diffuse_technology(tech)
        
        # 2. Market competition
        self._run_competition()
        
        # 3. Update positions (for visualization)
        self._update_positions()
        
        # 4. Recalculate market metrics
        self._recalculate_market_shares()
        
        return self.get_state()
    
    def _diffuse_technology(self, tech: Technology):
        """Spread technology through the network."""
        new_adopters = []
        
        for company in self.companies.values():
            if tech.id in company.tech_stack:
                continue  # Already adopted
            
            # Check if adoption threshold met
            if tech.adoption_rate >= company.adoption_threshold():
                # Higher chance if connected to adopters
                connected_adopters = sum(
                    1 for conn_id in company.connections 
                    if conn_id in tech.adopters
                )
                
                adoption_prob = tech.diffusion_speed * (1 + connected_adopters * 0.5)
                
                if random.random() < adoption_prob:
                    new_adopters.append(company)
        
        for company in new_adopters:
            self._adopt_technology(company, tech)
    
    def _run_competition(self):
        """Simulate market competition between companies."""
        # Rich-get-richer with some randomness
        for company in self.companies.values():
            if company.company_type == CompanyType.REGULATOR:
                continue
            
            # Growth based on innovation and market position
            growth_rate = 0.001 * (
                company.innovation_score * 2 +
                len(company.tech_stack) * 0.5 +
                random.gauss(0, 0.5)
            )
            
            # Network effect - connected to successful companies
            network_bonus = sum(
                self.companies[conn_id].market_share * 0.1
                for conn_id in company.connections
                if conn_id in self.companies
            )
            
            company.market_cap *= (1 + growth_rate + network_bonus)
            
            # Small companies can fail
            if company.market_cap < 10:
                company.market_cap = 10  # Minimum viable
    
    def _update_positions(self):
        """Update company positions for visualization (force-directed)."""
        # Simplified force-directed layout
        for company in self.companies.values():
            # Attraction to connected companies
            for conn_id in company.connections[:5]:
                if conn_id not in self.companies:
                    continue
                other = self.companies[conn_id]
                dx = other.x - company.x
                dy = other.y - company.y
                dist = max(1, math.sqrt(dx*dx + dy*dy))
                
                force = 0.01 * (dist - 100) / dist
                company.vx += dx * force
                company.vy += dy * force
            
            # Repulsion from close companies
            for other in random.sample(list(self.companies.values()), min(10, len(self.companies))):
                if other.id == company.id:
                    continue
                dx = other.x - company.x
                dy = other.y - company.y
                dist = max(1, math.sqrt(dx*dx + dy*dy))
                
                if dist < 50:
                    force = -5 / (dist * dist)
                    company.vx += dx * force
                    company.vy += dy * force
            
            # Apply velocity with damping
            company.x += company.vx * 0.5
            company.y += company.vy * 0.5
            company.vx *= 0.9
            company.vy *= 0.9
            
            # Keep in bounds
            company.x = max(50, min(self.width - 50, company.x))
            company.y = max(50, min(self.height - 50, company.y))
    
    def get_state(self) -> Dict:
        """Get current market state for visualization."""
        return {
            "tick": self.tick,
            "companies": [c.to_dict() for c in self.companies.values()],
            "technologies": [
                {
                    "id": t.id,
                    "name": t.name,
                    "adoption_rate": t.adoption_rate,
                    "adopters": len(t.adopters),
                }
                for t in self.technologies.values()
            ],
            "metrics": {
                "total_market_cap": self.total_market_cap,
                "concentration_index": self.concentration_index,
                "num_companies": len(self.companies),
                "num_technologies": len(self.technologies),
            },
            "events": self.events[-10:],  # Last 10 events
        }
    
    def scale_to(self, num_companies: int):
        """Scale simulation to different number of companies."""
        current = len(self.companies)
        
        if num_companies > current:
            # Add more companies
            for i in range(current, num_companies):
                company_type = random.choice([
                    CompanyType.INNOVATOR,
                    CompanyType.FAST_FOLLOWER,
                    CompanyType.CONSERVATIVE,
                ])
                
                company = Company(
                    id=i,
                    name=f"{company_type.value[:3].upper()}-{i:03d}",
                    company_type=company_type,
                    market_cap=100 * (1 + random.paretovariate(1.5)),
                    innovation_score=random.random(),
                    x=random.random() * self.width,
                    y=random.random() * self.height,
                )
                self.companies[i] = company
        
        elif num_companies < current:
            # Remove smallest companies
            sorted_companies = sorted(
                self.companies.values(), 
                key=lambda c: c.market_cap
            )
            for company in sorted_companies[:current - num_companies]:
                del self.companies[company.id]
        
        self._build_network()
        self._recalculate_market_shares()

