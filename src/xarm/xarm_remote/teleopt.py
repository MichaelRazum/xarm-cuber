import numpy as np
from retry import retry

from .bus_servo_serial import BusServoSerial

def pwm2pos(pwm:np.ndarray) -> np.ndarray:
    """
    :param pwm: numpy array of pwm values in range [0, 1000]
    """
    if not isinstance(pwm, np.ndarray):
        pwm = np.array(pwm) + np.array([0,0,20
                                        ,-30,0,0])
    return (pwm / 500 - 1) * 2.06


class BusServoRemoteTelopt(BusServoSerial):

    def __init__(self,
                 port='/dev/ttyUSB1',
                 remote_bus_server='bus_servo',
                 max_read_size=50,
                 timeout=.01,
                 active_joints=None,):
        super(BusServoRemoteTelopt, self).__init__(port=port,
                                                   remote_bus_server=remote_bus_server,
                                                   max_read_size=max_read_size,
                                                   timeout=timeout)
        self.last_position = [-10,-10,-10,-10,-10,-10]
        if active_joints is None:
            self.active_joints = [True for _ in range(6)]
        else:
            assert len(active_joints) == 6
            self.active_joints = active_joints

    def disable_torque(self):
        servo_ids  = [1, 2, 3, 4, 5, 6]
        for id in servo_ids:
            self.unload(id)

    def enable_torque(self):
        servo_ids = [1, 2, 3, 4, 5, 6]
        for id in servo_ids:
            self.load(id)

    @retry( tries=4, delay=0.03)
    def read_position(self):
        try:
            goal_positions = self.get_positions()
            self.last_position = goal_positions
            return np.array(goal_positions)
        except Exception as e:
            print(f'got exception {e}')
            raise e

    def set_goal_pos(self, goal_positions, servo_runtime=250, verbose=True, TOL=3):
        print(goal_positions, pwm2pos(goal_positions))
        MAX_P = 1000
        for n, p in enumerate(goal_positions):
            motor_id = n + 1
            if abs(self.last_position[n] - goal_positions[n]) > TOL:
                if verbose:
                    print(f'setting position old {self.last_position[n]}  NEW {goal_positions[n]} ')
                p = min(MAX_P, p)
                if motor_id == 3:
                    if p < 70:
                        print('warn for id =3 ',p)
                        p = 70
                self.run(motor_id, p, servo_runtime)
        self.last_position = goal_positions

    # mock method
    def read_velocity(self):
        return np.zeros(6)

if __name__ == '__main__':
    follower = BusServoRemoteTelopt('/dev/ttyUSB0')
    leader = BusServoRemoteTelopt('/dev/ttyUSB1')


    follower.enable_torque()
    leader.enable_torque()

    leader.disable_torque()

    follower.set_goal_pos(leader.read_position(), servo_runtime=300)

    while True:
        print('run_loop')
        try:
            positions = leader.read_position()
        except Exception as e:
            print('error for leader', e)
            continue
        try:
            follower.set_goal_pos(positions)
        except Exception as e:
            print('error for follower', e)