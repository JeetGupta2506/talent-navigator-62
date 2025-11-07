"""Lightweight LangGraph flow that registers the jd_analyzer node as the entry point.

This module tries to use the installed `langgraph` API if available. If LangGraph's
Graph class or registration API isn't present, it falls back to creating a minimal
in-memory graph object with the same `add_node` / `set_entry_point` methods so the
module remains importable for testing.

Usage:
  from backend.langgraph_nodes.graph_flow import g
  # g is the graph-like object with the jd_analyzer node registered and entry set

If you prefer a different registration pattern (decorator-based auto-registration)
use the `backend/langgraph_nodes/jd_node.py` module which already attempts auto-registration.
"""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

try:
    # Import the node implementation
    from backend.langgraph_nodes.jd_node import jd_analyzer_node  # type: ignore
except Exception as e:
    logger.exception("Could not import jd_analyzer_node: %s", e)
    raise


class _SimpleGraph:
    """Small fallback graph object with minimal API used for testing.

    It stores nodes in a dict and remembers an entry point name.
    """
    def __init__(self):
        self.nodes = {}
        self.entry_point = None

    def add_node(self, name: str, fn):
        self.nodes[name] = fn

    def set_entry_point(self, name: str):
        if name not in self.nodes:
            raise KeyError(f"Node {name} not found when setting entry point")
        self.entry_point = name


# try to create a real LangGraph Graph if possible, otherwise use fallback
try:
    import langgraph as _lg  # type: ignore

    # try to find a Graph class; api may vary
    GraphClass = getattr(_lg, "Graph", None) or getattr(_lg, "LangGraph", None)
    if GraphClass:
        g = GraphClass()
        try:
            g.add_node("jd_analyzer", jd_analyzer_node)
            g.set_entry_point("jd_analyzer")
            logger.info("Registered jd_analyzer with LangGraph Graph instance")
        except Exception as e:
            logger.exception("Failed to register node on LangGraph Graph instance: %s", e)
            # fall back to simple graph
            g = _SimpleGraph()
            g.add_node("jd_analyzer", jd_analyzer_node)
            g.set_entry_point("jd_analyzer")
    else:
        # LangGraph installed but no Graph class found — use fallback
        g = _SimpleGraph()
        g.add_node("jd_analyzer", jd_analyzer_node)
        g.set_entry_point("jd_analyzer")
except Exception:
    # langgraph not installed or import failed — use fallback graph
    logger.debug("langgraph not available or failed to initialize; using fallback graph")
    g = _SimpleGraph()
    g.add_node("jd_analyzer", jd_analyzer_node)
    g.set_entry_point("jd_analyzer")


__all__ = ["g"]
