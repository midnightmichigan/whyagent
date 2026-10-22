"""WhyAgent — an explainable investigation agent.

Track 02 target: "The Agent That Can Explain Why" — investigate complex
questions across multiple data sources, connect findings, and produce
evidence-backed answers or recommendations.
"""

from .evidence import (ArxivSearch, MultiSearch, SearchBackend, StubSearch,
                       WikipediaSearch, best_backend)
from .explain import Explanation, explain
from .investigate import Investigation, investigate

__all__ = [
    "ArxivSearch", "MultiSearch", "SearchBackend", "StubSearch",
    "WikipediaSearch", "best_backend",
    "Explanation", "explain",
    "Investigation", "investigate",
]
