from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from ...db.database import get_db
from ...models.graph import Node, Edge, Graph

router = APIRouter()

@router.post("/nodes/", response_model=Node, status_code=201)
def create_node(node: Node, db = Depends(get_db)):
    """
    Create a new node in the graph.
    """
    nodes_collection = db.collection("nodes")
    node_dict = node.dict(exclude_unset=True)
    
    # Remove id if it's None
    if "id" in node_dict and node_dict["id"] is None:
        del node_dict["id"]
    
    try:
        result = nodes_collection.insert(node_dict)
        node_dict["id"] = result["_key"]
        return node_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create node: {str(e)}")

@router.get("/nodes/", response_model=List[Node])
def get_nodes(
    type: Optional[str] = None, 
    limit: int = Query(100, gt=0, le=1000),
    db = Depends(get_db)
):
    """
    Get all nodes in the graph, with optional filtering by type.
    """
    try:
        # Build AQL query based on filters
        if type:
            query = "FOR n IN nodes FILTER n.type == @type LIMIT @limit RETURN n"
            bind_vars = {"type": type, "limit": limit}
        else:
            query = "FOR n IN nodes LIMIT @limit RETURN n"
            bind_vars = {"limit": limit}
        
        # Execute query
        cursor = db.aql.execute(query, bind_vars=bind_vars)
        
        # Process results
        nodes = []
        for doc in cursor:
            nodes.append({
                "id": doc["_key"],
                "label": doc.get("label", ""),
                "type": doc.get("type", ""),
                "properties": doc.get("properties", {})
            })
        
        return nodes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch nodes: {str(e)}")

@router.get("/nodes/{node_id}", response_model=Node)
def get_node(node_id: str, db = Depends(get_db)):
    """
    Get a specific node by ID.
    """
    nodes_collection = db.collection("nodes")
    
    try:
        doc = nodes_collection.get(node_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Node not found")
        
        return {
            "id": doc["_key"],
            "label": doc.get("label", ""),
            "type": doc.get("type", ""),
            "properties": doc.get("properties", {})
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch node: {str(e)}")

@router.post("/edges/", response_model=Edge, status_code=201)
def create_edge(edge: Edge, db = Depends(get_db)):
    """
    Create a new edge between nodes.
    """
    edges_collection = db.collection("edges")
    edge_dict = edge.dict(exclude_unset=True)
    
    # Remove id if it's None
    if "id" in edge_dict and edge_dict["id"] is None:
        del edge_dict["id"]
    
    # Convert to ArangoDB format
    edge_dict["_from"] = edge_dict.pop("from_node")
    edge_dict["_to"] = edge_dict.pop("to_node")
    
    try:
        result = edges_collection.insert(edge_dict)
        
        # Format response
        return {
            "id": result["_key"],
            "from_node": edge_dict["_from"],
            "to_node": edge_dict["_to"],
            "label": edge_dict.get("label", ""),
            "properties": edge_dict.get("properties", {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create edge: {str(e)}")

@router.get("/edges/", response_model=List[Edge])
def get_edges(
    limit: int = Query(100, gt=0, le=1000),
    db = Depends(get_db)
):
    """
    Get all edges in the graph.
    """
    try:
        query = "FOR e IN edges LIMIT @limit RETURN e"
        cursor = db.aql.execute(query, bind_vars={"limit": limit})
        
        edges = []
        for doc in cursor:
            edges.append({
                "id": doc["_key"],
                "from_node": doc["_from"],
                "to_node": doc["_to"],
                "label": doc.get("label", ""),
                "properties": doc.get("properties", {})
            })
        
        return edges
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch edges: {str(e)}")

@router.get("/", response_model=Graph)
def get_graph(
    limit: int = Query(100, gt=0, le=1000),
    db = Depends(get_db)
):
    """
    Get the entire graph (nodes and edges) with optional limit.
    """
    try:
        # Get nodes
        nodes_cursor = db.aql.execute(
            "FOR n IN nodes LIMIT @limit RETURN n",
            bind_vars={"limit": limit}
        )
        
        nodes = []
        for doc in nodes_cursor:
            nodes.append({
                "id": doc["_key"],
                "label": doc.get("label", ""),
                "type": doc.get("type", ""),
                "properties": doc.get("properties", {})
            })
        
        # Get edges
        edges_cursor = db.aql.execute(
            "FOR e IN edges LIMIT @limit RETURN e",
            bind_vars={"limit": limit}
        )
        
        edges = []
        for doc in edges_cursor:
            edges.append({
                "id": doc["_key"],
                "from_node": doc["_from"],
                "to_node": doc["_to"],
                "label": doc.get("label", ""),
                "properties": doc.get("properties", {})
            })
        
        return {"nodes": nodes, "edges": edges}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch graph: {str(e)}")

@router.get("/neighbors/{node_id}", response_model=Graph)
def get_node_neighbors(
    node_id: str,
    depth: int = Query(1, gt=0, le=3),
    db = Depends(get_db)
):
    """
    Get a node and its neighbors (up to a specified depth).
    """
    try:
        # First check if node exists
        nodes_collection = db.collection("nodes")
        if not nodes_collection.has(node_id):
            raise HTTPException(status_code=404, detail="Node not found")
        
        # Get the full node ID for ArangoDB
        full_node_id = f"nodes/{node_id}"
        
        # Execute traversal query
        query = """
        LET start_node = DOCUMENT(@node_id)
        
        LET neighbors = (
            FOR v, e IN 1..@depth ANY @node_id GRAPH 'webgraph'
                RETURN {
                    vertex: v,
                    edge: e
                }
        )
        
        LET nodes = APPEND(
            [{ 
                _key: start_node._key,
                label: start_node.label,
                type: start_node.type,
                properties: start_node.properties
            }],
            (FOR n IN neighbors
                RETURN DISTINCT {
                    _key: n.vertex._key,
                    label: n.vertex.label,
                    type: n.vertex.type,
                    properties: n.vertex.properties
                }
            )
        )
        
        LET edges = (
            FOR n IN neighbors
                FILTER n.edge != null
                RETURN DISTINCT {
                    _key: n.edge._key,
                    _from: n.edge._from,
                    _to: n.edge._to,
                    label: n.edge.label,
                    properties: n.edge.properties
                }
        )
        
        RETURN {
            nodes: nodes,
            edges: edges
        }
        """
        
        cursor = db.aql.execute(
            query,
            bind_vars={"node_id": full_node_id, "depth": depth}
        )
        
        result = cursor.next()
        
        # Format nodes for response
        formatted_nodes = []
        for node in result["nodes"]:
            formatted_nodes.append({
                "id": node["_key"],
                "label": node.get("label", ""),
                "type": node.get("type", ""),
                "properties": node.get("properties", {})
            })
        
        # Format edges for response
        formatted_edges = []
        for edge in result["edges"]:
            formatted_edges.append({
                "id": edge["_key"],
                "from_node": edge["_from"],
                "to_node": edge["_to"],
                "label": edge.get("label", ""),
                "properties": edge.get("properties", {})
            })
        
        return {"nodes": formatted_nodes, "edges": formatted_edges}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch node neighbors: {str(e)}"
        )