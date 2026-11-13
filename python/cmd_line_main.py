import serial
import serial.tools.list_ports
from serial.serialutil import SerialException

port = None
ARDUINO_VID = 0x2341

print("searching for Arduino")
for p in serial.tools.list_ports.comports():
    print(p.device, "|", p.description, "|", p.vid, p.pid)
    if p.vid == ARDUINO_VID:
        try:
            port = serial.Serial(p.device)
        except SerialException:
            print("port taken by another device")
        break

if port == None:
    print("no port found")

else:
    joint_names = ["g", "wr", "wp", "e", "s", "t"]
    joint_targets = [0, 0, 0, 0, 0, 0] 



    while True:
        print("COMMANDS: stop, ch_port <from> <to>, " +", ".join(f"{name} <angle>" for name in joint_names))
        cmd = input(">")

        if cmd == "stop":
            break
        elif len(cmd) >= 7 and cmd[:7] == "ch_port":
            port.write((cmd + "\n").encode());
        else:
            data = cmd.split()
            if len(data) != 2:
                print("invalid command: " + cmd)
            else :
                try:
                    angle = float(data[1])
                    parsed_cmd = "move "
                    for name in joint_names:
                        if name == data[0]:
                            parsed_cmd += str(angle)
                        parsed_cmd += ","
                    parsed_cmd += "\n"
                    print("writing " + parsed_cmd)
                    port.write(parsed_cmd.encode())
                except ValueError:
                    print("invalid command: " + cmd)
        
        lines = int(port.readline().decode().strip())
        for i in range(lines):
            print(port.readline().decode().strip())