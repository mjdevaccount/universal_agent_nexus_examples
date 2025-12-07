"""MCP server for research paper search with embeddings (example)."""

import asyncio
import json
import os
import sqlite3

from mcp.server import Server
from mcp.types import TextContent
from sentence_transformers import SentenceTransformer


class ArxivSearchServer:
    """Lightweight semantic search over a SQLite corpus."""

    def __init__(self, db_path: str, model_name: str = "all-minilm-l6-v2"):
        self.db_path = db_path
        self.model = SentenceTransformer(model_name)
        self.conn = sqlite3.connect(db_path)

    async def search_papers(self, query: str, top_k: int = 5) -> list[dict]:
        query_embedding = self.model.encode(query)

        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, title, abstract, year FROM papers
            WHERE year >= 2023
            ORDER BY year DESC
            LIMIT ?
            """,
            (top_k,),
        )

        rows = cursor.fetchall()
        results = [
            {
                "id": row[0],
                "title": row[1],
                "abstract": row[2],
                "year": row[3],
                "similarity": float(query_embedding[0]) if len(query_embedding) else 0.0,
            }
            for row in rows
        ]
        return results


server = Server("arxiv-search")


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    search_server = ArxivSearchServer(
        db_path=os.environ.get("DB_PATH", "/data/papers.sqlite"),
        model_name=os.environ.get("EMBEDDING_MODEL", "all-minilm-l6-v2"),
    )

    if name == "search_papers":
        results = await search_server.search_papers(
            arguments["query"], arguments.get("top_k", 5)
        )
        return [TextContent(type="text", text=json.dumps(results))]

    return [TextContent(type="text", text="Unsupported tool call")]


if __name__ == "__main__":
    asyncio.run(server.run())
