"""
Document Writer - Enhanced structured document generation with Plan-Execute pattern.

Pattern: Preprocess → Plan → Multi-Pass Execute → Compile
- Preprocessing: Codebase analysis, clustering, dependency graphs
- Planner creates outline (deterministic structure)
- Multi-pass executor: Architecture → Modules → Examples
- Compiler saves final document

No churning because each phase has clear completion criteria.
Enhanced with Qwen-specific optimizations and multi-pass generation.
"""

from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import json

# Output directory for generated documents
OUTPUT_DIR = Path(__file__).parent.parent / "generated_docs"
OUTPUT_DIR.mkdir(exist_ok=True)


class DocumentPlan:
    """Structured document plan - prevents unbounded generation."""
    
    def __init__(self, title: str, sections: List[Dict], generation_mode: str = "standard"):
        self.title = title
        self.sections = sections  # [{id, heading, description}]
        self.content = {}  # section_id -> content
        self.created_at = datetime.utcnow().isoformat()
        self.generation_mode = generation_mode  # "standard" or "multi_pass"
        self.preprocessing_data = {}  # Store clustering, dependency graph, etc.
        self.pass_status = {
            "architecture": False,
            "modules": False,
            "examples": False
        }
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "sections": self.sections,
            "content": self.content,
            "created_at": self.created_at,
            "completed_sections": len(self.content),
            "total_sections": len(self.sections),
            "generation_mode": self.generation_mode,
            "pass_status": self.pass_status
        }


# In-memory plan storage (per-session)
_active_plan: Optional[DocumentPlan] = None


def create_document_plan(title: str, sections: List[Dict]) -> dict:
    """
    PHASE 1: Create a structured document plan.
    
    Args:
        title: Document title
        sections: List of {id, heading, description} for each section
    
    Returns plan summary. Call write_section for each section.
    """
    global _active_plan
    
    # Validate sections
    if not sections or len(sections) == 0:
        return {"error": "Must provide at least one section"}
    
    if len(sections) > 10:
        return {"error": "Maximum 10 sections to prevent churning"}
    
    # Create plan
    _active_plan = DocumentPlan(title, sections)
    
    return {
        "status": "plan_created",
        "title": title,
        "sections": [{"id": s["id"], "heading": s["heading"]} for s in sections],
        "next_step": f"Call write_section with section_id='{sections[0]['id']}' and content"
    }


def write_section(section_id: str, content: str) -> dict:
    """
    PHASE 2: Write content for a specific section.
    
    Args:
        section_id: ID of section from the plan
        content: Markdown content for this section
    
    Returns progress and next step.
    """
    global _active_plan
    
    if _active_plan is None:
        return {"error": "No active plan. Call create_document_plan first."}
    
    # Validate section exists
    section = next((s for s in _active_plan.sections if s["id"] == section_id), None)
    if not section:
        valid_ids = [s["id"] for s in _active_plan.sections]
        return {"error": f"Section '{section_id}' not in plan. Valid: {valid_ids}"}
    
    # Store content
    _active_plan.content[section_id] = content
    
    # Determine next step
    completed = len(_active_plan.content)
    total = len(_active_plan.sections)
    
    if completed >= total:
        return {
            "status": "all_sections_complete",
            "completed": completed,
            "total": total,
            "next_step": "Call compile_document to save the final document"
        }
    
    # Find next incomplete section
    for s in _active_plan.sections:
        if s["id"] not in _active_plan.content:
            return {
                "status": "section_written",
                "completed": completed,
                "total": total,
                "next_step": f"Call write_section with section_id='{s['id']}'"
            }
    
    return {"status": "ready_to_compile", "next_step": "Call compile_document"}


def compile_document(filename: str) -> dict:
    """
    PHASE 3: Compile all sections and save the document.
    
    Args:
        filename: Output filename (will be saved to generated_docs/)
    
    Returns path to saved document.
    """
    global _active_plan
    
    if _active_plan is None:
        return {"error": "No active plan. Call create_document_plan first."}
    
    # Check all sections are written
    missing = [s["id"] for s in _active_plan.sections if s["id"] not in _active_plan.content]
    if missing:
        return {
            "error": f"Missing sections: {missing}. Write them first.",
            "completed": len(_active_plan.content),
            "total": len(_active_plan.sections)
        }
    
    # Compile document
    lines = [f"# {_active_plan.title}", ""]
    lines.append(f"*Generated: {_active_plan.created_at}*")
    lines.append("")
    
    for section in _active_plan.sections:
        heading = section["heading"]
        content = _active_plan.content[section["id"]]
        
        lines.append(f"## {heading}")
        lines.append("")
        lines.append(content)
        lines.append("")
    
    document = "\n".join(lines)
    
    # Save
    if not filename.endswith(".md"):
        filename += ".md"
    
    output_path = OUTPUT_DIR / filename
    output_path.write_text(document, encoding="utf-8")
    
    # Clear plan
    saved_plan = _active_plan.to_dict()
    _active_plan = None
    
    return {
        "status": "document_saved",
        "path": str(output_path),
        "filename": filename,
        "sections_compiled": len(saved_plan["sections"]),
        "total_chars": len(document)
    }


