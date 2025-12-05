# Migrating from AWS Step Functions to Universal Agent Architecture

**Convert AWS Step Functions state machines to UAA manifests.**

## Why Migrate?

✅ **Local development** - Test without deploying to AWS  
✅ **Multi-runtime** - Deploy to LangGraph, MCP, or back to AWS  
✅ **LLM integration** - First-class AI/ML support  
✅ **Simplified syntax** - YAML vs complex ASL JSON  

---

## Automatic Migration

```bash
# Translate ASL to UAA
nexus translate state_machine.json --from asl --to uaa --output manifest.yaml

# Or directly from deployed state machine
nexus translate --from aws \
  --state-machine-arn arn:aws:states:us-east-1:123456789:stateMachine:MyMachine \
  --output manifest.yaml
```

---

## Manual Migration Pattern

### Before (AWS ASL):

```json
{
  "StartAt": "FetchData",
  "States": {
    "FetchData": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789:function:fetch-data",
      "Next": "ProcessData"
    },
    "ProcessData": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789:function:process-data",
      "End": true
    }
  }
}
```

### After (UAA):

```yaml
name: data-workflow
version: "1.0.0"

graphs:
  - name: main
    entry_node: fetch_data
    nodes:
      - id: fetch_data
        kind: tool
        label: "Fetch Data"
        tool_ref: fetch_lambda
      
      - id: process_data
        kind: tool
        label: "Process Data"
        tool_ref: process_lambda
    
    edges:
      - from_node: fetch_data
        to_node: process_data
        condition:
          trigger: success

tools:
  - name: fetch_lambda
    protocol: aws_lambda
    config:
      function_arn: "arn:aws:lambda:us-east-1:123456789:function:fetch-data"
  
  - name: process_lambda
    protocol: aws_lambda
    config:
      function_arn: "arn:aws:lambda:us-east-1:123456789:function:process-data"
```

---

## State Type Mappings

| AWS State Type | UAA Equivalent |
|---------------|----------------|
| Task | `kind: tool` or `kind: task` |
| Choice | `kind: router` with edges |
| Parallel | Multiple edges from same node |
| Map | `kind: task` with `iterate: true` |
| Wait | `kind: task` with `delay` config |
| Pass | `kind: task` with `passthrough: true` |
| Succeed | Terminal node (no outgoing edges) |
| Fail | `kind: task` with `error` config |

---

## Common Patterns

### 1. Choice States (Routing)

**AWS ASL:**

```json
{
  "Type": "Choice",
  "Choices": [
    {
      "Variable": "$.status",
      "StringEquals": "approved",
      "Next": "ProcessApproved"
    },
    {
      "Variable": "$.status",
      "StringEquals": "rejected",
      "Next": "ProcessRejected"
    }
  ],
  "Default": "ProcessPending"
}
```

**UAA:**

```yaml
nodes:
  - id: route_status
    kind: router
    router_ref: status_router

edges:
  - from_node: route_status
    to_node: process_approved
    condition:
      expression: "status == 'approved'"
  
  - from_node: route_status
    to_node: process_rejected
    condition:
      expression: "status == 'rejected'"
  
  - from_node: route_status
    to_node: process_pending
    condition:
      expression: "status != 'approved' and status != 'rejected'"
```

### 2. Parallel Execution

**AWS ASL:**

```json
{
  "Type": "Parallel",
  "Branches": [
    {"StartAt": "Branch1", "States": {...}},
    {"StartAt": "Branch2", "States": {...}}
  ],
  "Next": "Aggregate"
}
```

**UAA:**

```yaml
nodes:
  - id: start_parallel
    kind: task
    config:
      parallel: true
      branches:
        - branch_1
        - branch_2
  
  - id: branch_1
    kind: task
    label: "Branch 1"
  
  - id: branch_2
    kind: task
    label: "Branch 2"
  
  - id: aggregate
    kind: task
    config:
      wait_for: [branch_1, branch_2]

edges:
  - from_node: start_parallel
    to_node: branch_1
  - from_node: start_parallel
    to_node: branch_2
  - from_node: branch_1
    to_node: aggregate
  - from_node: branch_2
    to_node: aggregate
```

### 3. Error Handling

**AWS ASL:**

```json
{
  "Type": "Task",
  "Resource": "...",
  "Retry": [
    {
      "ErrorEquals": ["States.Timeout"],
      "MaxAttempts": 3,
      "BackoffRate": 2
    }
  ],
  "Catch": [
    {
      "ErrorEquals": ["States.ALL"],
      "Next": "HandleError"
    }
  ]
}
```

**UAA:**

```yaml
nodes:
  - id: my_task
    kind: tool
    config:
      retry:
        max_attempts: 3
        backoff_rate: 2
        retryable_errors:
          - timeout
      on_error: handle_error
  
  - id: handle_error
    kind: task
    label: "Error Handler"
```

### 4. Map State (Iteration)

**AWS ASL:**

```json
{
  "Type": "Map",
  "Iterator": {
    "StartAt": "ProcessItem",
    "States": {
      "ProcessItem": {
        "Type": "Task",
        "Resource": "...",
        "End": true
      }
    }
  },
  "ItemsPath": "$.items"
}
```

**UAA:**

```yaml
nodes:
  - id: process_items
    kind: task
    config:
      iterate: true
      items_path: "items"
      max_concurrency: 10
      processor:
        model: "gpt-4o-mini"
        prompt: "Process this item: {item}"
```

---

## Lambda Integration

Keep using your existing Lambda functions:

```yaml
tools:
  - name: my_lambda
    protocol: aws_lambda
    config:
      function_arn: "arn:aws:lambda:us-east-1:123456789:function:my-func"
      # Optional: invoke config
      invocation_type: "RequestResponse"
      timeout: 30
```

Or migrate to inline tasks:

```yaml
nodes:
  - id: process
    kind: task
    config:
      model: "gpt-4o-mini"
      prompt: "Process this data: {input}"
```

---

## Deployment Back to AWS

After migration, deploy back to Step Functions:

```bash
# Compile to AWS
nexus compile manifest.yaml --target aws --output state_machine.json

# Deploy
aws stepfunctions update-state-machine \
  --state-machine-arn arn:aws:states:... \
  --definition file://state_machine.json
```

---

## Migration Checklist

- [ ] Export existing state machine definition
- [ ] Map states to UAA nodes
- [ ] Convert Choice states to routers + edges
- [ ] Extract Lambda references to tools
- [ ] Configure retry/error handling
- [ ] Test locally with LangGraph target
- [ ] Validate AWS deployment

---

## Next Steps

- [LangGraph Migration](langgraph-to-uaa.md)
- [Custom Optimization Passes](custom-optimization-passes.md)
- [Examples](../)

