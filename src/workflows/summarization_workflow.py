"""
Summarization workflow using LangGraph.

This workflow orchestrates the summarization process including:
- Content loading
- Text chunking
- Embedding generation
- Map-reduce summarization
- Keyword extraction
"""

from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph, END
import time
import structlog

from src.utils.llm_client import llm_client
from src.utils.milvus_client import milvus_client
from src.utils.text_processing import chunk_text, clean_text
from src.core.exceptions import SummarizationError

logger = structlog.get_logger(__name__)


class SummarizationState(TypedDict):
    """State for summarization workflow."""
    content: str
    content_type: str  # chat, message, document
    chunks: List[str]
    chunk_summaries: List[str]
    summary: Optional[str]
    keywords: List[str]
    error: Optional[str]
    start_time: float


def prepare_content(state: SummarizationState) -> SummarizationState:
    """
    Prepare and clean content.

    Args:
        state: Current workflow state

    Returns:
        Updated state
    """
    try:
        state["start_time"] = time.time()
        state["content"] = clean_text(state["content"])
        logger.info(f"Prepared content: {len(state['content'])} characters")

    except Exception as e:
        logger.error(f"Content preparation error: {e}")
        state["error"] = str(e)

    return state


def chunk_content(state: SummarizationState) -> SummarizationState:
    """
    Split content into chunks.

    Args:
        state: Current workflow state

    Returns:
        Updated state
    """
    try:
        # If content is short enough, use as single chunk
        if len(state["content"]) < 3000:
            state["chunks"] = [state["content"]]
        else:
            # Chunk with overlap for better context
            state["chunks"] = chunk_text(
                state["content"],
                chunk_size=2000,
                overlap=200
            )

        logger.info(f"Split content into {len(state['chunks'])} chunks")

    except Exception as e:
        logger.error(f"Chunking error: {e}")
        state["error"] = str(e)

    return state


def embed_chunks(state: SummarizationState) -> SummarizationState:
    """
    Generate embeddings and store in Milvus.

    Args:
        state: Current workflow state

    Returns:
        Updated state
    """
    try:
        # Generate embeddings for all chunks
        embeddings = llm_client.get_embeddings_batch(state["chunks"])

        # Store in Milvus
        metadata = [
            {
                "content_type": state["content_type"],
                "chunk_index": i
            }
            for i in range(len(state["chunks"]))
        ]

        milvus_client.insert(
            collection_name="document_chunks",
            embeddings=embeddings,
            texts=state["chunks"],
            metadata=metadata
        )

        logger.info(f"Stored {len(embeddings)} chunk embeddings in Milvus")

    except Exception as e:
        logger.error(f"Embedding storage error: {e}")
        # Don't fail the workflow if vector storage fails

    return state


def map_summarize(state: SummarizationState) -> SummarizationState:
    """
    Summarize each chunk (Map phase).

    Args:
        state: Current workflow state

    Returns:
        Updated state
    """
    try:
        chunk_summaries = []

        # If only one chunk, skip map phase
        if len(state["chunks"]) == 1:
            state["chunk_summaries"] = state["chunks"]
            return state

        # Summarize each chunk
        for i, chunk in enumerate(state["chunks"]):
            try:
                summary = llm_client.summarize_text(chunk, max_length=100)
                chunk_summaries.append(summary)
                logger.info(f"Summarized chunk {i + 1}/{len(state['chunks'])}")
            except Exception as e:
                logger.error(f"Error summarizing chunk {i}: {e}")
                chunk_summaries.append(chunk[:200])  # Fallback to truncation

        state["chunk_summaries"] = chunk_summaries

    except Exception as e:
        logger.error(f"Map summarization error: {e}")
        state["error"] = str(e)

    return state


def reduce_summarize(state: SummarizationState) -> SummarizationState:
    """
    Combine chunk summaries into final summary (Reduce phase).

    Args:
        state: Current workflow state

    Returns:
        Updated state
    """
    try:
        # If we have chunk summaries, combine them
        if len(state["chunk_summaries"]) > 1:
            combined = "\n\n".join(state["chunk_summaries"])
            final_summary = llm_client.summarize_text(combined, max_length=200)
        else:
            # Single chunk, summarize directly
            final_summary = llm_client.summarize_text(
                state["chunk_summaries"][0],
                max_length=200
            )

        state["summary"] = final_summary
        logger.info("Generated final summary")

    except Exception as e:
        logger.error(f"Reduce summarization error: {e}")
        state["error"] = str(e)

    return state


def extract_keywords(state: SummarizationState) -> SummarizationState:
    """
    Extract keywords from content.

    Args:
        state: Current workflow state

    Returns:
        Updated state
    """
    try:
        # Extract keywords from original content or summary
        text_to_analyze = state["content"] if len(state["content"]) < 5000 else state.get("summary", state["content"])

        keywords = llm_client.extract_keywords(
            text_to_analyze,
            num_keywords=5
        )

        state["keywords"] = keywords
        logger.info(f"Extracted {len(keywords)} keywords")

    except Exception as e:
        logger.error(f"Keyword extraction error: {e}")
        state["keywords"] = []

    return state


def create_summarization_workflow() -> StateGraph:
    """
    Create the summarization workflow graph.

    Returns:
        Configured StateGraph
    """
    workflow = StateGraph(SummarizationState)

    # Add nodes
    workflow.add_node("prepare", prepare_content)
    workflow.add_node("chunk", chunk_content)
    workflow.add_node("embed", embed_chunks)
    workflow.add_node("map", map_summarize)
    workflow.add_node("reduce", reduce_summarize)
    workflow.add_node("keywords", extract_keywords)

    # Define edges
    workflow.set_entry_point("prepare")
    workflow.add_edge("prepare", "chunk")
    workflow.add_edge("chunk", "embed")
    workflow.add_edge("embed", "map")
    workflow.add_edge("map", "reduce")
    workflow.add_edge("reduce", "keywords")
    workflow.add_edge("keywords", END)

    return workflow.compile()


# Create global workflow instance
summarization_workflow = create_summarization_workflow()
