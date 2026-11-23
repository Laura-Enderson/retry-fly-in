"""
Expose the main components of the package.

This module provides a centralized interface to access the parser,
graph elements, and orchestration components.

The following components are made available:
    - ParseError: Exception raised when parsing fails.
    - Parser: Responsible for parsing input data.
    - Orchestrator: Manages the simulation orchestration.
    - Graph: Represents the graph structure.
    - InitError: Exception raised during initialization.
"""

from .parser import ParseError, Parser
from .elements import Orchestrator, Graph, InitError
__all__ = ["ParseError", "Parser", "Orchestrator", "Graph", "InitError"]
