# Output Parsers Guide

## Overview

Output parsers convert unstructured LLM responses into structured data.

Why parsers?
- **Local LLMs don't support tool calling** - Let them respond naturally, then parse
- **Structured extraction** - Get predictable, typed output
- **Fallback handling** - Graceful degradation when parsing fails
- **Confidence scoring** - Know how confident the parser is

## Available Parsers

### ClassificationParser

Extract a single category from fixed list.

```python
from shared.output_parsers import ClassificationParser

parser = ClassificationParser(
    categories=["safe", "low_risk", "medium_risk", "high_risk", "critical"],
    case_insensitive=True,
    confidence_threshold=0.5
)

result = parser.parse("""
Content Analysis: This is clearly CRITICAL risk
Reasoning: Explicit harmful content detected
""")

print(result.parsed)  # {"category": "critical"}
print(result.confidence)  # 1.0 (exact word match)
```

**Use cases:**
- Content moderation (safe/unsafe/review)
- Risk classification (low/medium/high/critical)
- Routing decisions (route_a/route_b/escalate)

### SentimentParser

Analyze sentiment and optional score.

```python
from shared.output_parsers import SentimentParser

parser = SentimentParser()

result = parser.parse("""
This product is amazing! I absolutely love it.
Sentiment Score: 0.92
""")

print(result.parsed)
# {"sentiment": "positive", "score": 0.92}

print(result.confidence)  # Based on keyword matches
```

**Use cases:**
- Customer feedback analysis
- Review sentiment extraction
- Emotional tone detection

### ExtractionParser

Extract multiple fields using regex patterns.

```python
from shared.output_parsers import ExtractionParser

parser = ExtractionParser(
    fields={
        "name": r"Name:\s*([^,]+)",
        "age": r"Age:\s*(\d+)",
        "city": r"City:\s*([^,\n]+)",
    },
    required=["name"],  # Fail if missing
    fallback=True  # Return raw string on error
)

result = parser.parse("""
Name: John Smith
Age: 30
City: Dallas
""")

print(result.parsed)
# {"name": "John Smith", "age": "30", "city": "Dallas"}
```

**Use cases:**
- Form data extraction
- Entity extraction
- Citation extraction
- Structured data parsing

### BooleanParser

Determine true/false from text.

```python
from shared.output_parsers import BooleanParser

parser = BooleanParser()

result = parser.parse("""
Should we proceed? YES, definitely.
Confidence: high
""")

print(result.parsed)  # {"value": True}
```

**Use cases:**
- Approval/rejection decisions
- Content filtering (pass/reject)
- Accessibility decisions
- Workflow branching

### RegexParser

Generic parser with custom patterns.

```python
from shared.output_parsers import RegexParser

parser = RegexParser(
    patterns={
        "risk_level": r"(safe|low|medium|high|critical)",
        "confidence": r"(\d+)%",
        "recommendation": r"Recommend:\s*(.+)(?:\n|$)",
    }
)

result = parser.parse("""
Risk Assessment:
Level: medium
Confidence: 85%
Recommend: Manual review required
""")

print(result.parsed)
# {"risk_level": "medium", "confidence": "85", "recommendation": "Manual review..."}
```

**Use cases:**
- Custom extraction patterns
- Multiple field extraction
- Complex format parsing

## ParserResult

All parsers return `ParserResult`:

```python
from shared.output_parsers import ParserResult

# Result structure
result = ParserResult(
    success=True,                      # Parse succeeded
    parsed={"category": "safe"},      # Extracted data
    raw="Original text here",          # Original input
    error=None,                        # Error message if failed
    confidence=0.95                    # Confidence 0.0-1.0
)

# Usage
if result.success:
    print(f"Parsed: {result.parsed}")
    print(f"Confidence: {result.confidence}")
else:
    print(f"Error: {result.error}")
    if result.parsed:  # Fallback value
        print(f"Fallback: {result.parsed}")
```

## Error Handling & Fallback

### With Fallback (Default)

```python
parser = ClassificationParser(
    categories=["yes", "no"],
    fallback=True  # Return raw string on error
)

result = parser.parse("maybe")  # Doesn't match categories

print(result.success)  # True (fallback is "successful")
print(result.parsed)   # "maybe" (raw string)
print(result.confidence)  # 0.0 (low confidence)
print(result.error)    # Error message explaining what happened
```

