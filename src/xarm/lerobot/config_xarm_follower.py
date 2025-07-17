"""
Configuration for xArm robot integration with LeRobot
"""

from dataclasses import dataclass, field
from typing import Dict, Any

from lerobot.robots.config import RobotConfig
from lerobot.cameras.configs import CameraConfig


@RobotConfig.register_subclass("xarm_follower")
@dataclass
class XArmFollowerConfig(RobotConfig):
    """Configuration for xArm robot."""
    
    # Connection settings
    port: str = "/dev/ttyUSB0"
    connection_type: str = "serial"  # "serial", "http", "websocket"
    address: str | None = None  # For HTTP/WebSocket connections
    servo_runtime = 250

    # Robot configuration
    num_joints: int = 6
    pos_tol: int = 3
    max_relative_target: float | None = None

    # Serial communication settings
    baudrate: int = 115200
    timeout: float = 0.01
    max_read_size: int = 50
    remote_bus_server: str = "bus_servo"
    
    # Joint limits and safety
    joint_limits: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "gripper": {"min": 0, "max": 1500},
        "joint_1": {"min": 0, "max": 1000},
        "joint_2": {"min": 70, "max": 1000},# Special limit for joint 2
        "joint_3": {"min": 0, "max": 1000},
        "joint_4": {"min": 0, "max": 1000},
        "joint_5": {"min": 0, "max": 1000},
    })

    joint2motorid = {
        "gripper": 1,
        "joint_1": 2,
        "joint_2": 3,
        "joint_3": 4,
        "joint_4": 5,
        "joint_5": 6
    }
    motorid2name = {v:k for k,v in joint2motorid.items()}

    # Camera configuration
    cameras: Dict[str, CameraConfig] = field(default_factory=dict)
    
    # Servo runtime settings
    default_servo_runtime: int = 250
    position_tolerance: int = 3