from dataclasses import dataclass

from lerobot.teleoperators import TeleoperatorConfig
from .config_xarm_follower import XArmFollowerConfig


@TeleoperatorConfig.register_subclass("xarm_leader")
@dataclass
class XArmLeaderConfig(TeleoperatorConfig, XArmFollowerConfig):
    port: str = "/dev/ttyUSB1"


