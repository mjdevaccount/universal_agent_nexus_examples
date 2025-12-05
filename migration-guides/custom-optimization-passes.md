# Building Custom Optimization Passes

**Extend Universal Agent Nexus with your own optimization passes.**

## Overview

The UAA compiler uses a **PassManager** architecture that allows you to:

- Add custom optimization passes
- Modify the IR before code generation
- Implement domain-specific optimizations
- Validate graphs against custom rules

---

## PassManager Architecture

```
manifest.yaml
      ↓
   Parser
      ↓
  UAA IR (Intermediate Representation)
      ↓
┌─────────────────────────────────┐
│         PassManager             │
├─────────────────────────────────┤
│  Pass 1: Validate               │
│  Pass 2: DeadNodeElimination    │
│  Pass 3: EdgeFusion             │
│  Pass 4: YourCustomPass         │
└─────────────────────────────────┘
      ↓
  Optimized IR
      ↓
  CodeGenerator (LangGraph/AWS/MCP)
      ↓
   Output
```

---

## Writing a Custom Pass

### Basic Structure

```python
from nexus.compiler.passes import Pass, PassResult
from nexus.compiler.ir import GraphIR

class MyCustomPass(Pass):
    """Description of what this pass does."""
    
    name = "my_custom_pass"
    
    def run(self, ir: GraphIR) -> PassResult:
        """
        Transform the IR.
        
        Args:
            ir: The intermediate representation to transform
            
        Returns:
            PassResult indicating success/failure and any diagnostics
        """
        modified = False
        diagnostics = []
        
        for graph in ir.graphs:
            for node in graph.nodes:
                # Your transformation logic here
                if self.should_transform(node):
                    self.transform_node(node)
                    modified = True
        
        return PassResult(
            success=True,
            modified=modified,
            diagnostics=diagnostics
        )
    
    def should_transform(self, node):
        # Your condition logic
        return node.kind == "task" and node.config.get("optimize")
    
    def transform_node(self, node):
        # Your transformation logic
        pass
```

### Registering Your Pass

```python
from nexus.compiler import PassManager

# Add to existing pass pipeline
pass_manager = PassManager()
pass_manager.add_pass(MyCustomPass(), after="validate")

# Or create custom pipeline
pass_manager = PassManager(passes=[
    ValidatePass(),
    MyCustomPass(),
    DeadNodeEliminationPass(),
    CodeGenPass(),
])
```

---

## Example Passes

### 1. Dead Node Elimination

Remove unreachable nodes:

```python
class DeadNodeEliminationPass(Pass):
    name = "dead_node_elimination"
    
    def run(self, ir: GraphIR) -> PassResult:
        modified = False
        
        for graph in ir.graphs:
            reachable = self.find_reachable(graph, graph.entry_node)
            dead_nodes = [n for n in graph.nodes if n.id not in reachable]
            
            for node in dead_nodes:
                graph.remove_node(node)
                modified = True
        
        return PassResult(success=True, modified=modified)
    
    def find_reachable(self, graph, start_node):
        visited = set()
        queue = [start_node]
        
        while queue:
            node_id = queue.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)
            
            for edge in graph.edges:
                if edge.from_node == node_id:
                    queue.append(edge.to_node)
        
        return visited
```

### 2. Edge Fusion

Combine sequential task nodes:

```python
class EdgeFusionPass(Pass):
    name = "edge_fusion"
    
    def run(self, ir: GraphIR) -> PassResult:
        modified = False
        
        for graph in ir.graphs:
            fusible = self.find_fusible_pairs(graph)
            
            for node_a, node_b in fusible:
                self.fuse_nodes(graph, node_a, node_b)
                modified = True
        
        return PassResult(success=True, modified=modified)
    
    def find_fusible_pairs(self, graph):
        pairs = []
        for edge in graph.edges:
            node_a = graph.get_node(edge.from_node)
            node_b = graph.get_node(edge.to_node)
            
            if self.can_fuse(node_a, node_b):
                pairs.append((node_a, node_b))
        
        return pairs
    
    def can_fuse(self, a, b):
        # Nodes are fusible if:
        # - Both are task nodes
        # - Single edge between them
        # - No other incoming edges to b
        # - Same model configuration
        return (
            a.kind == "task" and 
            b.kind == "task" and
            a.config.get("model") == b.config.get("model")
        )
```

