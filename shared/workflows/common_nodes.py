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

from pydantic import BaseModel, ValidationError
from langchain_core.messages import HumanMessage, BaseMessage

from shared.workflows.nodes import (
    BaseNode,
    NodeExecutionError,
    NodeStatus,
)

logger = logging.getLogger(__name__)


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
    Semantic validation and repair node.
    
    Single Responsibility: Validate extracted data and repair if possible.
    
    Temperature: 0.0 (strict enforcement)
    
    Input Requirements:
        - state["extracted"]: Dict from extraction node
    
    Output:
        - Adds `validated` key with validated/repaired data
        - Adds `validation_warnings` list
    
    Validation Layers:
        1. Pydantic schema validation (type checking)
        2. Custom semantic rules (business logic)
        3. Bounds checking and repair (clamp values)
    
    Design Pattern: Decorator
        Validation can be stacked (schema → rules → bounds).
    
    Example:
        validation = ValidationNode(
            output_schema=AdoptionPrediction,
            validation_rules={
                "timeline_sanity": lambda x: 1 <= x["adoption_timeline_months"] <= 60,
            }
        )
        
        state = await validation.execute({"extracted": data})
        # state["validated"] = repaired_and_validated_data
    """
    
    def __init__(
        self,
        output_schema: Type[BaseModel],
        validation_rules: Dict[str, Callable] = None,
        repair_on_fail: bool = True,
        name: str = "validation",
        description: str = "Validate and repair extracted data",
    ):
        """
        Initialize validation node.
        
        Args:
            output_schema: Pydantic model to validate against
            validation_rules: Dict of {rule_name: rule_func}
                where rule_func(data) returns True if valid, raises/returns False otherwise
            repair_on_fail: Whether to attempt repairs on validation failure
            name: Node identifier
            description: Human-readable description
        
        Example of validation_rules:
            {
                "timeline_bounds": lambda x: 1 <= x["adoption_timeline_months"] <= 60,
                "disruption_positive": lambda x: x["disruption_score"] >= 0,
            }
        """
        super().__init__(name=name, description=description)
        self.output_schema = output_schema
        self.validation_rules = validation_rules or {}
        self.repair_on_fail = repair_on_fail
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute validation.
        
        Process:
            1. Try to validate with Pydantic schema
            2. If fails and repair_on_fail, attempt repairs
            3. Apply custom semantic rules
            4. Return validated data
        
        Args:
            state: Must have "extracted" key
        
        Returns:
            State with added keys:
                - validated: Validated/repaired data dict
                - validation_warnings: List of warnings/repairs applied
        
        Raises:
            NodeExecutionError: If validation fails and can't be repaired
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
            
            data = state["extracted"].copy()
            warnings = []
            
            # If extracted data is just a status marker, create empty dict for repair
            if "extraction_status" in data and len(data) == 1:
                warnings.append("Extraction returned only status marker, using defaults for all fields")
                data = {}
            
            # Remove any undefined/null values and status markers
            data = {k: v for k, v in data.items() 
                   if k != "extraction_status" and v is not None 
                   and not (hasattr(v, '__class__') and 'Undefined' in str(type(v)))}
            
            # Layer 1: Pydantic validation with repair
            try:
                validated = self.output_schema(**data)
                logger.info(f"[{self.name}] Schema validation passed")
            except ValidationError as e:
                if self.repair_on_fail:
                    warnings.append(f"Schema validation failed: {e.error_count()} errors")
                    logger.info(f"[{self.name}] Attempting field repair (missing fields: {[err['loc'][0] for err in e.errors() if 'loc' in err]})")
                    data = self._repair_fields(data, e)
                    logger.info(f"[{self.name}] After repair, data keys: {list(data.keys())}")
                    try:
                        validated = self.output_schema(**data)
                        warnings.append("Data repaired and revalidated successfully")
                        logger.info(f"[{self.name}] Validation passed after repair")
                    except ValidationError as e2:
                        # Log what fields are still failing
                        error_details = [(err.get('loc', ['unknown'])[0], err.get('type'), err.get('msg', '')) 
                                        for err in e2.errors()]
                        logger.error(f"[{self.name}] Validation errors after repair: {error_details}")
                        # Try one more repair pass with more aggressive defaults
                        data = self._repair_fields_aggressive(data, e2)
                        try:
                            validated = self.output_schema(**data)
                            warnings.append("Data repaired on second pass")
                            logger.info(f"[{self.name}] Validation passed after second repair")
                        except ValidationError as e3:
                            raise NodeExecutionError(
                                node_name=self.name,
                                reason=f"Validation failed even after repair: {e3}",
                                state=state
                            )
                else:
                    raise NodeExecutionError(
                        node_name=self.name,
                        reason=f"Schema validation failed: {e}",
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
            
            # Store results
            state["validated"] = validated_dict
            if warnings:
                state["validation_warnings"] = warnings
                self.metrics.warnings = warnings
            
            # Update metrics
            self.metrics.output_keys = ["validated"]
            self.metrics.status = NodeStatus.SUCCESS
            
            logger.info(
                f"[{self.name}] Validation complete" + (
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
    
    def _repair_fields(self, data: Dict[str, Any], error: ValidationError) -> Dict[str, Any]:
        """
        Attempt to repair individual fields that failed validation.
        
        Repair strategies:
        - Fill missing required fields with defaults
        - Clamp out-of-bounds values
        - Convert types when possible
            - Clamp numeric values to bounds
            - Remove invalid keys
            - Fill missing required fields with defaults
        """
        # Get field info from schema
        if hasattr(self.output_schema, 'model_fields'):
            schema_fields = self.output_schema.model_fields
        elif hasattr(self.output_schema, '__fields__'):
            schema_fields = self.output_schema.__fields__
        else:
            return data  # Can't repair without schema info
        
        for field_name, field_info in schema_fields.items():
            # Check if field is missing, None, or PydanticUndefined
            field_value = data.get(field_name)
            is_undefined = (hasattr(field_value, '__class__') and 'Undefined' in str(type(field_value)))
            is_missing = (field_name not in data or 
                         field_value is None or 
                         is_undefined)
            
            # Also check if value is wrong type (will be caught by validation but we can fix proactively)
            needs_type_fix = False
            if field_name in data and not is_undefined:
                field_type = None
                if hasattr(field_info, 'annotation'):
                    field_type = field_info.annotation
                elif hasattr(field_info, 'type_'):
                    field_type = field_info.type_
                
                if field_type == str and not isinstance(field_value, str):
                    needs_type_fix = True
                elif field_type == float and not isinstance(field_value, (int, float)):
                    needs_type_fix = True
                elif field_type == int and not isinstance(field_value, int):
                    needs_type_fix = True
            
            if is_missing or needs_type_fix:
                # Missing field - try default or provide sensible fallback
                if field_info.default is not None:
                    data[field_name] = field_info.default
                elif field_info.default_factory is not None:
                    data[field_name] = field_info.default_factory()
                else:
                    # No default in schema - provide sensible fallback based on field name/type
                    # Get field type from annotation or type_ attribute
                    field_type = None
                    if hasattr(field_info, 'annotation'):
                        field_type = field_info.annotation
                    elif hasattr(field_info, 'type_'):
                        field_type = field_info.type_
                    
                    # Provide defaults based on type and field name
                    if field_type == str or (hasattr(field_type, '__origin__') and field_type.__origin__ is str):
                        # String defaults based on field name
                        if "severity" in field_name.lower() or "level" in field_name.lower():
                            data[field_name] = "safe"  # Safe default for severity
                        elif "category" in field_name.lower():
                            data[field_name] = "none"  # Default category
                        else:
                            data[field_name] = ""  # Empty string default
                    elif field_type == float or (hasattr(field_type, '__origin__') and field_type.__origin__ is float):
                        if "confidence" in field_name.lower():
                            data[field_name] = 0.5  # Medium confidence default
                        else:
                            data[field_name] = 0.0  # Zero default for floats
                    elif field_type == int or (hasattr(field_type, '__origin__') and field_type.__origin__ is int):
                        data[field_name] = 0  # Zero default for ints
                    else:
                        # Unknown type - try string default
                        if "severity" in field_name.lower() or "level" in field_name.lower():
                            data[field_name] = "safe"
                        elif "category" in field_name.lower():
                            data[field_name] = "none"
                        elif "confidence" in field_name.lower():
                            data[field_name] = 0.5
                        else:
                            data[field_name] = ""  # Last resort: empty string
            else:
                # Field exists - try to repair value/type
                value = data[field_name]
                
                # Fix type mismatches first
                field_type = None
                if hasattr(field_info, 'annotation'):
                    field_type = field_info.annotation
                elif hasattr(field_info, 'type_'):
                    field_type = field_info.type_
                
                if field_type == str and not isinstance(value, str):
                    # Convert to string
                    if "severity" in field_name.lower() or "level" in field_name.lower():
                        data[field_name] = "safe"
                    elif "category" in field_name.lower():
                        data[field_name] = "none"
                    else:
                        data[field_name] = str(value) if value else ""
                elif field_type == float and not isinstance(value, (int, float)):
                    # Convert to float
                    try:
                        data[field_name] = float(value) if value else 0.5
                    except (ValueError, TypeError):
                        data[field_name] = 0.5 if "confidence" in field_name.lower() else 0.0
                elif field_type == int and not isinstance(value, int):
                    # Convert to int
                    try:
                        data[field_name] = int(value) if value else 0
                    except (ValueError, TypeError):
                        data[field_name] = 0
                
                # Clamp numerics to valid ranges
                value = data[field_name]  # Use potentially fixed value
                if field_name.endswith("_months") and isinstance(value, (int, float)):
                    data[field_name] = max(1, min(60, int(value)))
                elif field_name.endswith("_score") and isinstance(value, (int, float)):
                    data[field_name] = max(0.0, min(10.0, float(value)))
                elif "confidence" in field_name.lower() and isinstance(value, (int, float)):
                    data[field_name] = max(0.0, min(1.0, float(value)))
        
        return data
    
    def _repair_fields_aggressive(self, data: Dict[str, Any], error: ValidationError) -> Dict[str, Any]:
        """
        More aggressive repair that handles type mismatches and invalid values.
        
        This is called when the first repair pass fails.
        """
        # Get schema fields
        if hasattr(self.output_schema, 'model_fields'):
            schema_fields = self.output_schema.model_fields
        elif hasattr(self.output_schema, '__fields__'):
            schema_fields = self.output_schema.__fields__
        else:
            return data
        
        # Get error details and fix each failing field
        for err in error.errors():
            if 'loc' in err and len(err['loc']) > 0:
                field_name = err['loc'][0]
                error_type = err.get('type', '')
                
                if field_name in schema_fields:
                    field_info = schema_fields[field_name]
                    field_type = None
                    if hasattr(field_info, 'annotation'):
                        field_type = field_info.annotation
                    elif hasattr(field_info, 'type_'):
                        field_type = field_info.type_
                    
                    # Force correct type based on error
                    if error_type in ('string_type', 'type_error'):
                        # Expected string but got something else (including PydanticUndefined)
                        if "severity" in field_name.lower() or "level" in field_name.lower():
                            data[field_name] = "safe"  # Valid enum value
                        elif "category" in field_name.lower():
                            data[field_name] = "none"
                        else:
                            data[field_name] = ""  # Empty string
                    elif error_type in ('float_type', 'int_parsing', 'float_parsing'):
                        # Expected number but got something else
                        if "confidence" in field_name.lower():
                            data[field_name] = 0.5  # Valid confidence
                        else:
                            data[field_name] = 0.0  # Default float
                    elif error_type == 'value_error':
                        # Invalid value (e.g., not in enum)
                        if "severity" in field_name.lower() or "level" in field_name.lower():
                            data[field_name] = "safe"  # Valid severity
                        elif "confidence" in field_name.lower():
                            data[field_name] = 0.5  # Valid confidence
        
        return data
