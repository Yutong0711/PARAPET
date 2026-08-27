__all__ = [
    "AgentMemory",
    "agent",
    "PerfOrchPipeline",
    "classify_problem",
    "CATEGORIES",
]


def __getattr__(name):
    if name == "AgentMemory":
        from .memory import AgentMemory
        return AgentMemory
    if name == "agent":
        from .main import agent
        return agent
    if name == "PerfOrchPipeline":
        from .pipeline import PerfOrchPipeline
        return PerfOrchPipeline
    if name == "classify_problem":
        from .classifier import classify_problem
        return classify_problem
    if name == "CATEGORIES":
        from .classifier import CATEGORIES
        return CATEGORIES
    raise AttributeError(name)
