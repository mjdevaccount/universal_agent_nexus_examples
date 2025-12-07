"""
Codebase Analyzer
Intelligent preprocessing for documentation generation:
- AST parsing for structural analysis
- Semantic clustering
- Dependency graph building
- PageRank-style importance scoring
"""

import ast
import json
import re
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path
import hashlib

try:
    from chunk_manager import load_sync_state, get_file_type
except ImportError:
    from .chunk_manager import load_sync_state, get_file_type


class CodebaseAnalyzer:
    """Analyzes codebase structure for intelligent documentation generation."""
    
    def __init__(self):
        self.sync_state = load_sync_state()
        self.structure_cache = {}
        self.dependency_graph = defaultdict(set)  # file -> {imported_files}
        self.reverse_deps = defaultdict(set)  # file -> {files_that_import_this}
        self.file_metadata = {}  # file_path -> {classes, functions, imports, complexity}
    
    def analyze_structure(self, repo: Optional[str] = None) -> dict:
        """
        Stage 1: Structural Analysis
        Parse AST for all files, extract classes, methods, signatures, dependencies.
        """
        print("🔍 Analyzing codebase structure...")
        
        repos_to_analyze = [repo] if repo else list(self.sync_state.get("repos", {}).keys())
        
        all_files = []
        for repo_name in repos_to_analyze:
            repo_data = self.sync_state.get("repos", {}).get(repo_name, {})
            files = repo_data.get("files", {})
            
            for file_path, file_info in files.items():
                full_path = f"{repo_name}/{file_path}"
                all_files.append({
                    "repo": repo_name,
                    "path": file_path,
                    "full_path": full_path,
                    "sha": file_info.get("github_sha"),
                    "chunks": file_info.get("chunks", 0)
                })
        
        # Analyze each file
        for file_info in all_files:
            file_path = file_info["full_path"]
            file_type = get_file_type(file_info["path"])
            
            if file_type == "python":
                metadata = self._analyze_python_file(file_info)
                if metadata:
                    self.file_metadata[file_path] = metadata
                    # Build dependency graph
                    for imp in metadata.get("imports", []):
                        self.dependency_graph[file_path].add(imp)
                        self.reverse_deps[imp].add(file_path)
        
        # Calculate complexity scores
        for file_path in self.file_metadata:
            self.file_metadata[file_path]["complexity"] = self._calculate_complexity(
                self.file_metadata[file_path]
            )
        
        return {
            "files_analyzed": len(self.file_metadata),
            "total_files": len(all_files),
            "dependency_graph_size": len(self.dependency_graph),
            "metadata": self.file_metadata
        }
    
    def _analyze_python_file(self, file_info: dict) -> Optional[dict]:
        """Analyze a Python file using AST."""
        repo = file_info["repo"]
        path = file_info["path"]
        
        # Try to get file content from Qdrant
        try:
            # Import here to avoid circular dependency at module level
            try:
                from chunk_manager import get_file_chunks
            except ImportError:
                from .chunk_manager import get_file_chunks
            chunks_result = get_file_chunks(repo, path)
            
            if "error" in chunks_result or not chunks_result.get("chunks"):
                # Fallback: return basic metadata
                return {
                    "classes": [],
                    "functions": [],
                    "imports": [],
                    "line_count": file_info.get("chunks", 0) * 50
                }
            
            # Reconstruct file content from chunks
            chunks = chunks_result.get("chunks", [])
            content = ""
            for chunk in chunks:
                chunk_content = chunk.get("content", "")
                if chunk_content:
                    content += chunk_content + "\n\n"
            
            if not content:
                return {
                    "classes": [],
                    "functions": [],
                    "imports": [],
                    "line_count": 0
                }
            
            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError:
                return {
                    "classes": [],
                    "functions": [],
                    "imports": [],
                    "line_count": len(content.split('\n'))
                }
            
            classes = []
            functions = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    classes.append({
                        "name": node.name,
                        "line": node.lineno,
                        "methods": methods,
                        "docstring": ast.get_docstring(node) or ""
                    })
                elif isinstance(node, ast.FunctionDef):
                    # Only top-level functions
                    is_in_class = False
                    for parent in ast.walk(tree):
                        if isinstance(parent, ast.ClassDef):
                            if any(node == item for item in parent.body if isinstance(item, ast.FunctionDef)):
                                is_in_class = True
                                break
                    if not is_in_class:
                        functions.append({
                            "name": node.name,
                            "line": node.lineno,
                            "args": [arg.arg for arg in node.args.args],
                            "docstring": ast.get_docstring(node) or ""
                        })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}" if module else alias.name)
            
            return {
                "classes": classes,
                "functions": functions,
                "imports": imports,
                "line_count": len(content.split('\n'))
            }
        
        except Exception as e:
            # Fallback on any error
            return {
                "classes": [],
                "functions": [],
                "imports": [],
                "line_count": file_info.get("chunks", 0) * 50
            }
            
            try:
                tree = ast.parse(content)
            except SyntaxError:
                return None
            
            classes = []
            functions = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    classes.append({
                        "name": node.name,
                        "line": node.lineno,
                        "methods": methods,
                        "docstring": ast.get_docstring(node) or ""
                    })
                elif isinstance(node, ast.FunctionDef):
                    # Only top-level functions
                    if not any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree) 
                              if hasattr(parent, 'body') and node in parent.body):
                        functions.append({
                            "name": node.name,
                            "line": node.lineno,
                            "args": [arg.arg for arg in node.args.args],
                            "docstring": ast.get_docstring(node) or ""
                        })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}" if module else alias.name)
            
            return {
                "classes": classes,
                "functions": functions,
                "imports": imports,
                "line_count": len(content.split('\n'))
            }
        
        except Exception as e:
            print(f"Error analyzing {path}: {e}")
            return None
    
    def _calculate_complexity(self, metadata: dict) -> int:
        """Calculate complexity score (simple heuristic)."""
        score = 0
        score += len(metadata.get("classes", [])) * 5
        score += len(metadata.get("functions", [])) * 2
        score += metadata.get("line_count", 0) // 50
        return score
    
    def create_semantic_clusters(self, max_clusters: int = 10) -> dict:
        """
        Stage 2: Semantic Clustering
        Group related components (database layer, API controllers, utilities).
        """
        print("📦 Creating semantic clusters...")
        
        if not self.file_metadata:
            return {"error": "Run analyze_structure first"}
        
        # Simple clustering based on path patterns and dependencies
        clusters = defaultdict(list)
        
        for file_path, metadata in self.file_metadata.items():
            # Determine cluster by path patterns
            cluster_name = self._infer_cluster(file_path, metadata)
            clusters[cluster_name].append({
                "file": file_path,
                "metadata": metadata
            })
        
        # If too many clusters, merge small ones
        if len(clusters) > max_clusters:
            clusters = self._merge_small_clusters(clusters, max_clusters)
        
        # Generate cluster summaries
        cluster_summaries = {}
        for cluster_name, files in clusters.items():
            cluster_summaries[cluster_name] = {
                "name": cluster_name,
                "files": [f["file"] for f in files],
                "file_count": len(files),
                "total_classes": sum(len(f["metadata"].get("classes", [])) for f in files),
                "total_functions": sum(len(f["metadata"].get("functions", [])) for f in files),
                "description": self._generate_cluster_description(cluster_name, files)
            }
        
        return {
            "clusters": cluster_summaries,
            "total_clusters": len(cluster_summaries)
        }
    
    def _infer_cluster(self, file_path: str, metadata: dict) -> str:
        """Infer cluster name from file path and content."""
        path_lower = file_path.lower()
        
        # Pattern matching
        if "adapter" in path_lower or "adapters" in path_lower:
            return "adapters"
        elif "runtime" in path_lower or "agent" in path_lower:
            return "runtime"
        elif "compiler" in path_lower or "compile" in path_lower:
            return "compiler"
        elif "tool" in path_lower or "mcp" in path_lower:
            return "tools"
        elif "test" in path_lower:
            return "tests"
        elif "config" in path_lower or "yaml" in path_lower or "yaml" in path_lower:
            return "configuration"
        elif "doc" in path_lower or "readme" in path_lower:
            return "documentation"
        elif "server" in path_lower or "api" in path_lower:
            return "api"
        else:
            # Check imports for hints
            imports = metadata.get("imports", [])
            if any("fastapi" in imp.lower() or "flask" in imp.lower() for imp in imports):
                return "api"
            elif any("pytest" in imp.lower() or "unittest" in imp.lower() for imp in imports):
                return "tests"
            else:
                return "core"
    
    def _merge_small_clusters(self, clusters: dict, max_clusters: int) -> dict:
        """Merge small clusters into 'other' category."""
        sorted_clusters = sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)
        result = {}
        
        # Keep top N-1 clusters
        for i, (name, files) in enumerate(sorted_clusters[:max_clusters - 1]):
            result[name] = files
        
        # Merge rest into "other"
        other_files = []
        for name, files in sorted_clusters[max_clusters - 1:]:
            other_files.extend(files)
        
        if other_files:
            result["other"] = other_files
        
        return result
    
    def _generate_cluster_description(self, cluster_name: str, files: List[dict]) -> str:
        """Generate a natural language description of a cluster."""
        file_count = len(files)
        total_classes = sum(len(f["metadata"].get("classes", [])) for f in files)
        total_functions = sum(len(f["metadata"].get("functions", [])) for f in files)
        
        descriptions = {
            "adapters": f"Integration layer with {file_count} adapter modules",
            "runtime": f"Agent runtime and execution engine ({file_count} files)",
            "compiler": f"Code generation and compilation logic",
            "tools": f"Tool definitions and MCP servers ({file_count} files)",
            "tests": f"Test suite with {file_count} test files",
            "configuration": f"Configuration and manifest files",
            "documentation": f"Documentation and README files",
            "api": f"API endpoints and server definitions",
            "core": f"Core functionality ({file_count} files, {total_classes} classes, {total_functions} functions)",
            "other": f"Miscellaneous files ({file_count} files)"
        }
        
        return descriptions.get(cluster_name, f"{cluster_name} cluster with {file_count} files")
    
    def build_dependency_graph(self) -> dict:
        """
        Build dependency graph showing what imports what.
        Returns adjacency list representation.
        """
        print("🔗 Building dependency graph...")
        
        graph = {}
        for file_path in self.file_metadata.keys():
            graph[file_path] = {
                "imports": list(self.dependency_graph.get(file_path, set())),
                "imported_by": list(self.reverse_deps.get(file_path, set())),
                "in_degree": len(self.reverse_deps.get(file_path, set())),
                "out_degree": len(self.dependency_graph.get(file_path, set()))
            }
        
        return {
            "nodes": len(graph),
            "edges": sum(len(v["imports"]) for v in graph.values()),
            "graph": graph
        }
    
    def calculate_pagerank_scores(self, iterations: int = 10) -> dict:
        """
        Stage 3: PageRank-style Importance Scoring
        Identify "hub" modules that many others depend on.
        """
        print("📊 Calculating PageRank scores...")
        
        if not self.dependency_graph:
            return {"error": "Build dependency graph first"}
        
        # Initialize scores
        nodes = set(self.file_metadata.keys())
        scores = {node: 1.0 for node in nodes}
        
        # PageRank algorithm (simplified)
        damping = 0.85
        
        for _ in range(iterations):
            new_scores = {}
            for node in nodes:
                score = (1 - damping) / len(nodes)
                
                # Sum contributions from nodes that link to this one
                for incoming in self.reverse_deps.get(node, set()):
                    if incoming in nodes:
                        out_degree = len(self.dependency_graph.get(incoming, set()))
                        if out_degree > 0:
                            score += damping * scores[incoming] / out_degree
                
                new_scores[node] = score
            
            scores = new_scores
        
        # Normalize and combine with complexity
        max_score = max(scores.values()) if scores.values() else 1.0
        final_scores = {}
        
        for node in nodes:
            pagerank = scores[node] / max_score if max_score > 0 else 0
            complexity = self.file_metadata.get(node, {}).get("complexity", 0)
            # Combined score (weighted)
            final_scores[node] = {
                "pagerank": pagerank,
                "complexity": complexity,
                "combined": pagerank * 0.6 + (complexity / 100) * 0.4,  # Normalize complexity
                "in_degree": len(self.reverse_deps.get(node, set())),
                "out_degree": len(self.dependency_graph.get(node, set()))
            }
        
        # Sort by combined score
        top_files = sorted(
            final_scores.items(),
            key=lambda x: x[1]["combined"],
            reverse=True
        )[:20]  # Top 20
        
        return {
            "scores": final_scores,
            "top_files": [{"file": f, "score": s} for f, s in top_files],
            "total_files": len(final_scores)
        }
    
    def get_modules(self, repo: Optional[str] = None) -> List[dict]:
        """Get all modules (files) for a repository."""
        modules = []
        
        repos_to_get = [repo] if repo else list(self.sync_state.get("repos", {}).keys())
        
        for repo_name in repos_to_get:
            repo_data = self.sync_state.get("repos", {}).get(repo_name, {})
            files = repo_data.get("files", {})
            
            for file_path, file_info in files.items():
                full_path = f"{repo_name}/{file_path}"
                if full_path in self.file_metadata:
                    modules.append({
                        "repo": repo_name,
                        "path": file_path,
                        "full_path": full_path,
                        "metadata": self.file_metadata[full_path]
                    })
        
        return modules


