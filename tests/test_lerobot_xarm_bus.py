import time

from xarm import XArmFollowerConfig
from xarm.lerobot.xarm_bus import XArmBus
import pytest

@pytest.fixture(scope='module')
def xarm()-> XArmBus:
    config = XArmFollowerConfig()
    xarm = XArmBus(config)
    xarm.connect()
    return xarm

def test_connect():
    config = XArmFollowerConfig()
    xarm = XArmBus(config)
    xarm.connect()
    assert xarm.is_connected() == True

def test_read_position(xarm: XArmBus):
    positions = xarm.read_positions()
    assert len(positions) == 6
    for v in positions.values():
        assert 0 <= v <= 1000

def test_write_positions(xarm: XArmBus):
    position_default_open  =     {'gripper': 100.0,
                                  'joint_1': 500.0,
                                  'joint_2': 500.0,
                                  'joint_3': 500.0,
                                  'joint_4': 500.0,
                                  'joint_5': 500.0}
    xarm.write_positions(position_default_open, servo_runtime=400)
    time.sleep(0.4)
    positions = xarm.read_positions()
    assert abs(positions['gripper'] - position_default_open['gripper']) < 40

    position_default_close  =     {'gripper': 600.0,
                                  'joint_1': 500.0,
                                  'joint_2': 500.0,
                                  'joint_3': 500.0,
                                  'joint_4': 500.0,
                                  'joint_5': 500.0}
    xarm.write_positions(position_default_close, servo_runtime=400)
    time.sleep(0.45)
    positions = xarm.read_positions()
    assert abs(positions['gripper'] - position_default_close['gripper']) < 40