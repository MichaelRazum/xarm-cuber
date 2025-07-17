"""
xarm package - xArm robot control and kinematics
"""

# Re-export main classes for clean imports
from .xarm_remote.inverse_kinematics import get_xarm_kinematics, UPPERARM_LENGTH, FOREARM_LENGTH, HAND_LENGTH, InverseK, Link
from .xarm_remote.teleopt import BusServoRemoteTelopt, pwm2pos
from .xarm_remote.bus_servo_serial import BusServoSerial, print_open_ports

# LeRobot integration (optional import)
try:
    from .lerobot import XArmFollowerConfig, XArmFollower
    _LEROBOT_AVAILABLE = True
except ImportError:
    _LEROBOT_AVAILABLE = False

__all__ = [
    'get_xarm_kinematics',
    'UPPERARM_LENGTH',
    'FOREARM_LENGTH', 
    'HAND_LENGTH',
    'InverseK',
    'Link',
    'BusServoRemoteTelopt',
    'pwm2pos',
    'BusServoSerial',
    'print_open_ports',
]

if _LEROBOT_AVAILABLE:
    __all__.extend(['XArmConfig', 'XArm'])