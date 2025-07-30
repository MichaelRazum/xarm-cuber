from typing import Any

from lerobot.teleoperators import Teleoperator
from .xarm_follower import XArmFollower
from .config_xarm_leader import XArmLeaderConfig


class XArmLeader(Teleoperator):


    config_class = XArmLeaderConfig
    name = "xarm_leader"

    def __init__(self, config: XArmLeaderConfig):
        super().__init__(config)
        self.config = config
        # Use composition: contain an XArmFollower instance for robot operations
        self.robot = XArmFollower(config)

    @property
    def action_features(self) -> dict[str, type]:
        return self.robot.action_features

    @property
    def feedback_features(self) -> dict[str, type]:
        return {}

    @property
    def is_connected(self) -> bool:
        return self.robot.is_connected

    @property
    def is_calibrated(self) -> bool:
        return self.robot.is_calibrated

    def connect(self, calibrate: bool = True) -> None:
        self.robot.connect(calibrate=calibrate)
        self.configure()

    def calibrate(self) -> None:
        self.robot.calibrate()

    def configure(self) -> None:
        self.robot.bus.disable_torque()

    def get_action(self) -> dict[str, Any]:
        return self.robot.get_observation()

    def send_feedback(self, feedback: dict[str, Any]) -> None:
        raise NotImplementedError("Feedback not supported for xArm leader")

    def disconnect(self) -> None:
        self.robot.disconnect()

    def move_to_default_position(self, task: str = "") -> None:
        self.robot.move_to_default_position(task)
        self.robot.bus.disable_torque()