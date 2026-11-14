import serial
import serial.tools.list_ports
from serial.serialutil import SerialException


class SerialIO:
    def __init__(self, VID: int, joint_abbs: list[str]):
        self.port = None
        self.joint_abbs = joint_abbs

        for p in serial.tools.list_ports.comports():
            if p.vid == VID:
                print(p.device, "|", p.description, "|", p.vid, p.pid)
                try:
                    self.port = serial.Serial(p.device)
                except SerialException:
                    raise RuntimeError("Port taken by another device")
                break
            
        if self.port == None:
            raise RuntimeError("No port found")

    def write_stop(self):
        self.port.write(b"stop\n")
    def write_start(self):
        self.port.write(b"start\n")
    
    def write_change_port(self, from_port: int, to_port: int):
        self.port.write(("ch_port " + str(from_port) + " " + str(to_port) + "\n").encode())
    
    def write_move_joints(self, angles: list[float | None]):
        out_str = "move "
        for angle in angles:
            if angle is not None:
                out_str += str(angle)
            out_str += ","
        self.port.write((out_str + "\n").encode())
    
    def get_response(self) -> list[str]:
        lines = int(self.port.readline().decode().strip())
        out = []
        for i in range(lines):
            out.append(self.port.readline().decode().strip())
        return out
    
    def print_response(self):
        lines = int(self.port.readline().decode().strip())
        for i in range(lines):
            print("Arduino: " + self.port.readline().decode().strip())