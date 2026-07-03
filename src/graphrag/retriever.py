"""
GraphRAG Retriever
=====================
Semantic search over the knowledge graph: embeds a query and finds the
most similar KnowledgeEntry nodes in Neo4j using the vector index.
"""
from __future__ import annotations

from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

from src.common.config import settings
from src.common.logging import get_logger
from src.graphrag.loader import EMBEDDING_MODEL, VECTOR_INDEX_NAME

logger = get_logger("graphrag.retriever")

_model: SentenceTransformer | None = None
_driver = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def _get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
    return _driver


def semantic_search(query: str, top_k: int = 1) -> list[dict]:
    """Find the most semantically similar knowledge entries to a query.

    Args:
        query: Natural-language search query.
        top_k: How many top matches to return.

    Returns:
        A list of dicts with 'topic', 'text', 'category', and 'score'.
    """
    model = _get_model()
    driver = _get_driver()
    query_embedding = model.encode(query).tolist()

    with driver.session() as session:
        result = session.run(
            f"""
            CALL db.index.vector.queryNodes(
                '{VECTOR_INDEX_NAME}', $top_k, $embedding
            )
            YIELD node, score
            RETURN node.topic AS topic, node.text AS text,
                   node.category AS category, score
            """,
            top_k=top_k,
            embedding=query_embedding,
        )
        matches = [dict(record) for record in result]

    logger.info("semantic_search", query=query, matches_found=len(matches))
    return matches