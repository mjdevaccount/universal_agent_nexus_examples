"""
Common Workflow Nodes

Pre-built node implementations for the December 2025 pattern:
  Intelligence → Extraction → Validation

These nodes are designed for reuse across all examples.
Each node has a single responsibility (SOLID).

NODE 1: IntelligenceNode
  - Purpose: Free-form reasoning and analysis
  - Temperature: 0.7-0.8 (creative)
  - Output: Unstructured text
  - For: Deep reasoning before extraction

NODE 2: ExtractionNode
  - Purpose: Convert unstructured text to JSON
  - Temperature: 0.1 (deterministic)
  - Output: JSON matching Pydantic schema
  - For: Structured output from reasoning

NODE 3: ValidationNode
  - Purpose: Semantic validation + repair
  - Temperature: 0.0 (strict)
  - Output: Validated data or repair suggestions
  - For: Quality gates before downstream use

Key Design:
  - Dependencies injected (LLM, schema, rules)
  - Error handling with repair strategies
  - Observability (warnings, metrics)
"""

import json
import re
import logging
from typing import (
    Any, Dict, List, Optional, Type, Callable, Tuple
)
from datetime import datetime
from abc import abstractmethod
from enum import Enum

from pydantic import BaseModel, ValidationError, Field as PydanticField
from langchain_core.messages import HumanMessage, BaseMessage

from shared.workflows.nodes import (
    BaseNode,
    NodeExecutionError,
    NodeStatus,
)

logger = logging.getLogger(__name__)


class ValidationMode(str, Enum):
    """
    Validation mode for ValidationNode.
    
    STRICT: Fail fast on Pydantic error (no automatic repair)
    RETRY: Use LLM repair loop with validation error feedback
    BEST_EFFORT: Allow local defaults/fixes (for non-critical pipelines)
    """
    STRICT = "strict"
    RETRY = "retry"
    BEST_EFFORT = "best_effort"


