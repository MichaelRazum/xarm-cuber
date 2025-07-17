import logging
import time
from typing import Dict, Any
from functools import cached_property

import numpy as np

from lerobot.robots.robot import Robot
from lerobot.cameras.utils import make_cameras_from_configs
from lerobot.errors import DeviceNotConnectedError, DeviceAlreadyConnectedError
from lerobot.robots.utils import ensure_safe_goal_position

from .config_xarm_follower import XArmFollowerConfig
from .xarm_bus import XArmBus

logger = logging.getLogger(__name__)


class XArmFollower(Robot):
    """xArm robot implementation for LeRobot."""
    
    config_class = XArmFollowerConfig
    name = "xarm_follower"
    
    def __init__(self, config: XArmFollowerConfig):
        super().__init__(config)
        self.config = config
        self.bus = XArmBus(config)
        self.cameras = make_cameras_from_configs(config.cameras)
        self._is_connected = False
        logger.info(f"Initialized xArm robot with {config.num_joints} joints")

    @property
    def _motors_ft(self) -> dict[str, type]:
        return {joint: float for joint in self.config.joint2motorid}

    @property
    def _cameras_ft(self) -> dict[str, tuple]:
        return {
            cam: (self.config.cameras[cam].height, self.config.cameras[cam].width, 3) for cam in self.cameras
        }


    @cached_property
    def observation_features(self) -> dict[str, type | tuple]:
        return {**self._motors_ft, **self._cameras_ft}

    @cached_property
    def action_features(self) -> dict[str, type]:
        return self._motors_ft
    
    @property
    def is_connected(self) -> bool:
        return self.bus.is_connected and all(cam.is_connected for cam in self.cameras.values())

    def connect(self, calibrate: bool = True) -> None:
        self.bus.connect()
        if not self.is_calibrated and calibrate:
            self.calibrate()

        for cam in self.cameras.values():
            cam.connect()

        self.configure()
        logger.info(f"{self} connected.")

    @property
    def is_calibrated(self) -> bool:
        return True
    
    def calibrate(self) -> None:
        pass
    
    def configure(self) -> None:
        self.bus.enable_torque()
    
    def get_observation(self) -> dict[str, Any]:
        start = time.perf_counter()
        obs_dict = self.bus.read_positions()
        obs_dict = {motor: val for motor, val in obs_dict.items()}
        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"{self} read state: {dt_ms:.1f}ms")

        # Capture images from cameras
        for cam_key, cam in self.cameras.items():
            start = time.perf_counter()
            obs_dict[cam_key] = cam.async_read()
            dt_ms = (time.perf_counter() - start) * 1e3
            logger.debug(f"{self} read {cam_key}: {dt_ms:.1f}ms")

        return obs_dict
    
    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
        goal_pos = {key.removesuffix(".pos"): val for key, val in action.items() if key.endswith(".pos")}
        if self.config.max_relative_target is not None:
            present_pos = self.bus.read_positions()
            goal_present_pos = {key: (g_pos, present_pos[key]) for key, g_pos in goal_pos.items()}
            goal_pos = ensure_safe_goal_position(goal_present_pos, self.config.max_relative_target)
        else:
            gaol_pos = action
        # Send goal position to the arm
        self.bus.write_positions(positions=gaol_pos, servo_runtime=self.config.servo_runtime, pos_tol=self.config.pos_tol)
        # self.bus.sync_write("Goal_Position", goal_pos)
        return {motor: val for motor, val in goal_pos.items()}
    
    def disconnect(self):
        self.bus.disconnect()
        for cam in self.cameras.values():
            cam.disconnect()
