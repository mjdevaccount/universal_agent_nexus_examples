"""Evolve the baseline manifest using reusable self-modifying helpers."""

from pathlib import Path
import sys

from universal_agent_nexus.ir import ToolIR

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
from universal_agent_tools.patterns import (  # noqa: E402
    ExecutionLog,
    SelfModifyingAgent,
    deterministic_tool_from_error,
)

BASE_MANIFEST = Path(__file__).parent / "manifest.yaml"
EVOLVED_AGENT_PATH = Path(__file__).parent / "agent_evolved.py"


def main() -> None:
    execution_log = ExecutionLog(
        failed_queries=[
            "Cannot reach billing database",
            "Cannot parse CSV file",
            "Cannot reach billing database",
            "Cannot reach billing database",
        ],
        decision_hint="add_billing_repair",
    )

    agent = SelfModifyingAgent(str(BASE_MANIFEST))

    generated_tool = agent.analyze_and_generate_tool(
        execution_log=execution_log,
        tool_generator=lambda error: deterministic_tool_from_error(
            error, name_prefix="repair_billing"
        ),
        failure_threshold=3,
    )

    if generated_tool:
        agent.register_generated_tool(
            tool=generated_tool,
            condition_expression="contains(output, 'add_billing_repair')",
            label="Repair Billing Access",
        )
        agent.compile(str(EVOLVED_AGENT_PATH))
        print("✨ Agent evolved. New tool added and compiled to agent_evolved.py")
    else:
        print("No evolution performed; insufficient failures detected.")


if __name__ == "__main__":
    main()
