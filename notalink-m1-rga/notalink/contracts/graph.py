from __future__ import annotations
from typing import List
from pydantic import BaseModel

class GraphNode(BaseModel):
    id: str
    label: str
    degree: int = 0

class GraphEdge(BaseModel):
    source: str
    target: str
    label: str = "links"

class GraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
