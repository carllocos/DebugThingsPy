from __future__ import annotations
from typing import Union

import json

from utils import get_logger


class OOTConfig:
    DefaultPort = 8000
    logger = get_logger("OOTConfig")

    def __init__(self, **kwargs):
        self.__port = kwargs.get("port", OOTConfig.DefaultPort)
        self.monitorsource = kwargs.get("monitorsource", True)
        self.breakpoint_policy = kwargs.get("breakpoint_policy", [])
        self.proxy = kwargs.get("proxy", [])
        self.program = kwargs["program"]
        self.ip_device = kwargs["ip_device"]

    @property
    def port(self) -> int:
        return self.__port

    @port.setter
    def port(self, p: int) -> None:
        self.__port = p

    @staticmethod
    def from_json_file(filepath: str) -> Union[OOTConfig, None]:
        try:
            _config = json.loads(filepath)
            return OOTConfig.from_dict(_config)
        except KeyError:
            OOTConfig.logger.error("missing `program` and/or `ip_device`")
        except UnicodeDecodeError:
            OOTConfig.logger.error("could not decode")
        except json.decoder.JSONDecodeError:
            OOTConfig.logger.error("could not parse JSON")

    @staticmethod
    def from_dict(config: dict) -> Union[None, OOTConfig]:
        try:
            return OOTConfig(**config)
        except KeyError:
            OOTConfig.logger.error("missing `program` and/or `ip_device`")

    @staticmethod
    def default_config() -> OOTConfig:
        return OOTConfig(program=None, monitorsource=True, ip_device=None)
