"""
Translation workflow using LangGraph.

This workflow orchestrates the translation process including:
- Cache checking
- Language detection
- LLM translation
- Result caching and vector storage
"""

from typing import TypedDict, Optional, Literal
from langgraph.graph import StateGraph, END
import structlog

from src.utils.redis_client import redis_client
from src.utils.milvus_client import milvus_client
from src.utils.llm_client import llm_client
from src.utils.text_processing import compute_text_hash, detect_language
from src.core.exceptions import TranslationError

logger = structlog.get_logger(__name__)


class TranslationState(TypedDict):
    """State for translation workflow."""
    source_text: str
    target_lang: str
    source_lang: Optional[str]
    translated_text: Optional[str]
    cached: bool
    error: Optional[str]


def check_cache(state: TranslationState) -> TranslationState:
    """
    Check if translation exists in cache.

    Args:
        state: Current workflow state

    Returns:
        Updated state
    """
    try:
        # Generate cache key
        text_hash = compute_text_hash(state["source_text"])
        source_lang = state.get("source_lang") or "auto"
        cache_key = f"translation:{source_lang}:{state['target_lang']}:{text_hash}"

        # Check cache
        cached_result = redis_client.get(cache_key)

        if cached_result:
            logger.info(f"Cache hit for translation: {cache_key}")
            state["translated_text"] = cached_result["translated_text"]
            state["source_lang"] = cached_result["source_lang"]
            state["cached"] = True
        else:
            logger.info(f"Cache miss for translation: {cache_key}")
            state["cached"] = False

    except Exception as e:
        logger.error(f"Cache check error: {e}")
        state["cached"] = False

    return state


def detect_source_language(state: TranslationState) -> TranslationState:
    """
    Detect source language if not provided.

    Args:
        state: Current workflow state

    Returns:
        Updated state
    """
    if not state.get("source_lang"):
        try:
            detected_lang = detect_language(state["source_text"])
            state["source_lang"] = detected_lang
            logger.info(f"Detected source language: {detected_lang}")
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            state["source_lang"] = "en"  # Default fallback

    return state


def translate_text(state: TranslationState) -> TranslationState:
    """
    Translate text using LLM.

    Args:
        state: Current workflow state

    Returns:
        Updated state
    """
    try:
        translated = llm_client.translate_text(
            text=state["source_text"],
            target_lang=state["target_lang"],
            source_lang=state.get("source_lang")
        )

        state["translated_text"] = translated
        logger.info("Translation completed successfully")

    except Exception as e:
        logger.error(f"Translation error: {e}")
        state["error"] = str(e)

    return state


def store_cache_and_vector(state: TranslationState) -> TranslationState:
    """
    Store translation in cache and vector database.

    Args:
        state: Current workflow state

    Returns:
        Updated state
    """
    try:
        # Generate cache key
        text_hash = compute_text_hash(state["source_text"])
        cache_key = f"translation:{state['source_lang']}:{state['target_lang']}:{text_hash}"

        # Store in Redis cache
        cache_data = {
            "source_text": state["source_text"],
            "translated_text": state["translated_text"],
            "source_lang": state["source_lang"],
            "target_lang": state["target_lang"]
        }
        redis_client.set(cache_key, cache_data)
        logger.info(f"Stored translation in cache: {cache_key}")

        # Generate and store embedding in Milvus
        try:
            embedding = llm_client.get_embedding(state["source_text"])
            metadata = {
                "source_lang": state["source_lang"],
                "target_lang": state["target_lang"],
                "text_hash": text_hash
            }

            milvus_client.insert(
                collection_name="translations",
                embeddings=[embedding],
                texts=[state["translated_text"]],
                metadata=[metadata]
            )
            logger.info("Stored translation embedding in Milvus")

        except Exception as e:
            logger.error(f"Vector storage error: {e}")
            # Don't fail the workflow if vector storage fails

    except Exception as e:
        logger.error(f"Cache storage error: {e}")
        # Don't fail the workflow if caching fails

    return state


def should_translate(state: TranslationState) -> Literal["translate", "end"]:
    """
    Determine if translation is needed.

    Args:
        state: Current workflow state

    Returns:
        Next node to execute
    """
    if state["cached"]:
        return "end"
    return "translate"


def create_translation_workflow() -> StateGraph:
    """
    Create the translation workflow graph.

    Returns:
        Configured StateGraph
    """
    workflow = StateGraph(TranslationState)

    # Add nodes
    workflow.add_node("check_cache", check_cache)
    workflow.add_node("detect_language", detect_source_language)
    workflow.add_node("translate", translate_text)
    workflow.add_node("store", store_cache_and_vector)

    # Define edges
    workflow.set_entry_point("check_cache")
    workflow.add_conditional_edges(
        "check_cache",
        should_translate,
        {
            "translate": "detect_language",
            "end": END
        }
    )
    workflow.add_edge("detect_language", "translate")
    workflow.add_edge("translate", "store")
    workflow.add_edge("store", END)

    return workflow.compile()


# Create global workflow instance
translation_workflow = create_translation_workflow()
