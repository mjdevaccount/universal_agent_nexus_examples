"""Tenant-aware enrichment strategy backed by reusable toolkit primitives."""

from tools.universal_agent_tools.enrichment import (
    TenantIsolationHandler,
    VectorDBIsolationHandler,
    create_tenant_agent,
)

__all__ = [
    "TenantIsolationHandler",
    "VectorDBIsolationHandler",
    "create_tenant_agent",
]


if __name__ == "__main__":
    tenants = {
        "acme-corp": {
            "name": "ACME Corporation",
            "retention": 90,
            "tools": ["database", "research", "email"],
        },
        "globex-inc": {
            "name": "Globex Inc",
            "retention": 30,
            "tools": ["database", "spreadsheet"],
        },
    }

    for tenant_id, config in tenants.items():
        path = create_tenant_agent(
            tenant_id=tenant_id,
            tenant_config=config,
            base_manifest_path="manifest.yaml",
        )
        print(f"✓ Created agent for {tenant_id}: {path}")
