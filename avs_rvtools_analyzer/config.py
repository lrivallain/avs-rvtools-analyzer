"""
Configuration management for AVS RVTools Analyzer.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set


@dataclass
class ServerConfig:
    """Server configuration settings."""

    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "info"
    timeout_graceful_shutdown: int = 3


@dataclass
class FastAPIConfig:
    """FastAPI application configuration."""

    title: str = "AVS RVTools Analyzer"
    description: str = (
        "A comprehensive tool for analyzing RVTools data with both web interface and RESTful API. Supports Model Context Protocol (MCP) for AI tool integration."
    )
    tags_metadata: List[Dict[str, str]] = field(
        default_factory=lambda: [
            {
                "name": "Web UI",
                "description": (
                    "Web-based user interface for uploading, exploring, and analyzing RVTools files through an interactive dashboard."
                ),
            },
            {
                "name": "API",
                "description": (
                    "RESTful API endpoints for programmatic access, automation, and AI tool integration via Model Context Protocol (MCP)."
                ),
            },
        ]
    )


@dataclass
class CORSConfig:
    """CORS middleware configuration."""

    allow_origins: List[str] = field(default_factory=lambda: ["*"])
    allow_credentials: bool = True
    allow_methods: List[str] = field(default_factory=lambda: ["*"])
    allow_headers: List[str] = field(default_factory=lambda: ["*"])


@dataclass
class FileConfig:
    """File handling configuration."""

    allowed_extensions: Set[str] = field(default_factory=lambda: {"xlsx", "xls"})
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    temp_file_suffix: str = ".xlsx"


@dataclass
class PathConfig:
    """Path configuration for application directories."""

    base_dir: Path = field(default_factory=lambda: Path(__file__).parent)

    @property
    def templates_dir(self) -> Path:
        return self.base_dir / "templates"

    @property
    def static_dir(self) -> Path:
        return self.base_dir / "static"

    @property
    def sku_data_file(self) -> Path:
        return self.static_dir / "sku.json"


@dataclass
class APIEndpointsConfig:
    """API endpoints configuration."""

    web_ui: str = "/"
    analyze: str = "/api/analyze"
    analyze_upload: str = "/api/analyze-upload"
    analyze_json: str = "/api/analyze-json"
    convert_to_json: str = "/api/convert-to-json"
    available_risks: str = "/api/risks"
    sku_capabilities: str = "/api/sku"
    health: str = "/health"
    api_info: str = "/api/info"
    mcp_api: str = "/mcp"


@dataclass
class MCPConfig:
    """MCP (Model Context Protocol) configuration."""

    name: str = "AVS RVTools Analyzer"
    mount_path: str = "/mcp"


@dataclass
class MigrationMethodsConfig:
    """Configuration for migration methods and their minimum hardware version requirements."""

    # Migration methods with their minimum required HW version
    migration_methods: Dict[str, int] = field(
        default_factory=lambda: {
            "HCX vMotion": 9,
            "Cold Migration": 9,
            "Replication Assisted vMotion": 9,
            "Bulk Migration": 7,
        }
    )

    # Special handling for very old versions
    minimum_supported_hw_version: int = 7
    all_methods_unsupported_message: str = "All migration methods (HW version too old)"


@dataclass
class AppConfig:
    """Main application configuration container."""

    server: ServerConfig = field(default_factory=ServerConfig)
    fastapi: FastAPIConfig = field(default_factory=FastAPIConfig)
    cors: CORSConfig = field(default_factory=CORSConfig)
    files: FileConfig = field(default_factory=FileConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    endpoints: APIEndpointsConfig = field(default_factory=APIEndpointsConfig)
    mcp: MCPConfig = field(default_factory=MCPConfig)
    migration: MigrationMethodsConfig = field(default_factory=MigrationMethodsConfig)

    def get_endpoint_urls(self, host: str = None, port: int = None) -> Dict[str, str]:
        """Generate full URLs for all endpoints."""
        host = host or self.server.host
        port = port or self.server.port
        base_url = f"http://{host}:{port}"

        return {
            "health": f"{base_url}{self.endpoints.health}",
            "api_docs": f"{base_url}/docs",
            "redoc": f"{base_url}/redoc",
            "openapi_json": f"{base_url}/openapi.json",
            "tools_list": f"{base_url}/tools",
            "api_info": f"{base_url}{self.endpoints.api_info}",
            "mcp_api": f"{base_url}{self.endpoints.mcp_api}",
        }
