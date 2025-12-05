"""
Capability implementations for playground agents.

These are the actual functions that get called when agents use tools.
"""

from typing import Dict, List, Any


async def speak(message: str, tone: str = "neutral") -> Dict[str, Any]:
    """Basic speaking capability - passthrough for agent responses."""
    return {
        "status": "success",
        "message": message,
        "tone": tone,
    }


async def analyze_situation(
    conversation_history: List[str],
    participants: List[str] = None,
) -> Dict[str, Any]:
    """
    Analyze social dynamics in the conversation.
    
    Used by: Mediator archetype
    """
    # Simple analysis based on message patterns
    analysis = {
        "message_count": len(conversation_history),
        "participants": participants or [],
        "tone_assessment": "neutral",
        "conflict_level": "low",
        "recommendations": [],
    }
    
    # Check for conflict indicators
    conflict_words = ["no", "stop", "mine", "get out", "shut up"]
    conflict_count = sum(
        1 for msg in conversation_history 
        if any(word in msg.lower() for word in conflict_words)
    )
    
    if conflict_count > 2:
        analysis["conflict_level"] = "high"
        analysis["tone_assessment"] = "tense"
        analysis["recommendations"].append("Suggest taking turns")
        analysis["recommendations"].append("Acknowledge all perspectives")
    elif conflict_count > 0:
        analysis["conflict_level"] = "medium"
        analysis["tone_assessment"] = "slightly_tense"
        analysis["recommendations"].append("Monitor for escalation")
    
    return analysis


async def observe_situation(
    recent_messages: List[str],
    participant_emotions: Dict[str, str] = None,
) -> Dict[str, Any]:
    """
    Observe and assess behavior patterns.
    
    Used by: Teacher archetype
    """
    observation = {
        "message_count": len(recent_messages),
        "behavioral_assessment": "normal",
        "intervention_needed": False,
        "suggested_action": None,
    }
    
    # Check for concerning behavior patterns
    concerning_patterns = ["bully", "mean", "hurt", "cry", "scared"]
    concerning_count = sum(
        1 for msg in recent_messages
        if any(word in msg.lower() for word in concerning_patterns)
    )
    
    if concerning_count > 1:
        observation["behavioral_assessment"] = "concerning"
        observation["intervention_needed"] = True
        observation["suggested_action"] = "Address behavior directly but kindly"
    
    # Add emotion analysis if provided
    if participant_emotions:
        negative_emotions = ["sad", "angry", "scared", "frustrated"]
        upset_participants = [
            name for name, emotion in participant_emotions.items()
            if emotion.lower() in negative_emotions
        ]
        if upset_participants:
            observation["upset_participants"] = upset_participants
            observation["intervention_needed"] = True
    
    return observation


# Registry of all capabilities
CAPABILITY_REGISTRY = {
    "speak": speak,
    "analyze_situation": analyze_situation,
    "observe_situation": observe_situation,
}


def get_capability(name: str):
    """Get a capability function by name."""
    return CAPABILITY_REGISTRY.get(name)


def list_capabilities() -> List[str]:
    """List all available capabilities."""
    return list(CAPABILITY_REGISTRY.keys())

