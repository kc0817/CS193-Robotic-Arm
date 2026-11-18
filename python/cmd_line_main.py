from serial_io import SerialIO

ARDUINO_VID = 0x2341
joint_names = ["g", "wr", "wp", "e", "s", "t"]
joint_targets = [0, 0, 0, 0, 0, 0] 

serial_io = SerialIO(ARDUINO_VID, joint_names)


while True:
    # cmd_list_str = "COMMANDS: start, stop, ch_port <from> <to>, "
    # for name in joint_names:
    #     cmd_list_str += name + " <angle>, "
    # print(cmd_list_str)

    cmd = input(">")

    data_sent = True
    if cmd == "get_angles":
        serial_io.write_get_angles()
    elif cmd == "start":
        serial_io.write_start()
    elif cmd == "stop":
        serial_io.write_stop()
        break
    elif len(cmd) >= 7 and cmd[:7] == "ch_port":
        data = cmd.split(" ")
        if len(data) != 3:
            print("Invalid change port command: " + cmd)
            data_sent = False
        try:
            from_port = int(data[1])
            to_port = int(data[2])
            serial_io.write_change_port(from_port, to_port)
        except ValueError:
            print("Invalid change port command: " + cmd)
            data_sent = False
    elif cmd == "home":
        serial_io.write_move_joints([0, 0, 0, 0, 0, 0])
    elif len(cmd) >= 5 and cmd[:5] == "speed":
        try:
            serial_io.write_speed(float(cmd[6:]))
        except ValueError:
            print("Invalid speed command: " + cmd);
            data_sent = False
    else:
        data = cmd.split(" ")
        if len(data) != 2 or data[0] not in joint_names:
            print("Invalid move command: " + cmd)
            data_sent = False
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
                print("Invalid move command: " + cmd)
                data_sent = False
    
    if data_sent:
        serial_io.print_response()