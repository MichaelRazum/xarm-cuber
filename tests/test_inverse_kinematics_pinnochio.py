import math

import numpy as np
import pinocchio as pin
import pytest

from xarm.xarm_remote.teleopt_pinnochio import get_rotation_angle, derotate


@pytest.mark.parametrize("theta", [np.pi, np.pi/4, -np.pi/3, np.pi/2])
def test_adjust_coordinate_system(theta):
    p1 = np.array([1,0,0], dtype=np.float32)
    p2 = np.array([1,1,0], dtype=np.float32)
    p3 = np.array([-1,0,0], dtype=np.float32)
    p4 = np.array([1,-1,0], dtype=np.float32)
    Pose = pin.Quaternion(1,0,0,0)

    # Rotation Matrix
    R = pin.utils.rpyToMatrix(0, 0, theta)

    p1_r = R @ p1
    p2_r = R @ p2
    p3_r = R @ p3
    p4_r = R @ p4
    Pose_R = pin.Quaternion((R @ Pose.toRotationMatrix()))

    assert math.isclose(theta, get_rotation_angle(p1_r), abs_tol=1e-6)

    assert np.allclose(derotate(p1_r, Pose_R, theta)[0], p1, atol=1e-6)
    assert np.allclose(derotate(p2_r, Pose_R, theta)[0], p2, atol=1e-6)
    assert np.allclose(derotate(p3_r, Pose_R, theta)[0], p3, atol=1e-6)
    assert np.allclose(derotate(p4_r, Pose_R, theta)[0], p4, atol=1e-6)
    assert np.allclose(derotate(np.zeros(3), Pose_R, theta)[1].toRotationMatrix(), Pose.toRotationMatrix(), atol=1e-6)


