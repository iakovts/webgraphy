from arango import ArangoClient
from app.config import settings

def get_db():
    """
    Creates a connection to ArangoDB and initializes required collections.
    """
    # Initialize the ArangoDB client
    client = ArangoClient(
        hosts=f"http://{settings.ARANGO_HOST}:{settings.ARANGO_PORT}"
    )
    
    # Connect to the system database
    sys_db = client.db(
        "_system",
        username=settings.ARANGO_USER,
        password=settings.ARANGO_PASSWORD
    )
    
    # Create application database if it doesn't exist
    if not sys_db.has_database(settings.ARANGO_DB):
        sys_db.create_database(
            settings.ARANGO_DB,
            users=[{
                "username": settings.ARANGO_USER,
                "password": settings.ARANGO_PASSWORD,
                "active": True
            }]
        )
    
    # Connect to the application database
    db = client.db(
        settings.ARANGO_DB,
        username=settings.ARANGO_USER,
        password=settings.ARANGO_PASSWORD
    )
    
    # Create collections if they don't exist
    if not db.has_collection("nodes"):
        db.create_collection("nodes")
    
    if not db.has_collection("edges"):
        db.create_collection("edges", edge=True)
    
    # Create graph if it doesn't exist
    if not db.has_graph("webgraph"):
        graph = db.create_graph("webgraph")
        
        # Add vertex collection
        if not graph.has_vertex_collection("nodes"):
            graph.create_vertex_collection("nodes")
        
        # Add edge definition
        if not graph.has_edge_definition("edges"):
            graph.create_edge_definition(
                edge_collection="edges",
                from_vertex_collections=["nodes"],
                to_vertex_collections=["nodes"]
            )
    
    return db