"""
GraphRAG Loader
=================
One-time (or repeatable) script that loads knowledge entries into Neo4j
as graph nodes, each with a vector embedding for semantic search.

Run it directly:
    python -m src.graphrag.loader
"""
from __future__ import annotations

from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

from src.common.config import settings
from src.common.logging import configure_logging, get_logger

configure_logging()
logger = get_logger("graphrag.loader")

# Same content as the old in-memory stub, now destined for the graph.
KNOWLEDGE_ENTRIES = [
    {
        "topic": "onboarding",
        "text": "New employees complete IT setup, HR paperwork, and a "
                 "security training within their first 5 business days.",
        "category": "HR",
    },
    {
        "topic": "vacation_policy",
        "text": "Full-time employees accrue 15 PTO days per year, "
                 "accrued monthly and capped at 30 days banked.",
        "category": "HR",
    },
    {
        "topic": "incident_response",
        "text": "Security incidents must be reported to the SOC within "
                 "1 hour of detection via the #incidents channel.",
        "category": "Security",
    },
]

EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # small, fast, runs locally, free
VECTOR_INDEX_NAME = "knowledge_embeddings"
VECTOR_DIMENSIONS = 384  # matches all-MiniLM-L6-v2 output size


def load_knowledge_graph() -> None:
    model = SentenceTransformer(EMBEDDING_MODEL)
    driver = GraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )

    with driver.session() as session:
        # Clear any previous run so this script is safely re-runnable
        session.run("MATCH (k:KnowledgeEntry) DETACH DELETE k")
        logger.info("cleared_existing_entries")

        # Create the vector index (safe to re-run, uses IF NOT EXISTS)
        session.run(
            f"""
            CREATE VECTOR INDEX {VECTOR_INDEX_NAME} IF NOT EXISTS
            FOR (k:KnowledgeEntry) ON (k.embedding)
            OPTIONS {{indexConfig: {{
                `vector.dimensions`: {VECTOR_DIMENSIONS},
                `vector.similarity_function`: 'cosine'
            }}}}
            """
        )
        logger.info("vector_index_ready", index=VECTOR_INDEX_NAME)

        for entry in KNOWLEDGE_ENTRIES:
            embedding = model.encode(entry["text"]).tolist()
            session.run(
                """
                CREATE (k:KnowledgeEntry {
                    topic: $topic,
                    text: $text,
                    category: $category,
                    embedding: $embedding
                })
                """,
                topic=entry["topic"],
                text=entry["text"],
                category=entry["category"],
                embedding=embedding,
            )
            logger.info("entry_loaded", topic=entry["topic"])

    driver.close()
    logger.info("graph_load_complete", count=len(KNOWLEDGE_ENTRIES))


if __name__ == "__main__":
    load_knowledge_graph()