def get_plan_status() -> dict:
    """Get current plan status."""
    global _active_plan
    
    if _active_plan is None:
        return {"status": "no_active_plan"}
    
    return _active_plan.to_dict()


def set_preprocessing_data(clusters: dict = None, dependency_graph: dict = None, 
                          pagerank_scores: dict = None) -> dict:
    """
    Store preprocessing data for multi-pass generation.
    Called after codebase analysis.
    """
    global _active_plan
    
    if _active_plan is None:
        return {"error": "Create a document plan first"}
    
    _active_plan.preprocessing_data = {
        "clusters": clusters or {},
        "dependency_graph": dependency_graph or {},
        "pagerank_scores": pagerank_scores or {}
    }
    
    return {
        "status": "preprocessing_data_stored",
        "clusters": bool(clusters),
        "dependency_graph": bool(dependency_graph),
        "pagerank_scores": bool(pagerank_scores)
    }


def get_qwen_prompt_template(pass_type: str, context: dict) -> str:
    """
    Generate Qwen-optimized prompts for different documentation passes.
    
    pass_type: "architecture", "module_detail", "code_examples"
    """
    base_system = "You are Qwen, created by Alibaba Cloud. You are a technical documentation expert who generates comprehensive, accurate API documentation with code examples."
    
    if pass_type == "architecture":
        clusters = context.get("clusters", {})
        dependency_graph = context.get("dependency_graph", {})
        top_files = context.get("top_files", [])
        
        prompt = f"""{base_system}

Analyze this codebase structure and generate a comprehensive architecture overview.

CODEBASE STRUCTURE:
{json.dumps(clusters, indent=2)[:2000]}...

DEPENDENCY GRAPH:
{json.dumps(dependency_graph, indent=2)[:2000]}...

TOP IMPORTANT FILES (by PageRank):
{json.dumps(top_files[:10], indent=2)[:1000]}...

Generate a comprehensive architecture overview covering:
1. System purpose and key capabilities
2. Major components and their responsibilities
3. Data flow and integration points
4. Technology stack and frameworks
5. Key design patterns used

Use clear markdown with diagrams (mermaid syntax where appropriate).
Be specific and reference actual module names and relationships.
"""
    
    elif pass_type == "module_detail":
        module_info = context.get("module_info", {})
        related_modules = context.get("related_modules", [])
        architecture_context = context.get("architecture_context", "")
        
        prompt = f"""{base_system}

Context from Architecture: {architecture_context[:500]}...

MODULE TO DOCUMENT:
{json.dumps(module_info, indent=2)[:3000]}...

RELATED MODULES:
{json.dumps(related_modules, indent=2)[:1000]}...

Generate detailed API documentation for this module:
1. Module purpose and use cases
2. Public API surface (classes, methods, endpoints)
3. Parameters, return types, exceptions
4. Code examples for each major function
5. Integration patterns

Format as professional API reference (like Swagger/OpenAPI style).
Be thorough but concise. Include actual code signatures.
"""
    
    elif pass_type == "code_examples":
        api_docs = context.get("api_docs", [])
        use_case = context.get("use_case", "common usage")
        
        prompt = f"""{base_system}

Based on this API documentation:
{json.dumps(api_docs, indent=2)[:2000]}...

Create practical code examples showing:
1. Authentication/initialization
2. Common use case: {use_case}
3. Error handling patterns
4. End-to-end workflow

Provide runnable Python code with explanations.
Make examples realistic and production-ready.
"""
    
    else:
        prompt = f"{base_system}\n\nGenerate documentation based on: {json.dumps(context, indent=2)[:1000]}..."
    
    return prompt