### 3. Model Cost Optimizer

Choose cheaper models when possible:

```python
class ModelCostOptimizerPass(Pass):
    name = "model_cost_optimizer"
    
    MODEL_COSTS = {
        "gpt-4o": 1.0,
        "gpt-4o-mini": 0.1,
        "gpt-3.5-turbo": 0.05,
    }
    
    def run(self, ir: GraphIR) -> PassResult:
        modified = False
        
        for graph in ir.graphs:
            for node in graph.nodes:
                if node.kind == "task" and "model" in node.config:
                    if self.can_downgrade(node):
                        node.config["model"] = self.suggest_model(node)
                        modified = True
        
        return PassResult(success=True, modified=modified)
    
    def can_downgrade(self, node):
        # Analyze task complexity
        prompt = node.config.get("prompt", "")
        
        # Simple heuristics
        is_simple = (
            len(prompt) < 500 and
            "complex" not in prompt.lower() and
            "reasoning" not in prompt.lower()
        )
        
        return is_simple
    
    def suggest_model(self, node):
        return "gpt-4o-mini"
```

### 4. Validation Pass

Enforce custom rules:

```python
class CustomValidationPass(Pass):
    name = "custom_validation"
    
    def run(self, ir: GraphIR) -> PassResult:
        diagnostics = []
        
        for graph in ir.graphs:
            # Rule 1: All graphs must have error handling
            if not self.has_error_handling(graph):
                diagnostics.append(
                    Diagnostic(
                        level="warning",
                        message=f"Graph '{graph.name}' lacks error handling",
                        location=graph.location
                    )
                )
            
            # Rule 2: Human review required for high-risk operations
            for node in graph.nodes:
                if self.is_high_risk(node) and not self.has_human_review(graph, node):
                    diagnostics.append(
                        Diagnostic(
                            level="error",
                            message=f"High-risk node '{node.id}' requires human review",
                            location=node.location
                        )
                    )
        
        success = not any(d.level == "error" for d in diagnostics)
        return PassResult(success=success, diagnostics=diagnostics)
```

---

## Using Custom Passes

### CLI

```bash
# Register pass in config
nexus config set passes.custom "./passes/my_pass.py:MyCustomPass"

# Run with custom pass
nexus compile manifest.yaml --target langgraph --passes custom
```

### Programmatic

```python
from nexus.compiler import Compiler
from my_passes import MyCustomPass

compiler = Compiler()
compiler.pass_manager.add_pass(MyCustomPass())

result = compiler.compile("manifest.yaml", target="langgraph")
```

### In manifest.yaml

```yaml
compiler:
  passes:
    - name: my_custom_pass
      enabled: true
      config:
        threshold: 0.5
```

---

## Testing Passes

```python
import pytest
from nexus.compiler.ir import GraphIR
from my_passes import MyCustomPass

def test_my_pass_transforms_correctly():
    # Create test IR
    ir = GraphIR.from_yaml("""
    graphs:
      - name: test
        entry_node: a
        nodes:
          - id: a
            kind: task
    """)
    
    # Run pass
    pass_instance = MyCustomPass()
    result = pass_instance.run(ir)
    
    # Assert
    assert result.success
    assert result.modified
    # Check transformations...

def test_my_pass_handles_edge_cases():
    # Empty graph
    ir = GraphIR.from_yaml("graphs: []")
    result = MyCustomPass().run(ir)
    assert result.success
    assert not result.modified
```

---

## Best Practices

1. **Single Responsibility** - Each pass should do one thing well
2. **Idempotent** - Running twice should have same result as once
3. **Preserve Semantics** - Transformations must not change behavior
4. **Report Diagnostics** - Provide helpful error/warning messages
5. **Test Thoroughly** - Unit test with various IR shapes
6. **Document** - Explain what the pass does and when to use it

---

## Next Steps

- [LangGraph Migration](langgraph-to-uaa.md)
- [AWS Migration](aws-to-uaa.md)
- [Examples](../)

