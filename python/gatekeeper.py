import math
import os
import threading

import numpy as np
from dotenv import load_dotenv
from helpers import calc_fk, to_deg, to_rad
from ikpy.chain import Chain
from input_functions import *
from serial_io import SerialIO

load_dotenv()
set_dt = 1 / float(os.getenv("FPS"))


ARDUINO_VID = 0x2341
# urdf_joint_order = ["t", "s", "e", "wp", "wr", "g"]
joint_names = ["t", "s", "e", "wp", "wr", "g"] #["g", "wr", "wp", "e", "s", "t"]
joint_targets = [0, 0, 0, 0, 0, 0] 
home_pos = [0, 0, 0, 0, 0, 0]

chain = Chain.from_urdf_file("arm.urdf")

total_z = 0
for link in chain.links[1:]:
    total_z += link.origin_translation[2]
target_pos = np.array([0, 0, total_z], dtype=np.float32)
target_pitch = 90
grabber_state = 0

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
        error = str(joint_targets)
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
        joint_targets = home_pos
        # updating end effector position
        pos, pitch = calc_fk(chain, joint_targets)
        target_pos = pos.tolist()
        target_pitch = pitch
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
                    
                    # updating end effector position
                    pos, pitch = calc_fk(chain, joint_targets)
                    target_pos = pos.tolist()
                    target_pitch = pitch

                    serial_io.write_move_joints(angles_list)

            except ValueError:
                error = ("Invalid move angle args: " + str(args))
                
    elif cmd == "calc_cur_coord":
        pos, pitch = calc_fk(chain, joint_targets)
        error = "target: " + str(target_pos) + ", " + str(target_pitch) + " \nfk: (" + str(pos[0]) + ", " +  str(pos[1]) + ", " + str(pos[2]) + ", " + str(to_deg(pitch))


    elif cmd == "move_coord":
        if len(args) != 4:
            error = "Invalid move coord args: " + str(args)
        else:
            disp = np.array(args, dtype=np.float32)
            target_pos += disp[:3]
            target_pitch += disp[3]

            angles_list_rad = [to_rad(joint_targets[i]) for i in range(len(joint_targets)-1)] # don't include grabber state
            angles_list_rad.insert(0, False)
            angles_list_rad.append(False)
            pitch_rad = to_rad(target_pitch)
            turret_rad = to_rad(joint_targets[0])
            direction = [
                math.cos(pitch_rad) * math.cos(turret_rad),
                math.cos(pitch_rad) * math.sin(turret_rad),
                math.sin(pitch_rad)
            ]
            result = chain.inverse_kinematics(
                target_position=target_pos,
                initial_position=angles_list_rad,
                orientation_mode="Z",
                target_orientation=direction)
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