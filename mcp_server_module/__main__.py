"""Main entry point for MCP server module."""

import asyncio
from .server import main

if __name__ == "__main__":
    asyncio.run(main())