"""VKM web application factory."""

import logging
import pathlib
from typing import Any

from tornado.web import StaticFileHandler

from mopidy_vkm.web.handlers import (
    AuthCancelHandler,
    AuthLoginHandler,
    AuthStatusHandler,
    AuthVerifyHandler,
    MainHandler,
)

logger = logging.getLogger(__name__)


def create_web_app(
    config: dict[str, Any], core: object
) -> list[tuple[str, Any, dict[str, Any]]]:
    """Create VKM web application handlers for Mopidy HTTP server."""

    # Handler configuration
    handler_kwargs = {"config": config, "core": core}

    # Get the path to the static files
    current_dir = pathlib.Path(__file__).parent
    static_dir = str(current_dir / "static")
    template_dir = str(current_dir / "templates")

    # URL routing for authentication handlers - Mopidy adds /vkm prefix automatically
    handlers = [
        # Main authentication page
        (r"/?", MainHandler, handler_kwargs),
        # Authentication API endpoints
        (r"/auth/login", AuthLoginHandler, handler_kwargs),
        (r"/auth/verify", AuthVerifyHandler, handler_kwargs),
        (r"/auth/status", AuthStatusHandler, handler_kwargs),
        (r"/auth/cancel", AuthCancelHandler, handler_kwargs),
        # Static files
        (r"/static/(.*)", StaticFileHandler, {"path": static_dir}),
    ]

    logger.info("Creating VKM web application with %d handlers", len(handlers))

    return handlers
