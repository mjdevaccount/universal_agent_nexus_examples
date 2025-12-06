"""
Document Writer - Structured document generation with Plan-Execute pattern.

Pattern: Plan → Execute Steps → Compile
- Planner creates outline (deterministic structure)
- Executor fills each section (bounded iterations)
- Compiler saves final document

No churning because each phase has clear completion criteria.
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
    
    def __init__(self, title: str, sections: List[Dict]):
        self.title = title
        self.sections = sections  # [{id, heading, description}]
        self.content = {}  # section_id -> content
        self.created_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "sections": self.sections,
            "content": self.content,
            "created_at": self.created_at,
            "completed_sections": len(self.content),
            "total_sections": len(self.sections)
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

