import socket
from .bus_servo_http import BusServoHttp

class BusServoSocket(BusServoHttp):

    def __init__(self, host_ip, port=5005, timeout=5):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((host_ip, port))
        s.settimeout(timeout)
        self.s = s

    def run_command(self, command, params):
        if params:
            data = f"{command}-{','.join(map(str, params))}"
        else:
            data = f"{command}"
        self.s.sendall(data.encode())
        response, _ = self.s.recvfrom(64)
        return response.decode()