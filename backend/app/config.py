import os
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import List, Optional

# Load environment variables from .env file
load_dotenv()

@dataclass(slots=True, frozen=True)
class Settings:
    # API configuration
    API_V1_STR: str = field(default="/api/v1")
    PROJECT_NAME: str = field(default="Webgraphy")
    
    # ArangoDB configuration
    ARANGO_HOST: str = field(default_factory=lambda: os.getenv("ARANGO_HOST", "localhost"))
    ARANGO_PORT: int = field(default_factory=lambda: int(os.getenv("ARANGO_PORT", "8529")))
    ARANGO_DB: str = field(default_factory=lambda: os.getenv("ARANGO_DB", "webgraphy"))
    ARANGO_USER: str = field(default_factory=lambda: os.getenv("ARANGO_USER", "root"))
    ARANGO_PASSWORD: str = field(default_factory=lambda: os.getenv("ARANGO_PASSWORD", ""))

settings = Settings()