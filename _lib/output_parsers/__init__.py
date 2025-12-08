"""
Output Parsers Module - Backward Compatibility Shim

⚠️ DEPRECATED: This module is deprecated and will be removed in Q2 2026.
Output Parsers have been promoted to universal-agent-nexus@3.1.0

Please update your imports:

Old (deprecated):
    from _lib.output_parsers import get_parser

New (recommended):
    from universal_agent_nexus.output_parsers import get_parser
"""

import warnings

warnings.warn(
    "_lib.output_parsers is deprecated. "
    "Use 'from universal_agent_nexus.output_parsers import ...' instead. "
    "This shim will be removed in Q2 2026. "
    "Requires universal-agent-nexus>=3.1.0",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from promoted package
try:
    from universal_agent_nexus.output_parsers import (
        OutputParser,
        ParserResult,
        ClassificationParser,
        SentimentParser,
        ExtractionParser,
        BooleanParser,
        RegexParser,
        get_parser,
    )
except ImportError:
    raise ImportError(
        "universal-agent-nexus>=3.1.0 is required. "
        "Install with: pip install 'universal-agent-nexus>=3.1.0'"
    )

__all__ = [
    "OutputParser",
    "ParserResult",
    "ClassificationParser",
    "SentimentParser",
    "ExtractionParser",
    "BooleanParser",
    "RegexParser",
    "get_parser",
]
