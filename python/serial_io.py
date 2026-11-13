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

    def write_stop():
        port.write("stop\n").encode()
    
    def write_change_port(from_port: int, to_port: int):
        port.write(("ch_port " + str(from_port) + " " + str(to_port) + "\n").encode())
    
    def write_move_joints(angles: list[float]):
        out_str = ""
        for angle in angles:
            out_str += str(angle) + ","
        port.write((out_str + "\n").encode())
    
    def write_move_joint(joint_abb: str, angle: float):
        out_str = ""
        for abb in joint_abbs:
            if abb == joint_abb:
                out_str += str(angle)
            out_str += ","
        port.write((out_str + "\n").encode())

    def get_response() -> list[str]:
        lines = int(port.readline().decode().strip())
        out = []
        for i in range(lines):
            out.append(port.readline().decode().strip())
        return out
    
    def print_response():
        lines = int(port.readline().decode().strip())
        for i in range(lines):
            print(port.readline().decode().strip())


if __name__ == "__main__":
    serial = SerialIO(0x2341, ["1", "2", "3", "4", "5", "6"])