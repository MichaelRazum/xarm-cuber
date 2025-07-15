import pytest

from xarm.xarm_remote.bus_servo_websocket import BusServoSocket

XARM_IP = '192.168.88.232'

@pytest.fixture(scope='module')
def servo():
    servo = BusServoSocket(XARM_IP)
    return servo

def test_read_position(servo):
    id = 1
    position = servo.get_position(id=id)
    assert int(position) > 0

def test_get_positions(servo):
    servo_ids = [1, 2, 3, 4, 5, 6]
    positions = servo.get_positions()
    for n, id in enumerate(servo_ids):
        position = servo.get_position(id=id)
        assert abs(position == positions[n]) < 5

def test_set_positions(servo):
    positions = servo.get_positions()
    if positions[0] > 350:
        positions[0] = 100
    else:
        positions[0] = 550
    servo.set_positions(positions, 100)


def test_close_or_open_gripper(servo):
    id = 1
    position = int(servo.get_position(id=id))
    if position > 350:
        new_position = 100
    else:
        new_position = 550
    servo.run(id,new_position,10)




