import math
import os
import threading

import numpy as np
from dotenv import load_dotenv
from ikpy.chain import Chain
from input_functions import *
from serial_io import SerialIO

load_dotenv()
set_dt = 1 / float(os.getenv("FPS"))

s_pos = np.array([float(os.getenv("SHOULDER_X")), float(os.getenv("SHOULDER_Y")), float(os.getenv("SHOULDER_Z"))])
s_link_len = float(os.getenv("SHOULDER_LINK_LENGTH"))
e_link_len = float(os.getenv("ELBOW_LINK_LENGTH"))
w_link_len = float(os.getenv("WRIST_LINK_LENGTH"))

target_pos = np.array([0, 0, .4070], dtype=np.float32)
target_pitch = 0
grabber_state = 0

ARDUINO_VID = 0x2341
# urdf_joint_order = ["t", "s", "e", "wp", "wr", "g"]
joint_names = ["t", "s", "e", "wp", "wr", "g"] #["g", "wr", "wp", "e", "s", "t"]
joint_targets = [0, 0, 0, 0, 0, 0] 
home_pos = [0, 0, 0, 0, 0, 0]

chain = Chain.from_urdf_file("arm.urdf")

serial_io = SerialIO(ARDUINO_VID, enabled=True)

terminal_thread = threading.Thread(target=read_terminal_input, daemon=True)
terminal_thread.start()

gamepad_thread = threading.Thread(target=read_gamepad_input, daemon=True)
# gamepad_thread.start()

while True:
    data = cmd_q.get()
    origin = data[0]
    cmd = data[1]
    args = data[2]

    error = None

    data_sent = True
    if cmd == "raw":
        arg_str = " ".join(arg for arg in args)
        serial_io.write_raw(arg_str)
    elif cmd == "get_angles":
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
        serial_io.write_move_joints(home_pos)
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
                index = joint_names.index(args[0])
                if index == -1:
                    error = "Invalid move angle args: " + str(args)
                else:
                    angles_list = [(angle if i == index else None) for i in range(len(joint_names))]
                    joint_targets[index] = angle
                    serial_io.write_move_joints(angles_list)
            except ValueError:
                error = ("Invalid move angle args: " + str(args))
                
    elif cmd == "move_coord":
        if len(args) != 4:
            error = "Invalid move coord args: " + str(args)
        else:
            disp = np.array(args, dtype=np.float32)
            target_pos += disp[:3]
            target_pitch += disp[3]

            # TODO: calculate target angles a
            print("target pos:" + str(target_pos))
            angles_list_rad = [joint_targets[i] * math.pi/180 for i in range(len(joint_targets)-1)] # don't include grabber state
            angles_list_rad.insert(0, False)
            angles_list_rad.append(False)
            result = chain.inverse_kinematics(
                target_position=target_pos,
                initial_position=angles_list_rad)
            print(result)
            angles_list = [result[i] * 180/math.pi for i in range(1, len(result)-1)]
            angles_list.append(joint_targets[len(joint_targets)-1])
            joint_targets = angles_list
            serial_io.write_move_joints(joint_targets)
    else:
        error = "Unrecognized command: " + cmd
    
    if error is None:
        response = serial_io.get_response()
        origin_id[origin].put(response)
    else:
        origin_id[origin].put([error])