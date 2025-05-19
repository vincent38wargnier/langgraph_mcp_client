import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Debug setting
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

# Log level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app")

# MCP transport method (sse, streamable_http, stdio, websocket)
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "sse")

# MongoDB connection settings
_DEFAULT_MONGODB_URI = "mongodb://localhost:27017/agent_db"
MONGODB_URI = os.getenv("MONGODB_URI", _DEFAULT_MONGODB_URI)

# Default database name
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "workflow")

# Connection pool settings
MONGODB_MAX_POOL_SIZE = int(os.getenv("MONGODB_MAX_POOL_SIZE", "50"))
MONGODB_MIN_POOL_SIZE = int(os.getenv("MONGODB_MIN_POOL_SIZE", "10"))
MONGODB_MAX_IDLE_TIME_MS = int(os.getenv("MONGODB_MAX_IDLE_TIME_MS", "50000"))
MONGODB_WAIT_QUEUE_TIMEOUT_MS = int(os.getenv("MONGODB_WAIT_QUEUE_TIMEOUT_MS", "5000"))
MONGODB_CONNECTION_TIMEOUT_MS = int(os.getenv("MONGODB_CONNECTION_TIMEOUT_MS", "10000"))
MONGODB_SOCKET_TIMEOUT_MS = int(os.getenv("MONGODB_SOCKET_TIMEOUT_MS", "10000"))
MONGODB_SERVER_SELECTION_TIMEOUT_MS = int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "10000"))
MONGODB_RETRY_WRITES = os.getenv("MONGODB_RETRY_WRITES", "True").lower() in ("true", "1", "t")
MONGODB_RETRY_READS = os.getenv("MONGODB_RETRY_READS", "True").lower() in ("true", "1", "t")

# Create a settings class
class Settings:
    """Application settings class with configuration values."""
    
    def __init__(self):
        # Default MCP endpoint - load from environment
        self._mcp_endpoint = os.getenv(
            "MCP_ENDPOINT", 
            "https://magify.app.n8n.cloud/mcp-test/d36d2dcd-b620-4efb-aab0-972d691a8550/sse"
        )
        
        # Load transport method
        self.MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "sse")
        
        # Set simple variables directly
        self.DEBUG = DEBUG
        self.LOG_LEVEL = LOG_LEVEL
        self.MONGODB_URI = MONGODB_URI
        self.MONGODB_DB_NAME = MONGODB_DB_NAME
        self.MONGODB_MAX_POOL_SIZE = MONGODB_MAX_POOL_SIZE
        self.MONGODB_MIN_POOL_SIZE = MONGODB_MIN_POOL_SIZE
        self.MONGODB_MAX_IDLE_TIME_MS = MONGODB_MAX_IDLE_TIME_MS
        self.MONGODB_WAIT_QUEUE_TIMEOUT_MS = MONGODB_WAIT_QUEUE_TIMEOUT_MS
        self.MONGODB_CONNECTION_TIMEOUT_MS = MONGODB_CONNECTION_TIMEOUT_MS
        self.MONGODB_SOCKET_TIMEOUT_MS = MONGODB_SOCKET_TIMEOUT_MS
        self.MONGODB_SERVER_SELECTION_TIMEOUT_MS = MONGODB_SERVER_SELECTION_TIMEOUT_MS
        self.MONGODB_RETRY_WRITES = MONGODB_RETRY_WRITES
        self.MONGODB_RETRY_READS = MONGODB_RETRY_READS
    
    @property
    def MCP_ENDPOINT(self):
        """
        Get the MCP server endpoint.
        For this specific endpoint, we actually need to preserve the /sse suffix.
        """
        return self._mcp_endpoint
    
    @property
    def USE_LOCAL_MCP_SERVER(self):
        """
        Determine if we should use the local MCP server.
        This is true if USE_LOCAL_MCP is set to true in the environment,
        or if REMOTE_MCP_FIRST is set to false.
        """
        use_local = os.getenv("USE_LOCAL_MCP", "False").lower() in ("true", "1", "t")
        remote_first = os.getenv("REMOTE_MCP_FIRST", "True").lower() in ("true", "1", "t")
        return use_local or not remote_first

# Create a singleton instance
settings = Settings() 