import math
import os
import threading
import time

import numpy as np
from dotenv import load_dotenv
from helpers import calc_fk, to_rad, save_current_plot
from ikpy.chain import Chain
from input_functions import *
from serial_io import SerialIO

load_dotenv()
set_dt = 1 / float(os.getenv("FPS"))
move_pos_step = float(os.getenv("MOVE_COORD_POS_STEP_SIZE"))
move_pitch_step = float(os.getenv("MOVE_COORD_PITCH_STEP_SIZE"))

ARDUINO_VID = int(os.getenv("ARDUINO_VID"), 16)
joint_names = ["t", "s", "e", "wp", "wr", "g"]
joint_targets = [0, 0, 0, 0, 0, 0] 
abs_targets = [0, 0, 0, 0, 0, 0]
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

def update_joints(new_joints):
    global joint_targets, abs_targets, target_pos, target_pitch
    joint_targets[:] = new_joints[:]

    # updating absolute joint angles
    abs_targets[:] = joint_targets[:]
    abs_targets[2] += abs_targets[1]
    abs_targets[3] += abs_targets[2]

    # updating end effector position
    pos, pitch = calc_fk(chain, joint_targets)
    target_pos = pos.tolist()
    target_pitch = pitch


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
    elif cmd == "get_angles": # TODO: MAKE THIS REQUEST ANGLE DATA FROM ARDUINO
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
        update_joints(home_pos)
        serial_io.write_move_joints(joint_targets)
    elif cmd == "speed":
        if len(args) != 1:
            error = ("Invalid speed args: " + str(args))
        else:
            try:
                serial_io.write_speed(float(args[0]))
            except ValueError:
                error = ("Invalid speed args: " + str(args))
    elif cmd == "check_current":
        serial_io.write_check_grabber_current()
    elif cmd == "gc":
        send_live_current = len(args) == 1 and args[0] == "send_current"
        serial_io.write_grabber_current_close(send_live_current)
        if send_live_current:
            error = serial_io.get_response()[0]
            if error == "closing grabber":
                currents = []
                times = []
                while True:
                    data = serial_io.get_response()[0]
                    if data == "done":
                        break
                    current, t = data.split(",")
                    currents.append(float(current))
                    times.append(float(t))
                save_current_plot(currents, times)
    
    elif cmd == "lock":
        if len(args) != 1:
            error = "Invalid lock joint args: " + str(args)
        else:
            if args[0] not in joint_names:
                error = "Invalid lock joint args: " + str(args)
            else:
                serial_io.write_lock_joint(args[0])
    elif cmd == "unlock":
        if len(args) != 1:
            error = "Invalid unlock joint args: " + str(args)
        else:
            if args[0] not in joint_names:
                error = "Invalid unlock joint args: " + str(args)
            else:
                serial_io.write_unlock_joint(args[0])
                error = str(serial_io.get_response())
                serial_io.write_move_joints([(angle if joint_names[i] == args[0] else None) for i, angle in enumerate(joint_targets)])
                _ = serial_io.get_response()

    elif cmd == "get_locks":
        serial_io.write_get_locks()
    elif cmd in joint_names:
        if len(args) != 1 and len(args) != 2:
            error = ("Invalid move angle args: " + str(args))
        else:
            absolute_angle = False
            if len(args) == 2:
                absolute_angle = args[1] == "abs"
            try:
                # updating target angle
                index = joint_names.index(cmd)
                angle = float(args[0]) + (0 if absolute_angle else joint_targets[index])
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
        error = "target: " + str(target_pos) + ", " + str(target_pitch) + " \nfk: (" + str(pos[0]) + ", " +  str(pos[1]) + ", " + str(pos[2]) + ", " + str(pitch)


    elif cmd == "move_coord":
        if len(args) != 4:
            error = "Invalid move coord args: " + str(args)
        # elif 2 - 1 == 1:
        #     disp = np.array(args, dtype=np.float32)
        #     target_pos += disp[:3]
        #     target_pitch += disp[3]
        #     error = str(target_pos) + ", " + str(target_pitch)
        else:
            error = "overriding normal comms protocol: "

            disp = np.array(args, dtype=np.float32)
            total_pos_disp = disp[:3]
            pos_norm = total_pos_disp / np.linalg.norm(total_pos_disp)
            total_pitch_disp = disp[3]
            pitch_norm = total_pitch_disp / abs(total_pitch_disp) if abs(total_pitch_disp) > .0001 else 0
            end_target_pos = target_pos + total_pos_disp
            end_target_pitch = target_pitch + total_pitch_disp
            # target_pos += disp[:3]
            # target_pitch += disp[3]
            i = 0
            pos_iters = math.ceil(float(np.max(np.abs(total_pos_disp))) / move_pos_step)
            pitch_iters = math.ceil(float(total_pitch_disp) / move_pitch_step)
            while i < max(pos_iters, pitch_iters):
                # calculating current targets
                pos_error = np.linalg.norm(target_pos - end_target_pos)
                target_pos += pos_norm * min(move_pos_step, pos_error)
                pitch_error = abs(target_pitch - end_target_pitch)
                target_pitch += pitch_norm * min(move_pitch_step, pitch_error)

                # preparing inputs for ik solve
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
                # print("target: " + str(target_pos) + ", " + str(target_pitch))
                # print("angle list rad: " + str(angles_list_rad))
                result = chain.inverse_kinematics(
                    target_position=target_pos,
                    initial_position=angles_list_rad,
                    orientation_mode="Z", # which axis to align to the target orientation in the end effector frame
                    target_orientation=direction)
                angles_list = [result[i] * 180/math.pi for i in range(1, len(result)-1)]
                angles_list.append(joint_targets[len(joint_targets)-1])
                joint_targets = angles_list
                serial_io.write_move_joints(joint_targets)
                error += "\n" + str(serial_io.get_response())
                time.sleep(1)
                i += 1

            
    else:
        error = "Unrecognized command: " + cmd
    
    if error is None:
        response = serial_io.get_response()
        origin_id[origin].put(response)
    else:
        origin_id[origin].put([error])