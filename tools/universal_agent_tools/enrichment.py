"""Composable enrichment handlers for tenant-aware compilation."""

from typing import Any, Dict, List, Optional

from universal_agent_nexus.enrichment import (
    ComposableEnrichmentStrategy,
    EnrichmentHandler,
    create_custom_enrichment_strategy,
)


class TenantIsolationHandler(EnrichmentHandler):
    """Inject tenant-specific metadata and policies."""

    def __init__(self, tenant_id: str, tenant_config: Dict[str, Any]):
        self.tenant_id = tenant_id
        self.tenant_config = tenant_config

    def handle(
        self,
        manifest: Dict[str, Any],
        role: Optional[Dict[str, Any]],
        domains: List[Dict[str, Any]],
        policies: List[Dict[str, Any]],
        mixins: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        manifest.setdefault("metadata", {})
        manifest["metadata"].update(
            {
                "tenant_id": self.tenant_id,
                "tenant_name": self.tenant_config.get("name"),
                "data_retention_days": self.tenant_config.get("retention"),
                "allowed_tools": self.tenant_config.get("tools", []),
            }
        )

        manifest.setdefault("policies", [])
        manifest["policies"].append(
            {
                "name": f"tenant_{self.tenant_id}_isolation",
                "target_pattern": "execute_*",
                "action": "add_tenant_context",
                "context": {
                    "tenant_id": self.tenant_id,
                    "isolated_db": f"tenant_{self.tenant_id}",
                },
            }
        )

        return manifest


class VectorDBIsolationHandler(EnrichmentHandler):
    """Map tools to tenant-specific vector stores."""

    def __init__(self, vector_store_mapping: Dict[str, str]):
        self.vector_store_mapping = vector_store_mapping

    def handle(
        self,
        manifest: Dict[str, Any],
        role: Optional[Dict[str, Any]],
        domains: List[Dict[str, Any]],
        policies: List[Dict[str, Any]],
        mixins: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if "tools" in manifest:
            for tool in manifest["tools"]:
                tenant_id = manifest.get("metadata", {}).get("tenant_id")
                if tenant_id and "vector_store" in tool.get("config", {}):
                    tool["config"]["vector_store"] = self.vector_store_mapping.get(
                        tenant_id, f"/vectorstores/{tenant_id}"
                    )

        return manifest


def create_tenant_agent(
    tenant_id: str,
    tenant_config: Dict[str, Any],
    base_manifest_path: str,
) -> str:
    """Compile a tenant-specific agent with isolated storage and policies."""
    from universal_agent_fabric import NexusEnricher
    from universal_agent_nexus.compiler import compile

    strategy: ComposableEnrichmentStrategy = create_custom_enrichment_strategy(
        handlers=[
            TenantIsolationHandler(tenant_id, tenant_config),
            VectorDBIsolationHandler({tenant_id: f"/vectorstores/{tenant_id}/embeddings.sqlite"}),
        ]
    )

    enricher = NexusEnricher(strategy=strategy)
    enriched_manifest_path = enricher.enrich(
        baseline_path=base_manifest_path,
        output_path=f"/tmp/enriched_{tenant_id}.yaml",
    )

    compiled_path = compile(
        enriched_manifest_path,
        target="langgraph",
        output=f"/agents/tenant_{tenant_id}_agent.py",
    )
    return compiled_path
