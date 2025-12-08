"""
⚠️ DEPRECATED: This module has been moved to _lib/

For backward compatibility, imports are redirected to _lib.
Please update your imports to use _lib directly.

Old: from shared import NexusRuntime
New: from _lib.runtime import NexusRuntime
"""

import sys
from pathlib import Path

# Redirect imports to _lib
_lib_path = Path(__file__).parent.parent / "_lib"
if _lib_path.exists() and str(_lib_path) not in sys.path:
    sys.path.insert(0, str(_lib_path.parent))

# Re-export from _lib for backward compatibility
try:
    from _lib.runtime import NexusRuntime, StandardExample, ResultExtractor
    from _lib.cache_fabric import CacheFabric, create_cache_fabric
    from _lib.output_parsers import get_parser, OutputParser
    from _lib.tools import ModelConfig, setup_observability
    
    __all__ = [
        "NexusRuntime",
        "StandardExample",
        "ResultExtractor",
        "CacheFabric",
        "create_cache_fabric",
        "get_parser",
        "OutputParser",
        "ModelConfig",
        "setup_observability",
    ]
except ImportError as e:
    import warnings
    warnings.warn(
        f"Failed to import from _lib: {e}. "
        "Please update imports to use _lib directly.",
        DeprecationWarning
    )
    __all__ = []
