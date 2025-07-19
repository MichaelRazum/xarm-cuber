import logging
from typing import Dict

from retry import retry

from lerobot.errors import DeviceAlreadyConnectedError
from ..xarm_remote.bus_servo_serial import BusServoSerial
from ..xarm_remote.bus_servo_http import BusServoHttp
from ..xarm_remote.bus_servo_websocket import BusServoSocket
from .config_xarm_follower import XArmFollowerConfig

logger = logging.getLogger(__name__)


class XArmBus:

    def __init__(self, config: XArmFollowerConfig):
        self.config = config
        self.xarm = None
        self._last_positions = [-10] * config.num_joints
        
    def connect(self):
        if self.xarm is not None:
            raise DeviceAlreadyConnectedError('device already connected')
        try:
            if self.config.connection_type == "serial":
                self.xarm = BusServoSerial(
                    port=self.config.port,
                    remote_bus_server=self.config.remote_bus_server,
                    max_read_size=self.config.max_read_size,
                )
            elif self.config.connection_type == "http":
                if not self.config.address:
                    raise ValueError("Address required for HTTP connection")
                self.xarm = BusServoHttp(self.config.address)
            elif self.config.connection_type == "websocket":
                if not self.config.address:
                    raise ValueError("Address required for WebSocket connection")
                self.xarm = BusServoSocket(self.config.address)
            else:
                raise ValueError(f"Unsupported connection type: {self.config.connection_type}")
                
            logger.info(f"Connected to xArm via {self.config.connection_type}")
            
        except Exception as e:
            logger.error(f"Failed to connect to xArm: {e}")
            raise
    
    def disconnect(self):
        pass

    def is_connected(self) -> bool:
        """Check if robot is connected."""
        try:
            self.xarm.get_positions()
        except:
            return False
        return True

    def enable_torque(self):
        """Enable torque on all servos."""
        motor_ids = [1, 2, 3, 4, 5, 6]
        for id in motor_ids:
            self.xarm.load(id)

    def disable_torque(self):
        """Enable torque on all servos."""
        motor_ids = [1, 2, 3, 4, 5, 6]
        for id in motor_ids:
            self.xarm.unload(id)

    @retry( tries=10, delay=0.03)
    def read_positions(self) -> Dict[str, float]:
        positions = self.xarm.get_positions()
        self._last_positions = positions
        joint_positions= {self.config.motorid2name[i+1]: float(pos)
                          for i, pos in enumerate(positions)}
        return joint_positions

    def write_positions(self, positions: Dict[str, float], servo_runtime: int | None = None, pos_tol=0):
        for joint in positions:
            pos = positions[joint]
            motor_id = self.config.joint2motorid[joint]
            limits = self.config.joint_limits[joint]
            pos = int(max(limits["min"], min(limits["max"], pos)))
            if abs(self._last_positions[motor_id-1] - pos) > pos_tol:
                self.xarm.run(motor_id, pos, servo_runtime)
                self._last_positions[motor_id-1] = pos