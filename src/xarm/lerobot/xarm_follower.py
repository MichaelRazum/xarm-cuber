import logging
import time
from typing import Dict, Any
from functools import cached_property


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
        return {f"{joint}.pos": float for joint in self.config.joint2motorid}

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
            self._disable_auto_white_balance(cam)

        self.configure()
        logger.info(f"{self} connected.")
    
    def _disable_auto_white_balance(self, camera) -> None:
        """Disable auto white balance and other automatic camera settings for consistent color."""
        try:
            import cv2
            # Get the underlying OpenCV VideoCapture object
            if hasattr(camera, 'cap') and camera.cap is not None:
                cap = camera.cap
                logger.info(f"Disabling auto white balance for camera")
                
                # Disable auto white balance
                cap.set(cv2.CAP_PROP_AUTO_WB, 0)
                cap.set(cv2.CAP_PROP_WB_TEMPERATURE, 4700)
                cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
                cap.set(cv2.CAP_PROP_EXPOSURE, 125)
                cap.set(cv2.CAP_PROP_GAIN, 0)
                cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                cap.set(cv2.CAP_PROP_FOCUS, 0)

                logger.info("Camera auto white balance disabled successfully")
            else:
                logger.warning("Camera does not have accessible OpenCV capture object")
        except Exception as e:
            logger.error(f"Failed to disable auto white balance: {e}")

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
        obs_dict = {f"{motor}.pos": val for motor, val in obs_dict.items()}
        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"{self} read state: {dt_ms:.1f}ms")

        # Capture images from cameras
        for cam_key, cam in self.cameras.items():
            start = time.perf_counter()
            obs_dict[cam_key] = cam.async_read()
            dt_ms = (time.perf_counter() - start) * 1e3
            logger.debug(f"{self} read {cam_key}: {dt_ms:.1f}ms")

        return obs_dict
    
    def send_action(self, action: dict[str, Any], servo_runtime=None) -> dict[str, Any]:
        goal_pos = {key.removesuffix(".pos"): val for key, val in action.items() if key.endswith(".pos")}
        if self.config.max_relative_target is not None:
            present_pos = self.bus.read_positions()
            goal_present_pos = {key: (g_pos, present_pos[key]) for key, g_pos in goal_pos.items()}
            goal_pos = ensure_safe_goal_position(goal_present_pos, self.config.max_relative_target)
        
        # Send goal position to the arm
        self.bus.write_positions(positions=goal_pos,
                                 servo_runtime=self.config.servo_runtime if servo_runtime is None else servo_runtime,
                                 pos_tol=self.config.pos_tol)
        return {f"{motor}.pos": val for motor, val in goal_pos.items()}
    
    def move_to_default_position(self, task: str = "") -> None:
        """Move robot to task-specific default position."""
        # Task-specific positions: [gripper, joint_1, joint_2, joint_3, joint_4, joint_5]
        if 'flip' in task.lower() or 'move cube to center' in task.lower():
            joint_pos = [600, 500, 125, 500, 500, 500]
        else:
            joint_pos = [0, 500, 125, 500, 500, 500]


        joints = ["gripper", "joint_1", "joint_2", "joint_3", "joint_4", "joint_5"]

        # Send position 3 times for reliability
        for _ in range(5):
            action = {f"{joint}.pos": pwm for joint, pwm in zip(joints, joint_pos)}
            self.send_action(action, servo_runtime=1000)
            time.sleep(0.2)
        logger.info(f"Moved to default position for task: {task or 'default'}")

    def disconnect(self):
        self.bus.disconnect()
        for cam in self.cameras.values():
            cam.disconnect()
