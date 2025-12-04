"""
Neo4j wrapper for ADK tools that returns ADK-friendly responses.
"""
import os
from typing import Any, Dict
from pathlib import Path
import atexit

from dotenv import load_dotenv

# Load environment variables - handle errors gracefully
try:
    from dotenv import find_dotenv
    env_path = find_dotenv()
    if env_path:
        load_dotenv(env_path, override=True)
    else:
        # Try to load from project root
        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file, override=True)
except Exception:
    # If .env file has issues, continue without it
    pass

from neo4j import (
    GraphDatabase,
    Result,
)


def tool_success(key: str, result: Any) -> Dict[str, Any]:
    """Convenience function to return a success result."""
    return {
        'status': 'success',
        key: result
    }


def tool_error(message: str) -> Dict[str, Any]:
    """Convenience function to return an error result."""
    return {
        'status': 'error',
        'error_message': message
    }


def to_python(value):
    """
    Convert Neo4j types to Python-native types.
    
    Handles Node, Relationship, Path, Record, and temporal types.
    """
    from neo4j.graph import Node, Relationship, Path
    from neo4j import Record
    import neo4j.time
    
    if isinstance(value, Record):
        return {k: to_python(v) for k, v in value.items()}
    elif isinstance(value, dict):
        return {k: to_python(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [to_python(v) for v in value]
    elif isinstance(value, Node):
        return {
            "id": value.id,
            "labels": list(value.labels),
            "properties": to_python(dict(value))
        }
    elif isinstance(value, Relationship):
        return {
            "id": value.id,
            "type": value.type,
            "start_node": value.start_node.id,
            "end_node": value.end_node.id,
            "properties": to_python(dict(value))
        }
    elif isinstance(value, Path):
        return {
            "nodes": [to_python(node) for node in value.nodes],
            "relationships": [to_python(rel) for rel in value.relationships]
        }
    elif isinstance(value, neo4j.time.DateTime):
        return value.iso_format()
    elif isinstance(value, (neo4j.time.Date, neo4j.time.Time, neo4j.time.Duration)):
        return str(value)
    else:
        return value


def result_to_adk(result: Result) -> Dict[str, Any]:
    """Convert a Neo4j Result to an ADK-friendly dictionary."""
    eager_result = result.to_eager_result()
    records = [to_python(record.data()) for record in eager_result.records]
    return tool_success("query_result", records)


class Neo4jForADK:
    """
    A wrapper for querying Neo4j which returns ADK-friendly responses.
    """
    _driver = None
    database_name = "neo4j"

    def __init__(self):
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_username = os.getenv("NEO4J_USERNAME") or "neo4j"
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        neo4j_database = os.getenv("NEO4J_DATABASE") or os.getenv("NEO4J_USERNAME") or "neo4j"
        
        # Validate that required environment variables are set
        if not neo4j_uri:
            raise ValueError(
                "NEO4J_URI environment variable is not set. "
                "Please set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD in your .env file."
            )
        if not neo4j_password:
            raise ValueError(
                "NEO4J_PASSWORD environment variable is not set. "
                "Please set NEO4J_PASSWORD in your .env file."
            )
        
        self.database_name = neo4j_database
        self._driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_username, neo4j_password)
        )
    
    def get_driver(self):
        """Get the Neo4j driver instance."""
        return self._driver
    
    def close(self):
        """Close the Neo4j driver connection."""
        return self._driver.close()
    
    def send_query(self, cypher_query, parameters=None) -> Dict[str, Any]:
        """
        Execute a Cypher query and return ADK-friendly results.
        
        Args:
            cypher_query: Cypher query string
            parameters: Optional query parameters dictionary
        
        Returns:
            Dictionary with status and query results or error message
        """
        session = self._driver.session()
        try:
            result = session.run(
                cypher_query, 
                parameters or {},
                database_=self.database_name
            )
            return result_to_adk(result)
        except Exception as e:
            return tool_error(str(e))
        finally:
            session.close()

    def get_import_directory(self):
        """
        Get the Neo4j import directory.
        
        Note: This returns a hardcoded path. In production, you might want to
        query Neo4j for the actual import directory.
        """
        # Uncomment below to query Neo4j for the actual import directory
        # results = self.send_query("""
        #     Call dbms.listConfig() YIELD name, value
        #     WHERE name CONTAINS 'server.directories.import'
        #     RETURN value as import_dir
        #     """)
        # 
        # if results["status"] == "success":
        #     return tool_success("neo4j_import_dir", results["query_result"][0]["import_dir"])
        # else:
        #     return tool_error(results["error_message"])
        
        import_dir = os.getenv("NEO4J_IMPORT_DIR", "../../neo4j/import")
        return tool_success("neo4j_import_dir", import_dir)


# Global instance - lazy initialization
_graphdb_instance = None

def get_graphdb():
    """
    Get or create the global Neo4jForADK instance.
    Uses lazy initialization to avoid connection errors when Neo4j is not configured.
    """
    global _graphdb_instance
    if _graphdb_instance is None:
        try:
            _graphdb_instance = Neo4jForADK()
            # Register cleanup function to close database connection on exit
            atexit.register(_graphdb_instance.close)
        except Exception as e:
            # If Neo4j is not configured, return None or raise a more helpful error
            import warnings
            warnings.warn(f"Neo4j connection not available: {e}. Some features may not work.")
            return None
    return _graphdb_instance

# For backward compatibility, create graphdb as a property-like accessor
# But don't initialize it at import time
class _GraphDBProxy:
    """Proxy class that lazily initializes Neo4j connection."""
    def __getattr__(self, name):
        db = get_graphdb()
        if db is None:
            raise RuntimeError("Neo4j is not configured. Please set NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD environment variables.")
        return getattr(db, name)

graphdb = _GraphDBProxy()