class IntelligenceNode(BaseNode):
    """
    Free-form reasoning node.
    
    Single Responsibility: Generate thoughtful analysis without structure constraints.
    
    Temperature: 0.7-0.8 (creative reasoning, explore alternatives)
    
    Input Requirements:
        - State must have all keys in `required_state_keys`
    
    Output:
        - Adds `analysis` key to state with raw text response
        - Updates `messages` with conversation history
    
    Design Pattern: Strategy
        Different reasoning templates can be swapped without changing node logic.
    
    Example:
        intelligence = IntelligenceNode(
            llm=reasoning_llm,  # High-temperature LLM
            prompt_template="Analyze: {event}\nContext: {scenario}",
            required_state_keys=["event", "scenario"],
            name="reasoning"
        )
        
        state = await intelligence.execute({
            "event": {"name": "AI breakthrough"},
            "scenario": "market impact analysis"
        })
        # state["analysis"] = "AI adoption will follow S-curve..."
    """
    
    def __init__(
        self,
        llm: Any,  # LangChain ChatModel
        prompt_template: str,
        required_state_keys: List[str] = None,
        name: str = "intelligence",
        description: str = "Free-form reasoning phase",
    ):
        """
        Initialize intelligence node.
        
        Args:
            llm: LangChain ChatModel (should have high temperature)
            prompt_template: Template with {key} placeholders for state values
            required_state_keys: Keys that must exist in state
            name: Node identifier
            description: Human-readable description
        
        Note:
            LLM should be configured with temperature=0.7-0.8 for creative reasoning.
        """
        super().__init__(name=name, description=description)
        self.llm = llm
        self.prompt_template = prompt_template
        self.required_state_keys = required_state_keys or []
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute intelligence analysis.
        
        Process:
            1. Format prompt with state values
            2. Invoke LLM (high temperature for reasoning)
            3. Capture response as analysis
            4. Update message history
        
        Args:
            state: Must have all keys in required_state_keys
        
        Returns:
            State with added keys:
                - analysis: LLM response text
                - messages: Updated conversation history
        
        Raises:
            NodeExecutionError: If LLM fails or validation fails
        """
        start_time = datetime.now()
        self.metrics.status = NodeStatus.RUNNING
        self.metrics.input_keys = self.required_state_keys
        
        try:
            # Validate input
            if not self.validate_input(state):
                missing = [k for k in self.required_state_keys if k not in state]
                raise NodeExecutionError(
                    node_name=self.name,
                    reason=f"Missing required keys: {missing}",
                    state=state
                )
            
            # Format prompt
            format_dict = {k: state.get(k) for k in self.required_state_keys}
            prompt_text = self.prompt_template.format(**format_dict)
            
            logger.info(f"[{self.name}] Invoking LLM for reasoning")
            
            # Invoke LLM (get existing messages or start fresh)
            messages = state.get("messages", [])
            messages.append(HumanMessage(content=prompt_text))
            
            response = await self.llm.ainvoke(messages)
            
            # Store results
            state["analysis"] = response.content
            state["messages"] = messages + [response]
            
            # Update metrics
            self.metrics.output_keys = ["analysis", "messages"]
            self.metrics.status = NodeStatus.SUCCESS
            
            logger.info(
                f"[{self.name}] Analysis complete "
                f"({len(response.content)} chars)"
            )
            
            return state
        
        except Exception as e:
            self.metrics.status = NodeStatus.FAILED
            self.metrics.error_message = str(e)
            raise await self.on_error(e, state)
        
        finally:
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics.duration_ms = elapsed
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        """
        Validate that state has all required keys.
        
        Args:
            state: Current workflow state
        
        Returns:
            True if all required keys present
        """
        return all(k in state for k in self.required_state_keys)


class ExtractionNode(BaseNode):
    """
    Structured output extraction node.
    
    Single Responsibility: Extract JSON from text and repair if needed.
    
    Temperature: 0.1 (deterministic, consistent)
    
    Input Requirements:
        - state["analysis"]: Unstructured text from intelligence node
    
    Output:
        - Adds `extracted` key with parsed/repaired JSON as dict
        - Adds `extraction_warnings` if repairs were needed
    
    Repair Strategies (applied in order):
        1. Direct JSON parse
        2. Incremental repair (close braces, remove trailing commas)
        3. LLM repair (ask model to fix JSON)
        4. Regex extraction (pull out key fields manually)
    
    Design Pattern: Strategy
        Multiple repair strategies tried in sequence.
        Different strategies can be enabled/disabled.
    
    Example:
        extraction = ExtractionNode(
            llm=extraction_llm,  # Low-temperature LLM
            prompt_template="Extract JSON from: {analysis}\nSchema: {schema}",
            output_schema=AdoptionPrediction,
            name="extraction"
        )
        
        state = await extraction.execute({"analysis": "Market will grow..."})
        # state["extracted"] = {
        #     "adoption_timeline_months": 18,
        #     "disruption_score": 8.5,
        #     ...
        # }
    """
    
    def __init__(
        self,
        llm: Any,  # LangChain ChatModel with low temperature
        prompt_template: str,
        output_schema: Type[BaseModel],  # Pydantic model
        json_repair_strategies: List[str] = None,
        name: str = "extraction",
        description: str = "Extract structured data from analysis",
    ):
        """
        Initialize extraction node.
        
        Args:
            llm: LangChain ChatModel (should have temperature=0.1)
            prompt_template: Template for extraction prompt
            output_schema: Pydantic BaseModel defining expected JSON structure
            json_repair_strategies: List of repair strategies to use
                Options: ["incremental_repair", "llm_repair", "regex_fallback"]
            name: Node identifier
            description: Human-readable description
        """
        super().__init__(name=name, description=description)
        self.llm = llm
        self.prompt_template = prompt_template
        self.output_schema = output_schema
        self.json_repair_strategies = json_repair_strategies or [
            "incremental_repair",
            "llm_repair",
            "regex_fallback",
        ]
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute extraction.
        
        Process:
            1. Format prompt with analysis text
            2. Invoke LLM for JSON extraction
            3. Parse JSON (with repair if needed)
            4. Return extracted data
        
        Args:
            state: Must have "analysis" key
        
        Returns:
            State with added keys:
                - extracted: Parsed JSON dict
                - extraction_warnings: List of warnings (if repairs applied)
        
        Raises:
            NodeExecutionError: If extraction fails
        """
        start_time = datetime.now()
        self.metrics.status = NodeStatus.RUNNING
        self.metrics.input_keys = ["analysis"]
        
        try:
            if "analysis" not in state:
                raise NodeExecutionError(
                    node_name=self.name,
                    reason="Missing 'analysis' from intelligence node",
                    state=state
                )
            
            # Format prompt
            schema_str = self.output_schema.__name__
            prompt_text = self.prompt_template.format(
                analysis=state["analysis"][:1500],  # Limit context
                schema=schema_str
            )
            
            logger.info(f"[{self.name}] Invoking LLM for extraction")
            
            # December 2025 Standard: Use with_structured_output() when available
            # This provides automatic parsing, validation, and retry logic
            warnings = []
            data = None
            
            # Try with_structured_output() first (December 2025 best practice)
            try:
                if hasattr(self.llm, 'with_structured_output'):
                    structured_llm = self.llm.with_structured_output(self.output_schema)
                    validated_model = await structured_llm.ainvoke(
                        [HumanMessage(content=prompt_text)]
                    )
                    # Convert Pydantic model to dict
                    data = validated_model.model_dump() if hasattr(validated_model, 'model_dump') else dict(validated_model)
                    logger.info(f"[{self.name}] Structured output extraction successful (with_structured_output)")
                else:
                    # Fallback: Manual parsing with repair strategies
                    raise AttributeError("LLM doesn't support with_structured_output")
            except (AttributeError, Exception) as e:
                # Fallback to manual parsing with repair strategies
                logger.info(f"[{self.name}] Using manual parsing (with_structured_output not available: {e})")
                
                # Invoke LLM manually
                response = await self.llm.ainvoke(
                    [HumanMessage(content=prompt_text)]
                )
                json_text = response.content
                
                # Strategy 1: Direct parse
                try:
                    data = json.loads(json_text)
                    logger.info(f"[{self.name}] Direct JSON parse successful")
                except json.JSONDecodeError as e:
                    logger.warning(f"[{self.name}] Direct parse failed: {e}")
                    
                    # Strategy 2: Incremental repair
                    if "incremental_repair" in self.json_repair_strategies:
                        try:
                            json_text = self._repair_json_incremental(json_text)
                            data = json.loads(json_text)
                            warnings.append("JSON required incremental repair")
                            logger.info(f"[{self.name}] Incremental repair successful")
                        except Exception as e2:
                            logger.warning(f"[{self.name}] Incremental repair failed: {e2}")
                    
                    # Strategy 3: LLM repair
                    if data is None and "llm_repair" in self.json_repair_strategies:
                        try:
                            repaired_text = await self._repair_json_with_llm(
                                json_text
                            )
                            data = json.loads(repaired_text)
                            warnings.append("JSON required LLM repair")
                            logger.info(f"[{self.name}] LLM repair successful")
                        except Exception as e3:
                            logger.warning(f"[{self.name}] LLM repair failed: {e3}")
                    
                    # Strategy 4: Regex extraction
                    if data is None and "regex_fallback" in self.json_repair_strategies:
                        try:
                            data = self._extract_with_regex(
                                json_text,
                                state["analysis"]
                            )
                            warnings.append("JSON required regex extraction")
                            logger.info(
                                f"[{self.name}] Regex extraction successful "
                                f"({len(data)} fields: {list(data.keys())})"
                            )
                        except Exception as e4:
                            logger.warning(f"[{self.name}] Regex extraction failed: {e4}")
                    
                    if data is None:
                        raise NodeExecutionError(
                            node_name=self.name,
                            reason="All JSON repair strategies failed",
                            state=state
                        )
            
            # Store results
            state["extracted"] = data
            if warnings:
                state["extraction_warnings"] = warnings
                self.metrics.warnings = warnings
            
            # Update metrics
            self.metrics.output_keys = ["extracted"]
            self.metrics.status = NodeStatus.SUCCESS
            
            logger.info(
                f"[{self.name}] Extraction complete "
                f"({len(data)} fields)" + (
                    f" with {len(warnings)} repairs" if warnings else ""
                )
            )
            
            return state
        
        except Exception as e:
            self.metrics.status = NodeStatus.FAILED
            self.metrics.error_message = str(e)
            raise await self.on_error(e, state)
        
        finally:
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics.duration_ms = elapsed
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        return "analysis" in state
    
    def _repair_json_incremental(self, json_str: str, max_attempts: int = 3) -> str:
        """
        Repair JSON by closing unclosed structures and removing trailing commas.
        
        Strategies:
            1. Close unclosed braces/brackets
            2. Remove trailing commas before closing
            3. Quote unquoted keys
        """
        for attempt in range(max_attempts):
            try:
                return json_str  # Success
            except:
                if attempt == 0:
                    # Close unclosed structures
                    missing_braces = json_str.count('{') - json_str.count('}')
                    missing_brackets = json_str.count('[') - json_str.count(']')
                    json_str = json_str + ('}' * missing_braces) + (']' * missing_brackets)
                elif attempt == 1:
                    # Remove trailing commas
                    json_str = json_str.replace(',}', '}').replace(',]', ']')
                elif attempt == 2:
                    # Quote unquoted keys
                    json_str = re.sub(
                        r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:',
                        r'\1"\2":',
                        json_str
                    )
        
        return json_str
    
    async def _repair_json_with_llm(self, broken_json: str) -> str:
        """
        Ask LLM to fix broken JSON.
        """
        repair_prompt = (
            f"Fix this broken JSON and return ONLY valid JSON:\n\n"
            f"{broken_json[:500]}\n\n"
            f"Return the corrected JSON (no markdown, no explanation):"
        )
        
        response = await self.llm.ainvoke(
            [HumanMessage(content=repair_prompt)]
        )
        return response.content
    
    def _extract_with_regex(self, json_text: str, analysis_text: str) -> Dict[str, Any]:
        """
        Last resort: extract key fields using regex patterns.
        
        This is a fallback for when JSON parsing completely fails.
        Returns partial data based on what can be extracted.
        Uses the Pydantic schema to determine what fields to extract.
        """
        import re
        from pydantic import Field
        
        data = {}
        # Search in both original and lowercased versions
        combined_text = (json_text + " " + analysis_text)
        combined_text_lower = combined_text.lower()
        
        # Get schema fields from Pydantic model
        schema_fields = {}
        if hasattr(self.output_schema, 'model_fields'):
            schema_fields = self.output_schema.model_fields
        elif hasattr(self.output_schema, '__fields__'):
            schema_fields = self.output_schema.__fields__
        
        # Extract each field from schema
        for field_name, field_info in schema_fields.items():
            # Get field type
            field_type = None
            if hasattr(field_info, 'annotation'):
                field_type = field_info.annotation
            elif hasattr(field_info, 'type_'):
                field_type = field_info.type_
            
            # Try to extract based on field name and type
            field_name_alt = field_name.replace("_", r"\s+")
            if field_type == int or (hasattr(field_type, '__origin__') and field_type.__origin__ is int):
                # Integer field - try both original and lowercased
                pattern = rf'(?:{field_name}|{field_name_alt})[^:]*[:\s]*(\d+)'
                match = re.search(pattern, combined_text, re.IGNORECASE) or re.search(pattern, combined_text_lower, re.IGNORECASE)
                if match:
                    try:
                        data[field_name] = int(match.group(1))
                    except (ValueError, IndexError):
                        pass
            elif field_type == float or (hasattr(field_type, '__origin__') and field_type.__origin__ is float):
                # Float field - try both original and lowercased
                pattern = rf'(?:{field_name}|{field_name_alt})[^:]*[:\s]*(\d+\.?\d*)'
                match = re.search(pattern, combined_text, re.IGNORECASE) or re.search(pattern, combined_text_lower, re.IGNORECASE)
                if match:
                    try:
                        data[field_name] = float(match.group(1))
                    except (ValueError, IndexError):
                        pass
            else:
                # String field - try to extract quoted strings or enum values
                # Look for field name followed by colon and quoted value
                patterns = [
                    rf'{field_name}[^:]*[:\s]*["\']?([^"\',\s}}]+)["\']?',
                    rf'["\']?{field_name}["\']?\s*:\s*["\']?([^"\',\s}}]+)["\']?',
                ]
                for pattern in patterns:
                    match = re.search(pattern, combined_text, re.IGNORECASE) or re.search(pattern, combined_text_lower, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        if value and len(value) < 100:  # Reasonable string length
                            data[field_name] = value
                            break
        
        # Fallback: Try common patterns for known field types
        # Try these even if we got some data, to fill in missing fields
        fallback_patterns = {
            "severity_level": [
                r'severity[_-]?level[^:]*[:\s]*["\']?(safe|low|medium|high|critical)["\']?',
                r'["\']?severity["\']?\s*:\s*["\']?(safe|low|medium|high|critical)["\']?',
                r'(?:severity|level)[^:]*[:\s]*["\']?(safe|low|medium|high|critical)["\']?',
            ],
            "risk_category": [
                r'risk[_-]?category[^:]*[:\s]*["\']?([^"\',\s}}]+)["\']?',
                r'["\']?risk[_-]?category["\']?\s*:\s*["\']?([^"\',\s}}]+)["\']?',
                r'(?:risk|category)[^:]*[:\s]*["\']?([^"\',\s}}]+)["\']?',
            ],
            "confidence": [
                r'confidence[^:]*[:\s]*(\d+\.?\d*)',
                r'["\']?confidence["\']?\s*:\s*(\d+\.?\d*)',
                r'confidence[^:]*[:\s]*(\d+\.?\d*)',
            ],
            "adoption_timeline_months": [
                r'(?:adoption|timeline|months)[^:]*[:\s]*(\d+)',
            ],
            "disruption_score": [
                r'(?:disruption|score)[^:]*[:\s]*(\d+\.?\d*)',
            ],
        }
        
        for key, patterns in fallback_patterns.items():
            if key in schema_fields and key not in data:  # Only extract if field exists and not already found
                for pattern in patterns:
                    # Try both original and lowercased text
                    match = re.search(pattern, combined_text, re.IGNORECASE) or re.search(pattern, combined_text_lower, re.IGNORECASE)
                    if match:
                        try:
                            value = match.group(1)
                            if key == "confidence":
                                data[key] = float(value)
                            elif key == "adoption_timeline_months":
                                data[key] = int(value)
                            elif key == "disruption_score":
                                data[key] = float(value)
                            else:
                                data[key] = value.strip('"\'')
                            break  # Found it, move to next field
                        except (ValueError, IndexError):
                            continue
        
        # If we have some data but not all required fields, try to provide defaults
        if data and len(data) < len(schema_fields):
            # Try to infer missing fields from context
            for field_name in schema_fields:
                if field_name not in data:
                    # Try one more time with a very broad pattern
                    broad_pattern = rf'{field_name}[^:]*[:\s]*["\']?([^"\',\n}}]+)["\']?'
                    match = re.search(broad_pattern, combined_text, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        if value and len(value) < 100:
                            # Try to infer type
                            field_info = schema_fields[field_name]
                            field_type = None
                            if hasattr(field_info, 'annotation'):
                                field_type = field_info.annotation
                            elif hasattr(field_info, 'type_'):
                                field_type = field_info.type_
                            
                            try:
                                if field_type == float or (hasattr(field_type, '__origin__') and field_type.__origin__ is float):
                                    data[field_name] = float(value)
                                elif field_type == int or (hasattr(field_type, '__origin__') and field_type.__origin__ is int):
                                    data[field_name] = int(value)
                                else:
                                    data[field_name] = value
                            except (ValueError, TypeError):
                                pass
        
        return data if data else {"extraction_status": "partial"}
    
    async def on_error(self, error: Exception, state: Dict[str, Any]) -> Exception:
        """
        Custom error handling for extraction failures.
        
        Log additional context and re-raise.
        """
        logger.error(
            f"[{self.name}] Extraction failed\n"
            f"Analysis length: {len(state.get('analysis', ''))}\n"
            f"Error: {error}"
        )
        return error


class ValidationNode(BaseNode):
    """
    Semantic validation and repair node (December 2025 Pattern).
    
    Single Responsibility: Validate extracted data with configurable repair strategies.
    
    Temperature: 0.0 (strict enforcement) or LLM temperature for repair loops
    
    Input Requirements:
        - state["extracted"]: Dict from extraction node
    
    Output:
        - Adds `validated` key with validated/repaired data
        - Adds `validation_warnings` list
        - Adds `validation_metadata` dict with mode, outcome, repairs
    
    Validation Modes (December 2025 Best Practice):
        1. STRICT: Fail fast on Pydantic error (no automatic repair)
           - Use for: Critical pipelines (finance, healthcare, legal)
           - Behavior: Raises NodeExecutionError on validation failure
        
        2. RETRY: LLM repair loop with validation error feedback
           - Use for: Production pipelines needing semantic repair
           - Behavior: Re-prompts LLM with Pydantic errors, retries up to max_retries
           - Pattern: Matches BentoML, Haystack, Instructor-style validation
        
        3. BEST_EFFORT: Local defaults/fixes (mechanical repairs only)
           - Use for: Analytics, internal dashboards, non-critical contexts
           - Behavior: Applies safe type coercion, uses schema defaults, minimal guessing
    
    Validation Layers:
        1. Pydantic schema validation (types, constraints, enums)
        2. Custom semantic rules (business logic via validation_rules)
        3. Schema-driven repair (uses Field(ge=, le=, default=) from Pydantic)
    
    Design Pattern: Strategy
        Different validation modes can be swapped without changing node logic.
        Domain semantics live in Pydantic schemas and validation_rules, not in the node.
    
    Example (STRICT mode - recommended for production):
        validation = ValidationNode(
            output_schema=AdoptionPrediction,
            mode=ValidationMode.STRICT,
            validation_rules={
                "timeline_sanity": lambda x: 1 <= x["adoption_timeline_months"] <= 60,
            }
        )
    
    Example (RETRY mode - with LLM repair):
        validation = ValidationNode(
            output_schema=AdoptionPrediction,
            mode=ValidationMode.RETRY,
            llm=repair_llm,  # Low-temperature LLM for repair
            max_retries=2,
        )
    
    Example (BEST_EFFORT mode - for analytics):
        validation = ValidationNode(
            output_schema=AdoptionPrediction,
            mode=ValidationMode.BEST_EFFORT,
        )
    """
    
    def __init__(
        self,
        output_schema: Type[BaseModel],
        validation_rules: Dict[str, Callable] = None,
        mode: ValidationMode = None,  # None for backward compatibility
        repair_on_fail: bool = None,  # DEPRECATED: Use mode instead
        llm: Any = None,  # Optional LLM for RETRY mode repair loop
        max_retries: int = 2,  # Max retries for RETRY mode
        name: str = "validation",
        description: str = "Validate and repair extracted data",
    ):
        """
        Initialize validation node.
        
        Args:
            output_schema: Pydantic model to validate against
                Should use Field(ge=, le=, default=) for constraints
            validation_rules: Dict of {rule_name: rule_func}
                where rule_func(data) returns True if valid, raises/returns False otherwise
            mode: ValidationMode enum (STRICT, RETRY, BEST_EFFORT)
                If None, inferred from repair_on_fail for backward compatibility
            repair_on_fail: DEPRECATED - Use mode instead
                If True, maps to BEST_EFFORT mode
                If False, maps to STRICT mode
            llm: Optional LangChain ChatModel for RETRY mode repair loop
                Required if mode=ValidationMode.RETRY
            max_retries: Maximum retry attempts for RETRY mode (default: 2)
            name: Node identifier
            description: Human-readable description
        
        Example of validation_rules:
            {
                "timeline_bounds": lambda x: 1 <= x["adoption_timeline_months"] <= 60,
                "disruption_positive": lambda x: x["disruption_score"] >= 0,
            }
        
        Note:
            For STRICT mode, validation failures raise NodeExecutionError immediately.
            For RETRY mode, validation errors are fed back to LLM for repair.
            For BEST_EFFORT mode, only safe mechanical repairs are applied.
        """
        super().__init__(name=name, description=description)
        self.output_schema = output_schema
        self.validation_rules = validation_rules or {}
        
        # Backward compatibility: map repair_on_fail to mode
        if mode is None:
            if repair_on_fail is not None:
                # Legacy parameter provided
                logger.warning(
                    f"[{self.name}] repair_on_fail parameter is deprecated. "
                    f"Use mode=ValidationMode.BEST_EFFORT or ValidationMode.STRICT instead."
                )
                self.mode = ValidationMode.BEST_EFFORT if repair_on_fail else ValidationMode.STRICT
            else:
                # Default to STRICT for new code
                self.mode = ValidationMode.STRICT
        else:
            self.mode = mode
            if repair_on_fail is not None:
                logger.warning(
                    f"[{self.name}] repair_on_fail parameter is ignored when mode is provided."
                )
        
        self.llm = llm
        self.max_retries = max_retries
        
        # Validate mode requirements
        if self.mode == ValidationMode.RETRY and llm is None:
            logger.warning(
                f"[{self.name}] RETRY mode requires llm parameter. "
                "Falling back to STRICT mode behavior."
            )
            self.mode = ValidationMode.STRICT
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute validation based on configured mode.
        
        Process (varies by mode):
            STRICT:
                1. Validate with Pydantic schema
                2. Apply semantic rules
                3. Raise on any failure
        
            RETRY:
                1. Validate with Pydantic schema
                2. If fails, re-prompt LLM with error details
                3. Retry validation up to max_retries
                4. Apply semantic rules
        
            BEST_EFFORT:
                1. Validate with Pydantic schema
                2. If fails, apply safe mechanical repairs
                3. Use schema defaults for missing fields
                4. Apply semantic rules
        
        Args:
            state: Must have "extracted" key
        
        Returns:
            State with added keys:
                - validated: Validated/repaired data dict
                - validation_warnings: List of warnings/repairs applied
                - validation_metadata: Dict with mode, outcome, repairs
        
        Raises:
            NodeExecutionError: If validation fails (STRICT mode) or all retries exhausted (RETRY mode)
        """
        start_time = datetime.now()
        self.metrics.status = NodeStatus.RUNNING
        self.metrics.input_keys = ["extracted"]
        
        try:
            if "extracted" not in state:
                raise NodeExecutionError(
                    node_name=self.name,
                    reason="Missing 'extracted' from extraction node",
                    state=state
                )
            
            # Store original data for audit trail
            original_data = state["extracted"].copy()
            data = original_data.copy()
            warnings = []
            repairs = {}  # Track per-field repairs
            validation_outcome = "strict_pass"
            
            # Clean extraction artifacts
            if "extraction_status" in data and len(data) == 1:
                warnings.append("Extraction returned only status marker, using schema defaults")
                data = {}
            
            # Remove undefined/null values and status markers
            data = {k: v for k, v in data.items() 
                   if k != "extraction_status" and v is not None 
                   and not (hasattr(v, '__class__') and 'Undefined' in str(type(v)))}
            
            # Layer 1: Pydantic validation with mode-specific repair
            validated = None
            validation_error = None
            
            try:
                validated = self.output_schema(**data)
                logger.info(f"[{self.name}] Schema validation passed (mode: {self.mode.value})")
            except ValidationError as e:
                validation_error = e
                logger.info(f"[{self.name}] Schema validation failed: {e.error_count()} errors")
                
                # Mode-specific handling
                if self.mode == ValidationMode.STRICT:
                    # STRICT: Fail immediately
                    raise NodeExecutionError(
                        node_name=self.name,
                        reason=f"Schema validation failed (STRICT mode): {self._format_validation_errors(e)}",
                        state=state
                    )
                
                elif self.mode == ValidationMode.RETRY:
                    # RETRY: LLM repair loop
                    if self.llm is None:
                        raise NodeExecutionError(
                            node_name=self.name,
                            reason="RETRY mode requires llm parameter",
                            state=state
                        )
                    
                    validation_outcome = "retry_attempt"
                    for attempt in range(self.max_retries):
                        logger.info(f"[{self.name}] LLM repair attempt {attempt + 1}/{self.max_retries}")
                        try:
                            repaired_data = await self._repair_with_llm(data, e)
                            validated = self.output_schema(**repaired_data)
                            validation_outcome = f"repaired_after_{attempt + 1}_retries"
                            warnings.append(f"Data repaired via LLM after {attempt + 1} attempt(s)")
                            data = repaired_data
                            logger.info(f"[{self.name}] Validation passed after LLM repair")
                            break
                        except ValidationError as e2:
                            if attempt == self.max_retries - 1:
                                # Last attempt failed
                                raise NodeExecutionError(
                                    node_name=self.name,
                                    reason=f"Validation failed after {self.max_retries} LLM repair attempts: {self._format_validation_errors(e2)}",
                                    state=state
                                )
                            e = e2  # Try again with new errors
                
                elif self.mode == ValidationMode.BEST_EFFORT:
                    # BEST_EFFORT: Mechanical repairs only
                    validation_outcome = "best_effort_repair"
                    warnings.append(f"Schema validation failed: {e.error_count()} errors, attempting best-effort repair")
                    logger.info(f"[{self.name}] Attempting best-effort repair")
                    
                    data, repairs = self._repair_fields_safe(data, e)
                    logger.info(f"[{self.name}] After repair, data keys: {list(data.keys())}, repairs: {list(repairs.keys())}")
                    
                    try:
                        validated = self.output_schema(**data)
                        validation_outcome = "repaired_once"
                        warnings.append("Data repaired and revalidated successfully")
                        logger.info(f"[{self.name}] Validation passed after best-effort repair")
                    except ValidationError as e2:
                        # Try one more pass with schema defaults
                        data, repairs2 = self._repair_fields_safe(data, e2, use_defaults=True)
                        repairs.update(repairs2)
                        try:
                            validated = self.output_schema(**data)
                            validation_outcome = "repaired_twice"
                            warnings.append("Data repaired on second pass")
                            logger.info(f"[{self.name}] Validation passed after second repair")
                        except ValidationError as e3:
                            raise NodeExecutionError(
                                node_name=self.name,
                                reason=f"Validation failed even after best-effort repair: {self._format_validation_errors(e3)}",
                                state=state
                            )
            
            validated_dict = validated.model_dump()
            
            # Layer 2: Custom semantic rules
            for rule_name, rule_func in self.validation_rules.items():
                try:
                    result = rule_func(validated_dict)
                    if not result:
                        warnings.append(f"Semantic rule '{rule_name}' returned False")
                except Exception as e:
                    warnings.append(f"Semantic rule '{rule_name}' raised: {e}")
            
            # Store results with metadata
            state["validated"] = validated_dict
            if warnings:
                state["validation_warnings"] = warnings
                self.metrics.warnings = warnings
            
            # Add validation metadata (December 2025 best practice)
            state["validation_metadata"] = {
                "mode": self.mode.value,
                "outcome": validation_outcome,
                "repairs": repairs,
                "original_keys": list(original_data.keys()),
                "validated_keys": list(validated_dict.keys()),
            }
            
            # Update metrics
            self.metrics.output_keys = ["validated", "validation_metadata"]
            self.metrics.status = NodeStatus.SUCCESS
            
            logger.info(
                f"[{self.name}] Validation complete (mode: {self.mode.value}, outcome: {validation_outcome})" + (
                    f" with {len(warnings)} warnings" if warnings else ""
                )
            )
            
            return state
        
        except Exception as e:
            self.metrics.status = NodeStatus.FAILED
            self.metrics.error_message = str(e)
            raise await self.on_error(e, state)
        
        finally:
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics.duration_ms = elapsed
    
    def validate_input(self, state: Dict[str, Any]) -> bool:
        return "extracted" in state
    
    def _format_validation_errors(self, error: ValidationError) -> str:
        """Format Pydantic validation errors for human-readable messages."""
        errors = []
        for err in error.errors():
            field = ".".join(str(loc) for loc in err.get("loc", ["unknown"]))
            error_type = err.get("type", "unknown")
            msg = err.get("msg", "")
            errors.append(f"{field}: {error_type} - {msg}")
        return "; ".join(errors)
    
    async def _repair_with_llm(
        self, 
        data: Dict[str, Any], 
        validation_error: ValidationError
    ) -> Dict[str, Any]:
        """
        Repair data using LLM with validation error feedback (December 2025 pattern).
        
        This implements the "JSON plumber" / "re-prompt with errors" pattern used by:
        - BentoML structured outputs
        - Haystack OutputValidator
        - Instructor retry loops
        
        Process:
            1. Format validation errors as clear feedback
            2. Construct repair prompt with original data and errors
            3. Ask LLM to fix and return valid JSON
            4. Parse and return repaired data
        """
        # Format errors for LLM
        error_summary = self._format_validation_errors(validation_error)
        
        # Get schema description
        schema_name = self.output_schema.__name__
        schema_json = self.output_schema.model_json_schema() if hasattr(self.output_schema, 'model_json_schema') else {}
        
        # Construct repair prompt
        repair_prompt = (
            f"You produced JSON data that failed validation against the {schema_name} schema.\n\n"
            f"Original data:\n{json.dumps(data, indent=2)}\n\n"
            f"Validation errors:\n{error_summary}\n\n"
            f"Schema definition:\n{json.dumps(schema_json, indent=2)}\n\n"
            f"Please fix the data to match the schema. Return ONLY valid JSON (no markdown, no explanation):"
        )
        
        logger.info(f"[{self.name}] Invoking LLM for validation repair")
        response = await self.llm.ainvoke([HumanMessage(content=repair_prompt)])
        
        # Parse repaired JSON
        json_text = response.content.strip()
        # Remove markdown code blocks if present
        if json_text.startswith("```"):
            json_text = re.sub(r'^```(?:json)?\n?', '', json_text)
            json_text = re.sub(r'\n?```$', '', json_text)
        
        try:
            repaired_data = json.loads(json_text)
            return repaired_data
        except json.JSONDecodeError as e:
            logger.warning(f"[{self.name}] LLM repair returned invalid JSON: {e}")
            # Fallback: try to extract JSON from response
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', json_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except:
                    pass
            raise NodeExecutionError(
                node_name=self.name,
                reason=f"LLM repair returned invalid JSON: {e}",
                state={"data": data, "llm_response": json_text[:200]}
            )
    
    def _repair_fields_safe(
        self, 
        data: Dict[str, Any], 
        error: ValidationError,
        use_defaults: bool = False
    ) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """
        Safe mechanical repair using Pydantic schema constraints (no domain heuristics).
        
        This method:
        - Uses schema Field(ge=, le=, default=) constraints
        - Applies safe type coercion
        - Uses schema defaults
        - Does NOT inject domain-specific values based on field names
        
        Returns:
            Tuple of (repaired_data, repairs_dict) where repairs_dict maps field_name -> repair_reason
        """
        repairs = {}
        
        # Get field info from schema
        if hasattr(self.output_schema, 'model_fields'):
            schema_fields = self.output_schema.model_fields
        elif hasattr(self.output_schema, '__fields__'):
            schema_fields = self.output_schema.__fields__
        else:
            return data, repairs  # Can't repair without schema info
        
        # Process each field
        for field_name, field_info in schema_fields.items():
            field_value = data.get(field_name)
            is_undefined = (hasattr(field_value, '__class__') and 'Undefined' in str(type(field_value)))
            is_missing = (field_name not in data or field_value is None or is_undefined)
            
            # Get field type and constraints from Pydantic
            field_type = None
            if hasattr(field_info, 'annotation'):
                field_type = field_info.annotation
            elif hasattr(field_info, 'type_'):
                field_type = field_info.type_
            
            # Get Pydantic Field constraints
            field_constraints = {}
            if hasattr(field_info, 'constraints'):
                field_constraints = field_info.constraints
            elif hasattr(field_info, 'field_info'):
                fi = field_info.field_info
                if hasattr(fi, 'ge'):
                    field_constraints['ge'] = fi.ge
                if hasattr(fi, 'le'):
                    field_constraints['le'] = fi.le
                if hasattr(fi, 'gt'):
                    field_constraints['gt'] = fi.gt
                if hasattr(fi, 'lt'):
                    field_constraints['lt'] = fi.lt
            
            # Handle missing fields
            if is_missing:
                if use_defaults or field_info.default is not None:
                    if field_info.default is not None:
                        data[field_name] = field_info.default
                        repairs[field_name] = "used_schema_default"
                    elif hasattr(field_info, 'default_factory') and field_info.default_factory is not None:
                        data[field_name] = field_info.default_factory()
                        repairs[field_name] = "used_schema_default_factory"
                    elif use_defaults:
                        # Only provide type-based defaults if explicitly requested
                        if field_type == str or (hasattr(field_type, '__origin__') and field_type.__origin__ is str):
                            data[field_name] = ""
                            repairs[field_name] = "defaulted_empty_string"
                        elif field_type == float or (hasattr(field_type, '__origin__') and field_type.__origin__ is float):
                            data[field_name] = 0.0
                            repairs[field_name] = "defaulted_zero_float"
                        elif field_type == int or (hasattr(field_type, '__origin__') and field_type.__origin__ is int):
                            data[field_name] = 0
                            repairs[field_name] = "defaulted_zero_int"
                        else:
                            data[field_name] = None
                            repairs[field_name] = "defaulted_none"
            
            # Handle type mismatches (safe coercion only)
            elif field_name in data and not is_undefined:
                value = data[field_name]
                needs_type_fix = False
                
                if field_type == str and not isinstance(value, str):
                    needs_type_fix = True
                elif field_type == float and not isinstance(value, (int, float)):
                    needs_type_fix = True
                elif field_type == int and not isinstance(value, int):
                    needs_type_fix = True
                
                if needs_type_fix:
                    try:
                        if field_type == str:
                            data[field_name] = str(value) if value is not None else ""
                            repairs[field_name] = "coerced_to_string"
                        elif field_type == float:
                            data[field_name] = float(value)
                            repairs[field_name] = "coerced_to_float"
                        elif field_type == int:
                            data[field_name] = int(float(value))  # Allow "3.0" -> 3
                            repairs[field_name] = "coerced_to_int"
                    except (ValueError, TypeError):
                        # Can't coerce, will be caught by validation
                        pass
                
                # Apply Pydantic constraints (clamp if out of bounds)
                if field_name in data:
                    value = data[field_name]
                    if isinstance(value, (int, float)):
                        if 'ge' in field_constraints and value < field_constraints['ge']:
                            data[field_name] = field_constraints['ge']
                            repairs[field_name] = f"clamped_to_min_{field_constraints['ge']}"
                        elif 'gt' in field_constraints and value <= field_constraints['gt']:
                            data[field_name] = field_constraints['gt'] + (0.01 if isinstance(value, float) else 1)
                            repairs[field_name] = f"clamped_above_min_{field_constraints['gt']}"
                        
                        if 'le' in field_constraints and value > field_constraints['le']:
                            data[field_name] = field_constraints['le']
                            repairs[field_name] = f"clamped_to_max_{field_constraints['le']}"
                        elif 'lt' in field_constraints and value >= field_constraints['lt']:
                            data[field_name] = field_constraints['lt'] - (0.01 if isinstance(value, float) else 1)
                            repairs[field_name] = f"clamped_below_max_{field_constraints['lt']}"
        
        return data, repairs
    
    def _repair_fields(self, data: Dict[str, Any], error: ValidationError) -> Dict[str, Any]:
        """
        DEPRECATED: Use _repair_fields_safe() instead.
        
        Kept for backward compatibility but delegates to safe repair.
        """
        repaired_data, _ = self._repair_fields_safe(data, error, use_defaults=True)
        return repaired_data
    
    def _repair_fields_aggressive(self, data: Dict[str, Any], error: ValidationError) -> Dict[str, Any]:
        """
        DEPRECATED: Use _repair_fields_safe() instead.
        
        Kept for backward compatibility but delegates to safe repair with defaults.
        """
        repaired_data, _ = self._repair_fields_safe(data, error, use_defaults=True)
        return repaired_data
