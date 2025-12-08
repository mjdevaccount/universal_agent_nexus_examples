"""Self-modifying agent helpers for runtime-driven tool generation."""

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from universal_agent_nexus.compiler import generate, parse
from universal_agent_nexus.ir import EdgeIR, ManifestIR, NodeIR, NodeKind, ToolIR
from universal_agent_nexus.ir.visitor import DefaultIRVisitor


@dataclass
class ExecutionLog:
    """Lightweight execution log used to decide whether to evolve the agent."""

    failed_queries: List[str]
    decision_hint: Optional[str] = None


class ToolGenerationVisitor(DefaultIRVisitor):
    """Tracks tool usage in a manifest IR for analysis or reporting."""

    def __init__(self) -> None:
        self.tool_call_counts: Dict[str, int] = {}

    def visit_tool(self, tool: ToolIR) -> None:  # type: ignore[override]
        self.tool_call_counts[tool.name] = self.tool_call_counts.get(tool.name, 0) + 1


class SelfModifyingAgent:
    """Utility for evolving manifests with newly generated tools."""

    def __init__(self, manifest_path: str):
        self.manifest_path = manifest_path
        self.ir: ManifestIR = parse(manifest_path)

    def analyze_and_generate_tool(
        self,
        execution_log: ExecutionLog,
        tool_generator: Callable[[str], ToolIR],
        failure_threshold: int = 3,
    ) -> Optional[ToolIR]:
        """Generate a tool from the most common failure if threshold is met."""

        if len(execution_log.failed_queries) < failure_threshold:
            return None

        common_failure = execution_log.failed_queries[-1]
        return tool_generator(common_failure)

    def register_generated_tool(
        self,
        tool: ToolIR,
        condition_expression: str,
        label: Optional[str] = None,
    ) -> None:
        """Inject the tool into the manifest and wire it to the router and formatter."""

        self.ir.tools.append(tool)

        for graph in self.ir.graphs:
            router = next((node for node in graph.nodes if node.kind == NodeKind.ROUTER), None)
            formatter = next((node for node in graph.nodes if node.kind == NodeKind.TASK), None)

            if not router:
                continue

            exec_node = NodeIR(
                id=f"{tool.name}_exec",
                kind=NodeKind.TOOL,
                tool_ref=tool.name,
                label=label or f"Execute {tool.name}",
            )
            graph.nodes.append(exec_node)

            graph.edges.append(
                EdgeIR(
                    from_node=router.id,
                    to_node=exec_node.id,
                    condition={"expression": condition_expression},
                )
            )

            if formatter:
                graph.edges.append(
                    EdgeIR(
                        from_node=exec_node.id,
                        to_node=formatter.id,
                    )
                )

    def compile(self, output_path: str, target: str = "langgraph") -> str:
        """Compile the evolved manifest to code for the requested runtime."""

        compiled_code = generate(self.ir, target=target)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(compiled_code)
        return output_path


def deterministic_tool_from_error(error_msg: str, name_prefix: str = "repair") -> ToolIR:
    """Create a deterministic MCP tool definition from an error message."""

    safe_suffix = error_msg.lower().replace(" ", "-").replace("'", "")[:32]
    return ToolIR(
        name=f"{name_prefix}_{safe_suffix}",
        protocol="mcp",
        description="Auto-generated repair tool derived from execution failures.",
        config={
            "command": "python",
            "args": ["-m", "mcp_toolkit.repair"],
            "env": {"ERROR_PATTERN": error_msg},
        },
    )


__all__ = [
    "ExecutionLog",
    "ToolGenerationVisitor",
    "SelfModifyingAgent",
    "deterministic_tool_from_error",
]