# Global analyzer instance
_analyzer = None


def get_analyzer() -> CodebaseAnalyzer:
    """Get or create global analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = CodebaseAnalyzer()
    return _analyzer


def analyze_codebase_structure(repo: Optional[str] = None) -> dict:
    """Tool: Analyze codebase structure."""
    analyzer = get_analyzer()
    result = analyzer.analyze_structure(repo)
    return result


def create_semantic_clusters(max_clusters: int = 10) -> dict:
    """Tool: Create semantic clusters."""
    analyzer = get_analyzer()
    if not analyzer.file_metadata:
        return {"error": "Run analyze_codebase_structure first"}
    return analyzer.create_semantic_clusters(max_clusters)


def build_dependency_graph() -> dict:
    """Tool: Build dependency graph."""
    analyzer = get_analyzer()
    if not analyzer.file_metadata:
        return {"error": "Run analyze_codebase_structure first"}
    return analyzer.build_dependency_graph()


def calculate_pagerank_scores(iterations: int = 10) -> dict:
    """Tool: Calculate PageRank scores."""
    analyzer = get_analyzer()
    if not analyzer.file_metadata:
        return {"error": "Run analyze_codebase_structure first"}
    return analyzer.calculate_pagerank_scores(iterations)


def get_codebase_modules(repo: Optional[str] = None) -> dict:
    """Tool: Get all modules."""
    analyzer = get_analyzer()
    if not analyzer.file_metadata:
        return {"error": "Run analyze_codebase_structure first"}
    modules = analyzer.get_modules(repo)
    return {"modules": modules, "count": len(modules)}


# Tool definitions for MCP server
TOOLS = [
    {
        "name": "analyze_codebase_structure",
        "description": "PREPROCESSING STEP 1: Analyze codebase structure using AST parsing. Extracts classes, functions, imports, and dependencies.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Optional: specific repo to analyze, or all repos if omitted"}
            }
        }
    },
    {
        "name": "create_semantic_clusters",
        "description": "PREPROCESSING STEP 2: Group related components into semantic clusters (adapters, runtime, tools, etc.)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "max_clusters": {"type": "integer", "description": "Maximum number of clusters (default: 10)"}
            }
        }
    },
    {
        "name": "build_dependency_graph",
        "description": "PREPROCESSING STEP 3: Build dependency graph showing what imports what",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "calculate_pagerank_scores",
        "description": "PREPROCESSING STEP 4: Calculate PageRank-style importance scores to identify hub modules",
        "inputSchema": {
            "type": "object",
            "properties": {
                "iterations": {"type": "integer", "description": "Number of PageRank iterations (default: 10)"}
            }
        }
    },
    {
        "name": "get_codebase_modules",
        "description": "Get all modules (files) with their metadata for documentation generation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Optional: specific repo, or all repos if omitted"}
            }
        }
    }
]


if __name__ == "__main__":
    # Test the analyzer
    analyzer = CodebaseAnalyzer()
    
    print("Testing codebase analyzer...")
    result = analyzer.analyze_structure()
    print(f"Analyzed {result['files_analyzed']} files")
    
    clusters = analyzer.create_semantic_clusters()
    print(f"Created {clusters['total_clusters']} clusters")
    
    graph = analyzer.build_dependency_graph()
    print(f"Dependency graph: {graph['nodes']} nodes, {graph['edges']} edges")
    
    scores = analyzer.calculate_pagerank_scores()
    print(f"Top files by importance:")
    for item in scores['top_files'][:5]:
        print(f"  - {item['file']}: {item['score']['combined']:.3f}")

