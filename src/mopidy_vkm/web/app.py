"""VKM web application factory."""

import logging
import pathlib
from typing import Any

from tornado.web import Application, StaticFileHandler

from mopidy_vkm.web.handlers import (
    AuthCancelHandler,
    AuthLoginHandler,
    AuthStatusHandler,
    AuthVerifyHandler,
    MainHandler,
)

logger = logging.getLogger(__name__)


def create_web_app(config: dict[str, Any], core: object) -> Application:
    """Create VKM web application with modular handlers."""

    # Handler configuration
    handler_kwargs = {"config": config, "core": core}

    # Get the path to the static files
    current_dir = pathlib.Path(__file__).parent
    static_dir = str(current_dir / "static")
    template_dir = str(current_dir / "templates")

    # URL routing for authentication handlers
    handlers = [
        # Main authentication page
        (r"/vkm/?", MainHandler, handler_kwargs),
        # Authentication API endpoints
        (r"/vkm/auth/login", AuthLoginHandler, handler_kwargs),
        (r"/vkm/auth/verify", AuthVerifyHandler, handler_kwargs),
        (r"/vkm/auth/status", AuthStatusHandler, handler_kwargs),
        (r"/vkm/auth/cancel", AuthCancelHandler, handler_kwargs),
        # Static files
        (r"/vkm/static/(.*)", StaticFileHandler, {"path": static_dir}),
    ]

    # Application settings
    settings = {
        "debug": config.get("debug", False),
        "autoreload": False,
        "compress_response": True,
        "serve_traceback": config.get("debug", False),
        "template_path": template_dir,
    }

    logger.info("Creating VKM web application with %d handlers", len(handlers))

    return Application(handlers, **settings)
