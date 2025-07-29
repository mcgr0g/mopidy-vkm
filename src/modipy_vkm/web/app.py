"""VKM web application factory."""

import logging
from typing import Any

from tornado.web import Application

logger = logging.getLogger(__name__)


def create_web_app(config: dict[str, Any], core: object) -> Application:
    """Create VKM web application with modular handlers."""

    # Handler configuration
    handler_kwargs = {"config": config, "core": core}

    # URL routing for authentication handlers
    handlers = [
        # TODO: Main authentication page
        # TODO: Authentication API endpoints
    ]

    # Application settings
    settings = {
        "debug": config.get("debug", False),
        "autoreload": False,
        "compress_response": True,
        "serve_traceback": config.get("debug", False),
    }

    logger.info("Creating VKM web application with %d handlers", len(handlers))

    return Application(handlers, **settings)
