# Enterprise Content Moderation Pipeline

## Overview

A sophisticated, production-ready content moderation system that models real business requirements with:

- **Multi-tier risk classification** (Safe, Low, Medium, High, Critical)
- **Policy compliance validation** with automated checks
- **Escalation workflows** with priority queues and SLAs
- **Audit logging** for compliance and traceability
- **Critical content handling** with immediate action and admin alerts

## Architecture

### Risk Assessment Flow

```
Content Input
    ↓
AI Risk Classifier (Router)
    ↓
┌───┴───┬──────┬──────┬──────┬──────────┐
│       │      │      │      │          │
Safe   Low   Medium  High  Critical
│       │      │      │      │
│       ↓      │      │      │
│   Policy    │      │      │
│   Check     │      │      │
│       ↓      │      │      │
│   Policy    │      │      │
│   Approve   │      │      │
│       │      │      │      │
│       └──────┴──────┴──────┘
│              │      │      │
│         Human   Auto   Critical
│         Review  Reject  Action
│              │      │      │
│              └──────┴──────┘
│                    │
│              Audit Log
│                    │
└────────────────────┘
```

## Node Descriptions

### 1. Risk Assessment (Router)
- **Type**: AI Router
- **Model**: Ollama qwen3:8b
- **Purpose**: Initial risk classification
- **Output**: One word (safe, low, medium, high, critical)

### 2. Auto Approve
- **Type**: Task
- **Action**: Immediate publication
- **Use Case**: Safe content that requires no review
- **Features**: Author notification enabled

### 3. Policy Check
- **Type**: Tool (HTTP)
- **Purpose**: Validate against community policies
- **Input**: Content, content type, user tier, policy version
- **Output**: Compliance status, violations list
- **Routes**:
  - Compliant → Policy Approve
  - Violation → Policy Failed (escalation)

### 4. Policy Approve
- **Type**: Task
- **Action**: Approve after policy validation
- **Use Case**: Low-risk content that passed policy check
- **Features**: Author notification

### 5. Human Review
- **Type**: Task
- **Action**: Escalate to moderation queue
- **Use Case**: Medium-risk content requiring human judgment
- **Features**:
  - Priority: Normal
  - SLA: 24 hours
  - Queue: `moderation_queue`

### 6. Auto Reject (High Risk)
- **Type**: Task
- **Action**: Reject with appeal option
- **Use Case**: High-risk violations
- **Features**:
  - Reason: `high_risk_violation`
  - Appeal allowed: Yes
  - Author notification: Yes

### 7. Critical Action
- **Type**: Task
- **Action**: Immediate critical handling
- **Use Case**: Illegal, dangerous, or platform-threatening content
- **Features**:
  - Immediate block: Yes
  - Admin notification: Yes
  - Legal escalation: Yes
  - Reason: `critical_violation`

### 8. Policy Failed
- **Type**: Task
- **Action**: Escalate to policy violation queue
- **Use Case**: Content that failed policy check
- **Features**:
  - Priority: High
  - SLA: 12 hours
  - Queue: `policy_violation_queue`

### 9. Audit Log
- **Type**: Task
- **Action**: Log all decisions for compliance
- **Purpose**: Compliance, traceability, analytics
- **Features**:
  - Retention: 365 days
  - All paths converge here

## Business Logic

### Risk Levels

| Level | Description | Action | SLA | Appeal |
|-------|-------------|--------|-----|--------|
| **Safe** | Clean, appropriate | Auto-approve | Immediate | N/A |
| **Low** | Minor concerns | Policy check → Approve | < 1 min | N/A |
| **Medium** | Moderate risk | Human review | 24 hours | Yes |
| **High** | Serious violation | Auto-reject | Immediate | Yes |
| **Critical** | Illegal/dangerous | Critical action + Legal | Immediate | No |

### Escalation Paths

1. **Normal Queue** (`moderation_queue`)
   - Medium-risk content
   - Priority: Normal
   - SLA: 24 hours

2. **Policy Violation Queue** (`policy_violation_queue`)
   - Failed policy checks
   - Priority: High
   - SLA: 12 hours

### Compliance Features

- **Audit Logging**: All decisions logged with full traceability
- **Retention**: 365 days (configurable)
- **Metadata**: Content, user, timestamp, decision path
- **Legal Escalation**: Automatic for critical content

## Testing

Run comprehensive tests:

```bash
python test_all_risk_levels.py
```

This tests all 5 risk levels with realistic content samples.

## Configuration

### Router Configuration

Located in `manifest.yaml` under `routers:`:

```yaml
routers:
  - name: risk_router
    strategy: llm
    system_message: |
      [Detailed classification instructions]
    default_model: "ollama://qwen3:8b"
```

### Policy Validator

HTTP tool that validates content against policies:

- **Endpoint**: Configurable via `POLICY_API_KEY` env var
- **Input Schema**: Content, content type, user tier, policy version
- **Output Schema**: Compliance status, violations, policy version

## Observability

- **OpenTelemetry**: Full tracing enabled
- **Jaeger UI**: View traces at http://localhost:16686
- **Service Name**: `content-moderation`
- **Traces Include**: Node execution, routing decisions, LLM calls

## Future Enhancements

1. **Machine Learning Feedback Loop**
   - Use audit logs to retrain risk classifier
   - Improve accuracy over time

2. **Multi-language Support**
   - Language detection
   - Language-specific policy checks

3. **User Reputation System**
   - Factor user history into risk assessment
   - Trusted users → faster approval

4. **A/B Testing**
   - Test different risk thresholds
   - Measure false positive/negative rates

5. **Real-time Monitoring**
   - Dashboard for moderation queue
   - Alert on SLA violations
   - Track decision distribution

## Production Considerations

1. **Rate Limiting**: Implement for policy validator API
2. **Caching**: Cache policy check results for similar content
3. **Retry Logic**: Handle transient failures in policy validator
4. **Monitoring**: Set up alerts for critical action triggers
5. **Scaling**: Queue-based architecture supports horizontal scaling

