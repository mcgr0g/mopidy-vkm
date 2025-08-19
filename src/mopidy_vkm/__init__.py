"""Mopidy VKM extension."""

import logging
import pathlib

from mopidy import config
from mopidy.config import types
from mopidy.config.schemas import ConfigSchema
from mopidy.ext import Extension, Registry

logger = logging.getLogger(__name__)


class VKMExtension(Extension):
    """Mopidy VKM extension."""

    dist_name = "Mopidy-VKM"
    ext_name = "vkm"
    version = "0.1.0"

    def get_default_config(self) -> str:
        """Get default configuration from ext.conf file."""
        return config.read(pathlib.Path(__file__).parent / "ext.conf")

    def get_config_schema(self) -> ConfigSchema:
        """Get configuration schema."""
        schema = super().get_config_schema()
        schema["user_agent"] = types.String(optional=True)
        schema["sensitive_cache_path"] = types.Path()
        schema["cache_path"] = types.Path(optional=True)
        schema["saved_path"] = types.Path(optional=True)
        return schema

    def setup(self, registry: Registry) -> None:
        """Setup the extension."""
        # Import here to avoid circular imports
        from mopidy_vkm.backend import VKMBackend
        from mopidy_vkm.web import create_web_app

        registry.add("backend", VKMBackend)
        # Dict param needs type ignore
        registry.add(
            "http:app",
            {"name": self.ext_name, "factory": create_web_app},  # type: ignore[arg-type]
        )
