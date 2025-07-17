import pytest

from xarm import XArmFollowerConfig, XArmFollower
from xarm.lerobot.config_xarm_leader import XArmLeaderConfig
from xarm.lerobot.xarm_teleop import XArmLeader


@pytest.fixture(scope='module')
def xarm_follower():
    config = XArmFollowerConfig()
    xarm = XArmFollower(config)
    return xarm

@pytest.fixture(scope='module')
def xarm_leader():
    config = XArmLeaderConfig()
    xarm = XArmLeader(config)
    return xarm

def test_xarm_robot_motor_ft(xarm_follower):
    assert list(xarm_follower._motors_ft.values()) == [float] * 6

def test_get_observation(xarm_follower):
    xarm_follower.connect()
    obs = xarm_follower.get_observation()
    assert len(obs) == 6

def test_get_action(xarm_leader):
    xarm_leader.connect()
    obs = xarm_leader.get_action()
    assert len(obs) == 6