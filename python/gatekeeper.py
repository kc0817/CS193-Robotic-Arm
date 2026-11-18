import os
import threading

import numpy as np
from dotenv import load_dotenv
from input_functions import *
from serial_io import SerialIO

load_dotenv()
set_dt = 1 / float(os.getenv("FPS"))

s_pos = np.array([float(os.getenv("SHOULDER_X")), float(os.getenv("SHOULDER_Y")), float(os.getenv("SHOULDER_Z"))])
s_link_len = float(os.getenv("SHOULDER_LINK_LENGTH"))
e_link_len = float(os.getenv("ELBOW_LINK_LENGTH"))
w_link_len = float(os.getenv("WRIST_LINK_LENGTH"))

target_pos = np.array([0, 0, 5])
target_pitch = 0
grabber_state = 0

ARDUINO_VID = 0x2341
joint_names = ["g", "wr", "wp", "e", "s", "t"]
joint_targets = [0, 0, 0, 0, 0, 0] 

serial_io = SerialIO(ARDUINO_VID, joint_names, enabled=False)

terminal_thread = threading.Thread(target=read_terminal_input, daemon=True)
terminal_thread.start()

gamepad_thread = threading.Thread(target=read_gamepad_input, daemon=True)

while True:
    data = cmd_q.get()
    origin = data[0]
    cmd = data[1]
    args = data[2]
    print("args: " + str(args))

    error = None

    data_sent = True
    if cmd == "get_angles":
        serial_io.write_get_angles()
    elif cmd == "start":
        serial_io.write_start()
    elif cmd == "stop":
        serial_io.write_stop()
        break
    elif cmd == "ch_port":
        if len(args) != 2:
            error = ("Invalid change port args: " + str(args))
        else:
            try:
                from_port = int(args[0])
                to_port = int(args[1])
                serial_io.write_change_port(from_port, to_port)
            except ValueError:
                error = ("Invalid change port args: " + str(args))
    elif cmd == "home":
        serial_io.write_move_joints([0, 0, 0, 0, 0, 0])
    elif cmd == "speed":
        if len(args) != 1:
            error = ("Invalid speed args: " + str(args))
        else:
            try:
                serial_io.write_speed(float(args[0]))
            except ValueError:
                error = ("Invalid speed args: " + str(args))
            
    elif cmd == "move_angle":
        if len(args) != 2 or args[0] not in joint_names:
            error = ("Invalid move angle args: " + str(args))
        else:
            try:
                angle = float(args[1])
                angles_list = []
                for name in joint_names:
                    if name == args[0]:
                        angles_list = (angle)
                    else:
                        angles_list = (None)
                
                serial_io.write_move_joints(angles_list)
            except ValueError:
                error = ("Invalid move angle args: " + str(args))
                
    elif cmd == "move_coord":
        if len(args) != 4:
            error = "Invalid move coord args: " + str(args)
        else:
            disp = np.array(args)
            target_pos += disp[:3]
            target_pitch += disp[3]

            # TODO: calculate target angles 
            angles_list = []

            seiral_io.write_move_joints(angles_list)
    else:
        error = "Unrecognized command: " + cmd
    
    if error is None:
        response = serial_io.get_response()
        origin_id[origin].put(response)
    else:
        origin_id[origin].put([error])