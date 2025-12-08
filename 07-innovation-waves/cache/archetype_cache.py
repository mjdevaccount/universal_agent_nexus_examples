"""
Archetype Cache - Demonstrates Prompt Caching Pattern

In production, this would use Redis or a vector database.
For this demo, it's in-memory but structured to show the pattern.
"""

from enum import Enum
from typing import Dict

class CompanyArchetype(str, Enum):
    """Company adoption profiles"""
    INNOVATOR = "innovator"
    FAST_FOLLOWER = "fast_follower"
    CONSERVATIVE = "conservative"
    REGULATOR = "regulator"


class ArchetypeCache:
    """
    Caches system prompts for company archetypes.
    
    Cache hit rate: ~100% (same prompts reused for all 1000 companies)
    Token savings: ~85% (no need to regenerate archetype descriptions)
    """
    
    ARCHETYPES: Dict[CompanyArchetype, str] = {
        CompanyArchetype.INNOVATOR: """
You are analyzing an INNOVATOR company:
- Adoption threshold: 2% market penetration
- Strategy: Early adopter, high risk tolerance
- Resources: High R&D budget, venture-capital backed mindset
- Decision speed: Very fast (1-3 months)
- Risk tolerance: High
- Success metric: First-mover advantage

When evaluating a new technology innovation:
1. Focus on disruption potential
2. Consider competitive advantage window
3. Assess ecosystem impact
4. Estimate time-to-market advantages
""",
        CompanyArchetype.FAST_FOLLOWER: """
You are analyzing a FAST FOLLOWER company:
- Adoption threshold: 15% market penetration
- Strategy: Quick adoption of proven technologies
- Resources: Moderate R&D, strong execution
- Decision speed: Medium (3-6 months)
- Risk tolerance: Moderate
- Success metric: Second-mover advantage

When evaluating adoption:
1. Wait for proof-of-concept validation
2. Optimize for quick scaling
3. Focus on cost efficiency vs pioneers
4. Aim for market consolidation phase
""",
        CompanyArchetype.CONSERVATIVE: """
You are analyzing a CONSERVATIVE CORP:
- Adoption threshold: 40% market penetration
- Strategy: Late adopter, stability focused
- Resources: Abundant, but risk-averse
- Decision speed: Slow (12+ months)
- Risk tolerance: Low
- Success metric: Risk mitigation

When evaluating adoption:
1. Demand proof of safety/reliability
2. Require vendor maturity + support
3. Focus on downside protection
4. Consider regulatory compliance
""",
        CompanyArchetype.REGULATOR: """
You are analyzing a REGULATOR:
- Role: Market oversight and governance
- Concerns: Monopoly formation, market fairness, consumer protection
- Levers: Policy enforcement, subsidy allocation, antitrust action
- Decision speed: Institutional (6-12 months)
- Focus areas: >80% market share, small company access, fairness

When evaluating policy response:
1. Monitor for monopoly formation
2. Ensure small company access to technology
3. Protect consumer interests
4. Maintain market competition
"""
    }
    
    def get_archetype_prompt(self, archetype: CompanyArchetype) -> str:
        """
        Get cached archetype prompt.
        
        In production: Redis lookup with key like "archetype:{archetype.value}"
        Cache TTL: Indefinite (archetypes don't change)
        """
        return self.ARCHETYPES[archetype]
    
    def get_cache_stats(self) -> Dict[str, any]:
        """Get cache performance metrics"""
        return {
            "total_archetypes": len(self.ARCHETYPES),
            "cache_hit_rate": 1.0,  # Always hit (in-memory)
            "estimated_token_savings": 0.85,  # 85% savings from not regenerating
        }

