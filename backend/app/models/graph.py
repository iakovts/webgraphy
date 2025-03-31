from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

class Node(BaseModel):
    """Model for a graph node"""
    id: Optional[str] = None
    label: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "label": "Person",
                "type": "person",
                "properties": {
                    "name": "John Doe",
                    "age": 30
                }
            }
        }

class Edge(BaseModel):
    """Model for a graph edge"""
    id: Optional[str] = None
    from_node: str
    to_node: str
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "from_node": "nodes/123",
                "to_node": "nodes/456",
                "label": "KNOWS",
                "properties": {
                    "since": "2022-01-01"
                }
            }
        }

class Graph(BaseModel):
    """Model for a complete graph"""
    nodes: List[Node] = Field(default_factory=list)
    edges: List[Edge] = Field(default_factory=list)