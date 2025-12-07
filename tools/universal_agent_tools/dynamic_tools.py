"""Dynamic tool creation helpers built on the Nexus IR visitor."""

from typing import List

from universal_agent_nexus.ir import EdgeIR, ManifestIR, NodeIR, NodeKind, ToolIR
from universal_agent_nexus.ir.visitor import DefaultIRVisitor


class DynamicCSVToolInjector(DefaultIRVisitor):
    """Analyze uploaded CSV files and inject dedicated MCP tools."""

    def __init__(self, uploaded_files: List[str]):
        self.uploaded_files = uploaded_files
        self.injected_tools: List[str] = []

    def inject_tools(self, ir: ManifestIR) -> ManifestIR:
        for index, file_path in enumerate(self.uploaded_files):
            file_name = file_path.split("/")[-1].replace(".csv", "")

            # Create new tool definition
            tool = ToolIR(
                name=f"query_{file_name}",
                description=f"Query and analyze CSV data from {file_name}",
                protocol="mcp",
                config={
                    "command": "mcp-csv-query-server",
                    "args": [file_path],
                },
            )
            ir.tools.append(tool)

            # Create new node in each graph
            for graph in ir.graphs:
                node = NodeIR(
                    id=f"csv_query_{index}",
                    kind=NodeKind.TOOL,
                    tool_ref=tool.name,
                    label=f"Query {file_name}",
                )
                graph.nodes.append(node)

                router = next((n for n in graph.nodes if n.kind == NodeKind.ROUTER), None)
                if router:
                    graph.edges.append(
                        EdgeIR(
                            from_node=router.id,
                            to_node=node.id,
                            condition={"expression": f"contains(output, '{file_name}')"},
                        )
                    )

            self.injected_tools.append(tool.name)

        return ir
