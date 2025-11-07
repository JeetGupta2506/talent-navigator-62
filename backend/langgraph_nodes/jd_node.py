"""LangGraph node wrapper for the `jd_analyzer` function.

This module exposes an async callable `jd_analyzer_node(state)` which simply delegates
to `backend.jd_analyzer.jd_analyzer`. It also attempts to register the function with
the `langgraph` package if a registration decorator is available.

The defensive approach below ensures the module still works as a plain importable
callable even if LangGraph's Python API is not present or differs in naming.
"""
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)

try:
    from backend.jd_analyzer import jd_analyzer as _jd_analyzer  # type: ignore
except Exception as e:
    logger.exception("Failed to import jd_analyzer: %s", e)
    raise


async def jd_analyzer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Primary LangGraph node function that delegates to backend.jd_analyzer.jd_analyzer.

    Args:
        state: dictionary containing at least the key 'job_description'.

    Returns:
        A dictionary with the single key 'jd_analysis' whose value is the parsed data.
    """
    return await _jd_analyzer(state)


# Attempt to auto-register with langgraph if a suitable decorator is available.
try:
    import langgraph as _lg  # type: ignore

    # Try common decorator names (this is defensive; LangGraph's API may change).
    _decorator = getattr(_lg, "node", None) or getattr(_lg, "register_node", None) or getattr(_lg, "make_node", None)
    if _decorator and callable(_decorator):
        try:
            # Try to use decorator with some sensible metadata if it accepts kwargs
            try:
                @_decorator(name="JD Analyzer", description="Extract structured data from a job description")
                async def _registered_node(state: Dict[str, Any]) -> Dict[str, Any]:
                    return await jd_analyzer_node(state)
                # expose registered reference
                jd_analyzer_node = _registered_node  # type: ignore
            except TypeError:
                # decorator didn't accept kwargs — use bare decorator
                @_decorator
                async def _registered_node(state: Dict[str, Any]) -> Dict[str, Any]:
                    return await jd_analyzer_node(state)
                jd_analyzer_node = _registered_node  # type: ignore
            logger.info("jd_analyzer_node auto-registered with langgraph")
        except Exception as e:
            logger.debug("LangGraph decorator present but registration failed: %s", e)
    else:
        logger.debug("LangGraph package imported but no registration decorator found; skipping auto-register")
except Exception:
    # langgraph not installed — that's fine; the plain function can still be used
    logger.debug("langgraph package not available; jd_analyzer_node is available as a plain callable")


__all__ = ["jd_analyzer_node"]
