import pytest

from xarm.xarm_remote.bus_servo_serial import BusServoSerial, print_open_ports


def test_list_all_serial_connections():
    print_open_ports()

def test_init_remote_control():
    with pytest.raises(Exception):
        BusServoSerial('/dev/wrong/port')
    BusServoSerial('/dev/ttyUSB0')

def test_read_position():
    servo = BusServoSerial()
    id = 1
    position = servo.get_position(id=id)
    assert int(position) > 0

def test_get_positions():
    servo = BusServoSerial()
    servo_ids = [1, 2, 3, 4, 5, 6]
    positions = servo.get_positions()
    for n, id in enumerate(servo_ids):
        position = servo.get_position(id=id)
        assert abs(position == positions[n]) < 5

def test_set_positions():
    servo = BusServoSerial()
    positions = servo.get_positions()
    if positions[0] > 350:
        positions[0] = 100
    else:
        positions[0] = 550
    servo.set_positions(positions, 100)


def test_close_or_open_gripper():
    servo = BusServoSerial()
    id = 1
    position = int(servo.get_position(id=id))
    if position > 350:
        new_position = 100
    else:
        new_position = 550
    servo.run(id,new_position,10)

def test_default_position():
    l =  [125, 0, 0, 0, 0, 0]
    servo = BusServoSerial()
    for n, v in  enumerate(l):
        angel = v
        angel_factor = 1000/ 240
        cmnd = int(angel * angel_factor) + 500
        print(n+1,cmnd)
        servo.run(n+1, cmnd, 500)

def test_default_position1():
    l = [0, 500, 500, 500, 500, 500]
    servo = BusServoSerial()
    for n, v in  enumerate(l):
        servo.run(n+1, v, 500)

def test_default_position2():
    l = [0, 500, 520, 470, 500, 500]
    servo = BusServoSerial()
    for n, v in  enumerate(l):
        servo.run(n+1, v, 500)

def test_default_position3():
    import numpy as np
    base = int(max(min((np.pi/2/ 2.06 + 1.) * 500+30, 1000), 0))
    upper_arm = int(max(min((-np.pi/2/ 2.06 + 1.) * 500+30, 1000), 0))
    middle_arm = int(max(min((np.pi/4/ 2.06 + 1.) * 500-20, 1000), 0))
    lower_arm = int(max(min((np.pi/4/ 2.06 + 1.) * 500-20, 1000), 0))
    l = [0, 500, upper_arm, middle_arm, lower_arm, base]
    servo = BusServoSerial()

    for n, v in  enumerate(l):
        servo.run(n+1, v, 3000)



