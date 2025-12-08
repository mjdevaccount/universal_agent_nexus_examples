"""Dynamic CSV tool injection example using reusable toolkit primitives."""

from universal_agent_tools.patterns import DynamicCSVToolInjector

__all__ = ["DynamicCSVToolInjector"]


if __name__ == "__main__":
    from universal_agent_nexus.compiler import generate, parse

    ir = parse("manifest.yaml")
    injector = DynamicCSVToolInjector(["/tmp/uploaded/customers.csv"])
    updated_ir = injector.inject_tools(ir)
    code = generate(updated_ir, target="langgraph")
    print(code[:500])
