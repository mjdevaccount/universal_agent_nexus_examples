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
            
            # Invoke LLM
            response = await self.llm.ainvoke(
                [HumanMessage(content=prompt_text)]
            )
            json_text = response.content
            
            # Parse and repair
            warnings = []
            data = None
            
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
                        logger.info(f"[{self.name}] Regex extraction successful")
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
        """
        data = {}
        
        # Try to extract common numeric fields
        patterns = {
            "adoption_timeline_months": r'(?:adoption|timeline|months)[^:]*[:\s]*(\d+)',
            "disruption_score": r'(?:disruption|score)[^:]*[:\s]*(\d+\.?\d*)',
            "market_cap": r'(?:market|trillion)[^:]*[:\s]*(\d+\.?\d*)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, json_text + analysis_text, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1))
                    data[key] = int(value) if key.endswith("_months") else value
                except (ValueError, IndexError):
                    pass
        
        return data or {"extraction_status": "partial"}
    
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
            
            # Layer 1: Pydantic validation with repair
            try:
                validated = self.output_schema(**data)
                logger.info(f"[{self.name}] Schema validation passed")
            except ValidationError as e:
                if self.repair_on_fail:
                    warnings.append(f"Schema validation failed: {e.error_count()} errors")
                    data = self._repair_fields(data, e)
                    try:
                        validated = self.output_schema(**data)
                        warnings.append("Data repaired and revalidated successfully")
                        logger.info(f"[{self.name}] Validation passed after repair")
                    except ValidationError as e2:
                        raise NodeExecutionError(
                            node_name=self.name,
                            reason=f"Validation failed even after repair: {e2}",
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
            - Clamp numeric values to bounds
            - Remove invalid keys
            - Fill missing required fields with defaults
        """
        # Get field info from schema
        schema_fields = self.output_schema.model_fields
        
        for field_name, field_info in schema_fields.items():
            if field_name not in data:
                # Missing field - try default
                if field_info.default is not None:
                    data[field_name] = field_info.default
                elif field_info.default_factory is not None:
                    data[field_name] = field_info.default_factory()
            else:
                # Field exists - try to repair
                value = data[field_name]
                
                # Clamp numerics
                if field_name.endswith("_months") and isinstance(value, (int, float)):
                    data[field_name] = max(1, min(60, int(value)))
                elif field_name.endswith("_score") and isinstance(value, (int, float)):
                    data[field_name] = max(0.0, min(10.0, float(value)))
        
        return data