### Without Fallback

```python
parser = ClassificationParser(
    categories=["yes", "no"],
    fallback=False  # Fail hard
)

result = parser.parse("maybe")

print(result.success)  # False
print(result.parsed)   # None
print(result.error)    # Error message
```

## Using Parsers in Examples

### In execute() Method

```python
class MyExample(StandardExample):
    def __init__(self):
        super().__init__(
            cache_backend="memory",
            output_parser="classification",
            parser_config={
                "categories": ["safe", "unsafe", "review"],
                "confidence_threshold": 0.7
            }
        )
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Execute graph and get output
        model_output = "This content is UNSAFE and should be rejected"
        
        # Parse output
        parsed_result = self.parser.parse(model_output)
        
        if parsed_result.success:
            # Use parsed data
            category = parsed_result.parsed["category"]
            confidence = parsed_result.confidence
            return {
                "category": category,
                "confidence": confidence,
                "raw_output": model_output
            }
        else:
            # Handle error
            return {
                "error": parsed_result.error,
                "raw_output": model_output
            }
```

## Custom Parser

Extend `OutputParser` for custom logic:

```python
from shared.output_parsers import OutputParser, ParserResult
import re

class CustomParser(OutputParser):
    """Parse custom format."""
    
    def parse(self, text: str) -> ParserResult:
        if not text:
            return self._handle_error(text, "Empty input")
        
        # Custom parsing logic
        match = re.search(r"Value: (\d+)", text)
        
        if match:
            return ParserResult(
                success=True,
                parsed={"value": int(match.group(1))},
                raw=text,
                confidence=0.95
            )
        else:
            return self._handle_error(text, "Pattern not found")
```

## Testing Parsers

```python
import pytest
from shared.output_parsers import ClassificationParser

def test_classification_parser():
    parser = ClassificationParser(categories=["yes", "no"])
    
    # Test exact match
    result = parser.parse("The answer is YES")
    assert result.success
    assert result.parsed["category"] == "yes"
    assert result.confidence == 1.0
    
    # Test no match
    result = parser.parse("maybe")
    assert result.success  # Fallback enabled
    assert result.confidence < 1.0
    
    # Test case insensitive
    result = parser.parse("yes please")
    assert result.parsed["category"] == "yes"
```

## Performance Considerations

- **Regex parsing**: Fast, good for structured data
- **Keyword matching**: Very fast, works for classifications
- **Fallback enabled**: Slightly slower (extra checks)
- **Complex patterns**: Can be slow, consider caching

## Common Patterns

### Classification + Routing

```python
parser = ClassificationParser(
    categories=["route_a", "route_b", "escalate"],
    confidence_threshold=0.8
)

result = parser.parse(model_output)
if result.confidence >= 0.9:
    route = result.parsed["category"]
else:
    route = "escalate"  # Low confidence -> escalate
```

### Extraction + Validation

```python
parser = ExtractionParser(
    fields={"email": r"([\w.-]+@[\w.-]+)"},
    required=["email"]
)

result = parser.parse(model_output)
if result.success and "@" in result.parsed["email"]:
    # Valid email extracted
    send_to(result.parsed["email"])
```

### Sentiment + Thresholding

```python
parser = SentimentParser()
result = parser.parse(model_output)

if result.success:
    sentiment = result.parsed["sentiment"]
    score = result.parsed.get("score", 0.5)
    
    if sentiment == "negative" and score < 0.3:
        # Very negative - escalate
        escalate()
```

## Troubleshooting

### Parser not matching

1. Check case sensitivity
2. Look for extra whitespace
3. Verify regex pattern with test tools
4. Check fallback behavior

### Low confidence scores

1. Adjust confidence_threshold
2. Improve keywords/patterns
3. Use RegexParser for more specific extraction

### Slow parsing

1. Profile with complex patterns
2. Cache compiled patterns (RegexParser does this)
3. Use simpler patterns if possible

## Next Steps

- Explore other parsers (Pydantic validation, JSON schema)
- Create domain-specific parsers
- Integrate with vector embeddings for semantic parsing
