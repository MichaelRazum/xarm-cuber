import json
import time

import serial
import serial.tools.list_ports

def print_open_ports():
    ports = list(serial.tools.list_ports.comports())
    for port, desc, hwid in sorted(ports):
        print("{}: {} [{}]".format(port, desc, hwid))

CTRL_A, CTRL_B, CTRL_C, CTRL_D = b"\x01", b"\x02", b"\x03", b"\x04"

class BusServoSerial:
    def __init__(self, port='/dev/ttyUSB0',
                       remote_bus_server='bus_servo',
                       max_read_size=50,
                       raw_mode=True):
        self.max_read_size = max_read_size
        self.remote_bus_server=remote_bus_server

        self.con = serial.Serial(port,
                                 baudrate=115200,
                                 timeout=0.1 if raw_mode else 0.01,
                                 )

        self.con.write(CTRL_B)
        self.con.read(self.max_read_size)
        self.con.write(CTRL_C)
        self.con.read(self.max_read_size)
        self.con.read(self.max_read_size)

        self.raw_mode = raw_mode
        if raw_mode:
            self.enter_raw_mode()

    def __del__(self):
        self.con.close()

    def run_command(self, command):

        if self.raw_mode:
            send_command = f'print({self.remote_bus_server}.{command})\n'
            self.con.write(send_command.encode() +  CTRL_D)
            res = self.parse_raw_result()
        else:
            self.con.read(size=self.max_read_size)
            send_command = f'{self.remote_bus_server}.{command}\r\n'
            self.con.write(send_command.encode())
            res = self.parse_result(command)
        return res

    def enter_raw_mode(self):
        self.con.write(CTRL_C)
        time.sleep(0.01)
        self.con.write(CTRL_A)
        time.sleep(0.01)
        self.con.read(self.max_read_size)

    def _read_until(self, marker: bytes, timeout=0.2) -> str:
        buf = bytearray()
        t0 = time.time()
        while marker not in buf:
            n = self.con.in_waiting
            if n:
                chunk = self.con.read(n)
                buf.extend(chunk)
            if time.time() - t0 > timeout:
                raise TimeoutError("Prompt not seen within %.1f s" % timeout)
        return buf.decode(errors='ignore')


    def parse_raw_result(self):
        res = self.con.read_until(b'>')
        return res[res.find(b'OK')+2:res.find(b'\r')].decode()

    def parse_result(self, command):
        res = self._read_until(b'>>>', timeout=0.2)
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