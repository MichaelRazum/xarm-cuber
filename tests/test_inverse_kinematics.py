from xarm.xarm_remote.inverse_kinematics import get_xarm_kinematics, UPPERARM_LENGTH, FOREARM_LENGTH, HAND_LENGTH
from xarm.xarm_remote.teleopt import BusServoRemoteTelopt


def test_inverse_kinematics_start_position():
    model = get_xarm_kinematics()
    x, y, z = 0,0, (UPPERARM_LENGTH + FOREARM_LENGTH + HAND_LENGTH) / 1000
    assert z < 0.4
    positions = model.compute_ik([x,y,z])
    assert positions == [500, 500, 500, 500, 500]

def test_inverse_kinematics():
    follower = BusServoRemoteTelopt('/dev/ttyUSB0')
    model = get_xarm_kinematics()
    positions = model.compute_ik([( HAND_LENGTH) / 1000 + FOREARM_LENGTH/1000, 0 , UPPERARM_LENGTH/1000])
    # assert positions[0] == 500
    print(positions)
    follower.set_goal_pos([100]+positions, servo_runtime=500)
