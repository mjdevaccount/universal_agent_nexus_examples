# Step-by-Step Approach for Tool Calling

## Current Issue

Even with `qwen2.5-coder:14b`, the model:
- ✅ Recognizes tools exist
- ✅ Has `tool_calls` attribute
- ❌ `tool_calls` is always empty `[]`

## Hypothesis: Multi-Turn Conversation Needed

The agent might need to see tool results before it understands it should call tools. Current flow:
1. Agent receives instruction
2. Agent responds (no tool calls)
3. Graph ends

**Missing:** The agent never sees what happens when tools ARE called.

## Proposed Solution: ReAct-Style Loop

Instead of relying on model's native tool calling, implement a ReAct pattern:

1. **Agent thinks** → Generates response
2. **Parse response** → Look for tool mentions in text
3. **Call tools manually** → Execute based on text analysis
4. **Feed results back** → Continue conversation
5. **Repeat** until task complete

## Alternative: Check Tool Format

The issue might be that MCPTool wrapper doesn't expose tools in the format Ollama expects. Need to verify:

1. Tool schema format
2. Whether tools need to be converted to LangChain's StructuredTool
3. If Ollama needs tools in a specific JSON schema format

## Current Status

- ✅ Model: `qwen2.5-coder:14b` (switched from qwen3:8b)
- ✅ Configuration: `temperature=0`, no thinking mode
- ✅ Binding: `bind_tools()` succeeds
- ❌ Execution: `tool_calls` empty

## Next Research Questions

1. Does `qwen2.5-coder:14b` actually support function calling in Ollama?
2. Do we need to use StructuredTool instead of BaseTool?
3. Should we implement manual tool calling (ReAct pattern)?
4. Is there a specific prompt format that triggers tool calls?

## Files to Check

- `agent_runtime.py:79-118` - MCPTool class definition
- `agent_runtime.py:199-232` - tool_node (never reached)
- LangChain Ollama documentation for tool format requirements

