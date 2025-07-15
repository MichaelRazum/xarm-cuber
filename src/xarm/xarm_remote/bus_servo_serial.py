import json
import time

import serial
import serial.tools.list_ports

def print_open_ports():
    ports = list(serial.tools.list_ports.comports())
    for port, desc, hwid in sorted(ports):
        print("{}: {} [{}]".format(port, desc, hwid))

class BusServoSerial:
    def __init__(self, port='/dev/ttyUSB0',
                       remote_bus_server='bus_servo',
                       max_read_size=50,
                       timeout=.01):
        self.max_read_size = max_read_size
        self.remote_bus_server=remote_bus_server

        self.con = serial.Serial(port, baudrate=115200, timeout=timeout)

        # Clear Console Cntrl-C
        self.con.write(b'\x03')
        self.con.read(self.max_read_size)

    def __del__(self):
        self.con.close()

    def run_command(self, command):
        self.con.read(size=self.max_read_size)
        send_command = f'{self.remote_bus_server}.{command}\r\n'
        self.con.write(send_command.encode())
        res = self.parse_result(command)
        return res

    def parse_result(self, command):
        res = ''
        for _ in range(100):
            res += self.con.read(size=self.max_read_size).decode()
            if '>>>' in res:
                break
            time.sleep(0.005)
        return res[res.find(command) + len(command):].split('>>>')[0].replace('\r', '').replace('\n', '')

    def run(self, id, p, servo_run_time=1000):
        return self.run_command(f'run({id}, {p}, {servo_run_time})')

    def run_mult(self, pp, servo_run_time):
        return self.run_command(f'run_mult({pp}, {servo_run_time})')

    def run_add_or_dec(self, id, speed):
        return self.run_command(f'run_add_or_dec({id}, {speed})')

    def stop(self, id):
        return self.run_command(f'stop({id})')

    def set_ID(self, old_id, new_id):
        return self.run_command(f'set_ID({old_id}, {new_id})')

    def get_ID(self, id):
        return self.run_command(f'get_ID({id})')

    def set_mode(self, id, mode, speed=0):
        return self.run_command(f'set_mode({id}, {mode}, {speed})')

    def load(self, id):
        return self.run_command(f'load({id})')

    def unload(self, id):
        return self.run_command(f'unload({id})')

    def servo_receive_handle(self):
        return self.run_command('servo_receive_handle()')

    def get_position(self, id):
        return int(self.run_command(f'get_position({id})'))

    def get_positions(self):
        pos_string =  self.run_command(f'get_positions()')
        try:
            json.loads(pos_string)
            return json.loads(pos_string)
        except:
            raise Exception(f'could not get position from string {pos_string}')

    def set_positions(self, goal_positions, servo_run_time):
        assert len(goal_positions) == 6
        self.run_command(f'set_positions({goal_positions}, {servo_run_time})')

    def get_vin(self, id):
        return self.run_command(f'get_vin({id})')

    def adjust_offset(self, id, offset):
        return self.run_command(f'adjust_offset({id}, {offset})')

    def save_offset(self, id):
        return self.run_command(f'save_offset({id})')

    def get_offset(self, id):
        return self.run_command(f'get_offset({id})')