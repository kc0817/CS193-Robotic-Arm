import serial
import serial.tools.list_ports
from serial.serialutil import SerialException


class SerialIO:
    def __init__(self, VID: int, enabled=True):
        self.port = None
        self.enabled = enabled

        if self.enabled:
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
        else:
            print("Serial IO disabled")

    def write_raw(self, cmd):
        self.port.write((cmd + "\n").encode())

    def write_get_angles(self):
        if self.enabled:
            self.port.write(b"get_angles\n")
    def write_stop(self):
        if self.enabled:
            self.port.write(b"stop\n")
    def write_start(self):
        if self.enabled:
            self.port.write(b"start\n")
    
    def write_speed(self, speed):
        if self.enabled:
            self.port.write(("speed " + str(speed) + "\n").encode())
    
    def write_change_port(self, from_port: int, to_port: int):
        if self.enabled:
            self.port.write(("ch_port " + str(from_port) + " " + str(to_port) + "\n").encode())
    
    def write_check_grabber_current(self):
        self.port.write(b"check_grabber_current\n")
    def write_grabber_current_close(self):
        self.port.write(b"gc\n")
    
    def write_lock_joint(self, joint_name: str):
        self.port.write(("lock " + joint_name + "\n").encode())
    def write_unlock_joint(self, joint_name: str):
        self.port.write(("unlock " + joint_name + "\n").encode())

    def write_move_joints(self, angles: list[float | None]):
        if self.enabled:
            out_str = "move "
            for angle in angles:
                if angle is not None:
                    out_str += str(angle)
                out_str += ","
            self.port.write((out_str + "\n").encode())
    
    def write_blocking_move_joints(self, angles: list[float | None]):
        if self.enabled:
            out_str = "move_blocking "
            for angle in angles:
                if angle is not None:
                    out_str += str(angle)
                out_str += ","
            self.port.write((out_str + "\n").encode())
    
    def write_get_locks(self): 
        if self.enabled:
            self.port.write(b"get_locks\n")

    def get_response(self) -> list[str]:
        if self.enabled:
            lines = int(self.port.readline().decode().strip())
            out = []
            for i in range(lines):
                out.append(self.port.readline().decode().strip())
            return out
        return ["serial disabled"]
    
    def print_response(self):
        if self.enabled:
            lines = int(self.port.readline().decode().strip())
            for i in range(lines):
                print("Arduino: " + self.port.readline().decode().strip())
        print("serial disabled")