def create_multi_pass_plan(title: str, topic: str) -> dict:
    """
    Create a multi-pass document plan optimized for comprehensive documentation.
    
    Passes:
    1. Architecture overview
    2. Module-by-module detailed docs
    3. Code examples and tutorials
    """
    global _active_plan
    
    sections = [
        {
            "id": "architecture",
            "heading": "Architecture Overview",
            "description": "High-level system architecture, components, and design patterns",
            "pass": "architecture"
        },
        {
            "id": "core_modules",
            "heading": "Core Modules",
            "description": "Detailed documentation of core modules and their APIs",
            "pass": "modules"
        },
        {
            "id": "adapters",
            "heading": "Adapters and Integrations",
            "description": "Integration layer and adapter modules",
            "pass": "modules"
        },
        {
            "id": "tools",
            "heading": "Tools and Utilities",
            "description": "Tool definitions, MCP servers, and utility functions",
            "pass": "modules"
        },
        {
            "id": "examples",
            "heading": "Code Examples and Tutorials",
            "description": "Practical examples and usage patterns",
            "pass": "examples"
        }
    ]
    
    _active_plan = DocumentPlan(title, sections, generation_mode="multi_pass")
    
    return {
        "status": "multi_pass_plan_created",
        "title": title,
        "topic": topic,
        "sections": [{"id": s["id"], "heading": s["heading"], "pass": s["pass"]} for s in sections],
        "next_step": "Call set_preprocessing_data with analysis results, then start with architecture pass"
    }


# Tool definitions
TOOLS = [
    {
        "name": "create_document_plan",
        "description": "STEP 1: Create a document outline. Provide title and sections (max 10). Each section needs: id, heading, description.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Document title"},
                "sections": {
                    "type": "array",
                    "description": "List of sections with id, heading, description",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "heading": {"type": "string"},
                            "description": {"type": "string"}
                        }
                    }
                }
            },
            "required": ["title", "sections"]
        }
    },
    {
        "name": "write_section",
        "description": "STEP 2: Write content for one section. Call once per section in the plan.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "section_id": {"type": "string", "description": "Section ID from the plan"},
                "content": {"type": "string", "description": "Markdown content for this section"}
            },
            "required": ["section_id", "content"]
        }
    },
    {
        "name": "compile_document",
        "description": "STEP 3: Save the completed document. Call after all sections are written.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Output filename (saved to generated_docs/)"}
            },
            "required": ["filename"]
        }
    },
    {
        "name": "get_plan_status",
        "description": "Check current document plan status",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "set_preprocessing_data",
        "description": "Store preprocessing data (clusters, dependency graph, PageRank scores) for multi-pass generation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "clusters": {"type": "object", "description": "Semantic clusters from codebase analysis"},
                "dependency_graph": {"type": "object", "description": "Dependency graph data"},
                "pagerank_scores": {"type": "object", "description": "PageRank importance scores"}
            }
        }
    },
    {
        "name": "create_multi_pass_plan",
        "description": "Create a multi-pass document plan (Architecture → Modules → Examples) for comprehensive documentation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Document title"},
                "topic": {"type": "string", "description": "Document topic/theme"}
            },
            "required": ["title", "topic"]
        }
    },
    {
        "name": "get_qwen_prompt_template",
        "description": "Get Qwen-optimized prompt template for a specific documentation pass",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pass_type": {"type": "string", "enum": ["architecture", "module_detail", "code_examples"], 
                             "description": "Type of documentation pass"},
                "context": {"type": "object", "description": "Context data for the prompt"}
            },
            "required": ["pass_type", "context"]
        }
    }
]


if __name__ == "__main__":
    # Test the pattern
    print("Testing Plan-Execute pattern...")
    
    # Phase 1: Create plan
    result = create_document_plan(
        title="Test Document",
        sections=[
            {"id": "intro", "heading": "Introduction", "description": "Overview"},
            {"id": "body", "heading": "Main Content", "description": "Details"},
            {"id": "conclusion", "heading": "Conclusion", "description": "Summary"}
        ]
    )
    print(f"Plan created: {result}")
    
    # Phase 2: Write sections
    result = write_section("intro", "This is the introduction.")
    print(f"Section 1: {result}")
    
    result = write_section("body", "This is the main content.")
    print(f"Section 2: {result}")
    
    result = write_section("conclusion", "This is the conclusion.")
    print(f"Section 3: {result}")
    
    # Phase 3: Compile
    result = compile_document("test_document")
    print(f"Compiled: {result}")

