import serial
import serial.tools.list_ports
from serial.serialutil import SerialException

ARDUINO_VID = 0x2341
joint_names = ["g", "wr", "wp", "e", "s", "t"]
joint_targets = [0, 0, 0, 0, 0, 0] 

serial_io = SerialIO(ARDUINO_VID, joint_names)


while True:
    print("COMMANDS: stop, ch_port <from> <to>, " +", ".join(joint_names))
    cmd = input(">")

    if cmd == "stop":
        break
    elif len(cmd) >= 7 and cmd[:7] == "ch_port":
        data = cmd.split(" ")
        if len(data) != 3:
            print("Invalid command: " + cmd)
        try:
            from_port = int(data[1])
            to_port = int(data[2])
            serial_io.write_change_port(from_port, to_port)
        except ValueError:
            print("Invalid command: " + cmd)
    else:
        data = cmd.split(" ")
        if len(data) != 2:
            print("Invalid command: " + cmd)
        else:
            try:
                angle = float(data[1])
                angles_list = []
                for name in joint_names:
                    if name == data[0]:
                        angles_list.append(angle)
                    else:
                        angles_list.append(None)
                
                serial_io.write_move_joints(angles_list)
            except ValueError:
                print("Invalid command: " + cmd)
    
    serial_io.print_response()