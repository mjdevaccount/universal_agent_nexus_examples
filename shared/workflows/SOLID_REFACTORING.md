# SOLID Refactoring Plan

## Overview

This document outlines the SOLID refactoring of the workflows module to improve maintainability, testability, and extensibility.

## SOLID Violations Identified

### 1. Single Responsibility Principle (SRP) Violations

**ExtractionNode:**
- JSON parsing
- Multiple repair strategies (incremental, LLM, regex)
- Strategy selection logic
- Metrics collection

**ValidationNode:**
- Pydantic validation
- Multiple validation modes (STRICT, RETRY, BEST_EFFORT)
- Repair logic (LLM repair, field repair)
- Semantic rule validation
- Metadata tracking

**Workflow:**
- Graph building
- Execution orchestration
- Metrics collection
- Error handling
- Visualization

### 2. Open/Closed Principle (OCP) Violations

- Repair strategies hardcoded in ExtractionNode
- Validation modes hardcoded in ValidationNode
- Cannot add new strategies/modes without modifying existing code

### 3. Dependency Inversion Principle (DIP) Violations

- Nodes depend on concrete LLM types (`Any`) instead of abstractions
- Workflow depends on concrete node implementations

### 4. Interface Segregation Principle (ISP)

- BaseNode has multiple responsibilities (execute, validate_input, on_error, get_metrics)

## Refactoring Solution

### New Abstractions

1. **`ILLMProvider`** - Abstract interface for LLM interactions (DIP)
2. **`IJSONRepairStrategy`** - Strategy interface for JSON repair (OCP, SRP)
3. **`IValidationStrategy`** - Strategy interface for validation modes (OCP, SRP)
4. **`IStateValidator`** - Interface for input validation (ISP)
5. **`IMetricsCollector`** - Interface for metrics collection (ISP)

### Strategy Implementations

**JSON Repair Strategies:**
- `IncrementalRepairStrategy` - Mechanical JSON repair
- `LLMRepairStrategy` - LLM-based repair
- `RegexRepairStrategy` - Regex-based extraction

**Validation Strategies:**
- `StrictValidationStrategy` - Fail fast
- `RetryValidationStrategy` - LLM repair with retries
- `BestEffortValidationStrategy` - Safe mechanical repairs

### Adapters

- `LangChainLLMAdapter` - Wraps LangChain LLMs to ILLMProvider interface

## Migration Path

1. **Phase 1:** Create abstractions and strategies (✅ Done)
2. **Phase 2:** Create LLM adapter (✅ Done)
3. **Phase 3:** Refactor ExtractionNode to use strategies (In Progress)
4. **Phase 4:** Refactor ValidationNode to use strategies
5. **Phase 5:** Separate Workflow concerns (GraphBuilder, Executor, MetricsCollector)
6. **Phase 6:** Update all examples to use new abstractions
7. **Phase 7:** Maintain backward compatibility through adapters

## Backward Compatibility

All existing code will continue to work through:
- Automatic adapter wrapping of LangChain LLMs
- Default strategy selection based on existing parameters
- Wrapper classes that maintain old API

## Benefits

1. **Testability:** Strategies can be tested independently
2. **Extensibility:** New strategies can be added without modifying existing code
3. **Maintainability:** Each class has a single, clear responsibility
4. **Flexibility:** Easy to swap implementations (e.g., different LLM providers)

