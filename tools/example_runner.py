"""Standardized command helper for Universal Agent Nexus examples.

This wrapper lists the canonical commands for each example and can optionally
execute them. It keeps lower-numbered (intro) and higher-numbered (advanced)
examples aligned without requiring contributors to memorize unique scripts.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


ROOT = Path(__file__).resolve().parent.parent


@dataclass
class CommandSpec:
    name: str
    command: str
    description: str


@dataclass
class ExampleSpec:
    code: str
    title: str
    summary: str
    workdir: Path
    commands: List[CommandSpec] = field(default_factory=list)
    notes: Optional[str] = None
    manifest: Optional[str] = None
    compile_output: str = "agent.py"
    fabric: str = "Defaults to resolve_fabric_from_env (memory unless overridden)."

    def as_display(self) -> str:
        lines = [f"{self.code} – {self.title}", f"  {self.summary}"]
        if self.notes:
            lines.append(f"  Notes: {self.notes}")
        for cmd in self.commands:
            lines.append(f"  - {cmd.name}: {cmd.command} ({cmd.description})")
        return "\n".join(lines)

    @property
    def compile_command(self) -> Optional[str]:
        if not self.manifest:
            return None
        return f"nexus compile {self.manifest} --target langgraph --output {self.compile_output}"

    @property
    def runtime_command(self) -> Optional[str]:
        # Prefer a 'run' command, otherwise take the first command.
        for cmd in self.commands:
            if cmd.name == "run":
                return cmd.command
        for cmd in self.commands:
            if cmd.name == "serve":
                return cmd.command
        return self.commands[0].command if self.commands else None


EXAMPLES: Dict[str, ExampleSpec] = {
    "01": ExampleSpec(
        code="01",
        title="Hello World",
        summary="Basic manifest compile and LangGraph execution.",
        workdir=ROOT / "01-hello-world",
        manifest="manifest.yaml",
        commands=[
            CommandSpec(
                "compile",
                "nexus compile manifest.yaml --target langgraph --output agent.py",
                "Compile the manifest to a runnable LangGraph script.",
            ),
            CommandSpec(
                "run",
                "python agent.py",
                "Execute the compiled graph locally.",
            ),
        ],
    ),
    "02": ExampleSpec(
        code="02",
        title="Content Moderation",
        summary="Multi-stage content moderation with routing and tests.",
        workdir=ROOT / "02-content-moderation",
        manifest="manifest.yaml",
        commands=[
            CommandSpec(
                "compile",
                "nexus compile manifest.yaml --target langgraph --output agent.py",
                "Compile the moderation manifest for LangGraph.",
            ),
            CommandSpec("run", "python run_agent.py", "Run the moderation pipeline."),
            CommandSpec("test", "python -m pytest", "Execute included risk-level tests."),
        ],
    ),
    "03": ExampleSpec(
        code="03",
        title="Data Pipeline",
        summary="ETL with LLM enrichment and schema validation.",
        workdir=ROOT / "03-data-pipeline",
        manifest="manifest.yaml",
        commands=[
            CommandSpec(
                "compile",
                "nexus compile manifest.yaml --target langgraph --output agent.py",
                "Compile the ETL manifest.",
            ),
            CommandSpec("run", "python run_agent.py", "Run the ETL pipeline locally."),
        ],
    ),
    "04": ExampleSpec(
        code="04",
        title="Support Chatbot",
        summary="Intent routing, knowledge base retrieval, and escalation.",
        workdir=ROOT / "04-support-chatbot",
        manifest="manifest.yaml",
        commands=[
            CommandSpec(
                "compile",
                "nexus compile manifest.yaml --target langgraph --output agent.py",
                "Compile the support chatbot manifest.",
            ),
            CommandSpec("run", "python run_agent.py", "Start the support chatbot."),
            CommandSpec("test", "python -m pytest", "Validate intents and fallback paths."),
        ],
    ),
    "05": ExampleSpec(
        code="05",
        title="Research Assistant",
        summary="Document analysis and summarization pipeline.",
        workdir=ROOT / "05-research-assistant",
        manifest="manifest.yaml",
        commands=[
            CommandSpec(
                "compile",
                "nexus compile manifest.yaml --target langgraph --output agent.py",
                "Compile the research assistant manifest.",
            ),
            CommandSpec("run", "python run_agent.py", "Run the research assistant graph."),
        ],
    ),
    "06": ExampleSpec(
        code="06",
        title="Playground Simulation",
        summary="Multi-agent playground with real-time frontend and backend.",
        workdir=ROOT / "06-playground-simulation",
        commands=[
            CommandSpec(
                "deps",
                "pip install -r backend/requirements.txt",
                "Install backend dependencies for the simulation.",
            ),
            CommandSpec(
                "serve",
                "uvicorn backend/main:app --port 8888",
                "Start the backend API and WebSocket server.",
            ),
        ],
        notes="Open frontend/index.html after the backend is running.",
    ),
    "07": ExampleSpec(
        code="07",
        title="Innovation Waves",
        summary="Technology adoption simulator with multi-runtime demo matrix.",
        workdir=ROOT / "07-innovation-waves",
        commands=[
            CommandSpec("deps", "pip install -r backend/requirements.txt", "Install backend dependencies."),
            CommandSpec("serve", "python backend/main.py", "Launch the simulation backend."),
        ],
        notes="Open frontend pages for single-view or demo-matrix modes.",
    ),
    "08": ExampleSpec(
        code="08",
        title="Local Agent Runtime",
        summary="LangGraph runtime with MCP filesystem/git servers and Ollama.",
        workdir=ROOT / "08-local-agent-runtime",
        commands=[
            CommandSpec("deps", "pip install -r backend/requirements.txt", "Install runtime dependencies."),
            CommandSpec(
                "mcp",
                "python mcp_servers/filesystem/server.py & python mcp_servers/git/server.py",
                "Start MCP servers.",
            ),
            CommandSpec("run", "python runtime/agent_runtime.py", "Execute the local agent runtime."),
        ],
    ),
    "09": ExampleSpec(
        code="09",
        title="Autonomous Flow",
        summary="Dynamic tool discovery with regenerated manifests.",
        workdir=ROOT / "09-autonomous-flow",
        manifest="autonomous_flow.yaml",
        commands=[
            CommandSpec(
                "compile",
                "nexus compile autonomous_flow.yaml --target langgraph --output agent.py",
                "Compile the autonomous flow graph.",
            ),
            CommandSpec("run", "python runtime/autonomous_runtime.py", "Run the autonomous flow demo."),
        ],
    ),
    "10": ExampleSpec(
        code="10",
        title="Local LLM Tool Servers",
        summary="Nested scaffolding, enrichment, and dynamic tool generation.",
        workdir=ROOT / "10-local-llm-tool-servers",
        commands=[
            CommandSpec("deps", "pip install -r requirements.txt", "Install shared toolkit dependencies."),
            CommandSpec("org", "python organization_agent.py", "Run the organization-level scaffolded agent."),
            CommandSpec(
                "research",
                "python research_agent/run_local.py",
                "Launch the local research agent variant.",
            ),
        ],
    ),
    "11": ExampleSpec(
        code="11",
        title="N-Decision Router",
        summary="Adaptive router with manifest generation and tests.",
        workdir=ROOT / "11-n-decision-router",
        manifest="manifest.yaml",
        commands=[
            CommandSpec("deps", "pip install -r requirements.txt", "Install router dependencies."),
            CommandSpec(
                "compile",
                "nexus compile manifest.yaml --target langgraph --output agent.py",
                "Compile the router manifest for LangGraph.",
            ),
            CommandSpec("run", "python run_agent.py", "Execute the N-decision router."),
        ],
    ),
    "12": ExampleSpec(
        code="12",
        title="Self-Modifying Agent",
        summary="Agent that regenerates its own manifest on the fly.",
        workdir=ROOT / "12-self-modifying-agent",
        manifest="manifest.yaml",
        commands=[
            CommandSpec(
                "compile",
                "nexus compile manifest.yaml --target langgraph --output agent.py",
                "Compile the baseline manifest before self-modifying runs.",
            ),
            CommandSpec("run", "python run_agent.py", "Run the self-modifying agent."),
        ],
    ),
    "13": ExampleSpec(
        code="13",
        title="Practical Quickstart",
        summary="Batteries-included starter with sensible defaults.",
        workdir=ROOT / "13-practical-quickstart",
        manifest="manifest.yaml",
        commands=[
            CommandSpec(
                "compile",
                "nexus compile manifest.yaml --target langgraph --output agent.py",
                "Compile the quickstart manifest.",
            ),
            CommandSpec("run", "python run_agent.py", "Execute the quickstart graph."),
        ],
    ),
    "15": ExampleSpec(
        code="15",
        title="Cached Content Moderation",
        summary="Cache Fabric integration with observability and feedback.",
        workdir=ROOT / "15-cached-content-moderation",
        manifest="manifest.yaml",
        fabric="Cache Fabric integrated end-to-end (compile + runtime).",
        commands=[
            CommandSpec("deps", "pip install -r requirements.txt", "Install cache fabric dependencies."),
            CommandSpec(
                "compile",
                "nexus compile manifest.yaml --target langgraph --output agent.py",
                "Compile the cached content moderation manifest.",
            ),
            CommandSpec("run", "python run_fabric_demo.py", "Run the Cache Fabric demo end-to-end."),
        ],
    ),
}


def list_examples() -> None:
    for key in sorted(EXAMPLES.keys()):
        spec = EXAMPLES[key]
        print(f"{spec.code} – {spec.title}: {spec.summary}")


def show_example(code: str) -> None:
    spec = EXAMPLES.get(code)
    if not spec:
        raise SystemExit(f"Unknown example code '{code}'. Available: {', '.join(sorted(EXAMPLES))}")

    print(spec.as_display())


def show_matrix() -> None:
    header = ["Code", "Design", "Compile", "Runtime", "Fabric"]
    col_widths = [6, 24, 40, 28, 40]
    print(
        f"{header[0]:<{col_widths[0]}} | {header[1]:<{col_widths[1]}} | {header[2]:<{col_widths[2]}} | {header[3]:<{col_widths[3]}} | {header[4]}"
    )
    print("-" * 150)

    for key in sorted(EXAMPLES.keys()):
        spec = EXAMPLES[key]
        design = spec.manifest or "runtime-first"
        compile_cmd = spec.compile_command or "(no manifest)"
        runtime_cmd = spec.runtime_command or "(no runtime command)"
        fabric = spec.fabric

        print(
            f"{spec.code:<{col_widths[0]}} | {design:<{col_widths[1]}} | {compile_cmd:<{col_widths[2]}} | {runtime_cmd:<{col_widths[3]}} | {fabric}"
        )


def run_command(code: str, command_name: str, execute: bool) -> None:
    spec = EXAMPLES.get(code)
    if not spec:
        raise SystemExit(f"Unknown example code '{code}'. Available: {', '.join(sorted(EXAMPLES))}")

    cmd = next((c for c in spec.commands if c.name == command_name), None)
    if not cmd:
        available = ", ".join(c.name for c in spec.commands)
        raise SystemExit(f"Unknown command '{command_name}' for example {code}. Available: {available}")

    print(f"[{spec.code}] {cmd.name}: {cmd.command}")
    print(f"Working directory: {spec.workdir}")

    if not execute:
        print("(dry run) Set --execute to run this command.")
        return

    try:
        subprocess.run(cmd.command, cwd=spec.workdir, shell=True, check=True)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)

    sub.add_parser("list", help="List available examples")
    sub.add_parser("matrix", help="Show design → compile → runtime → fabric matrix")

    show_parser = sub.add_parser("show", help="Show commands for one example")
    show_parser.add_argument("code", help="Example code (e.g., 01, 08, 15)")

    run_parser = sub.add_parser("run", help="Print or execute a command for an example")
    run_parser.add_argument("code", help="Example code (e.g., 01, 08, 15)")
    run_parser.add_argument("command", help="Command name (e.g., run, deps, compile)")
    run_parser.add_argument("--execute", action="store_true", help="Actually run the command instead of printing")

    args = parser.parse_args(argv)

    if args.action == "list":
        list_examples()
    elif args.action == "matrix":
        show_matrix()
    elif args.action == "show":
        show_example(args.code)
    elif args.action == "run":
        run_command(args.code, args.command, execute=args.execute)
    else:
        parser.error(f"Unknown action {args.action}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
