import queue

from helpers import print_list

cmd_q = queue.Queue()
terminal_response_q = queue.Queue()
gamepad_response_q = queue.Queue()

origin_id = {
    "T": terminal_response_q,
    "G": gamepad_response_q
}

def read_terminal_input():
    while True:
        data = input(">").split(" ")
        cmd_q.put(("T", data[0], data[1:]))
        print_list(terminal_response_q.get())

def read_gamepad_input():
    import os
    import time

    import pygame
    from dotenv import load_dotenv
    
    load_dotenv()
    set_dt = 1 / float(os.getenv("FPS"))
    max_pos_speed = float(os.getenv("MAX_POS_SPEED"))
    max_pitch_speed = float(os.getenv("MAX_PITCH_SPEED"))
    
    pygame.init()
    pygame.joystick.init()
        
    gamepad = None
    joystick_deadband_sqrd = .01
    grabber_state = 0

    prev_nanos = time.time_ns()
    prev_button0 = False

    while True:
        cur_nanos = time.time_ns()
        dt = (cur_nanos - prev_nanos) / 1e9
        sleep_time = set_dt - dt
        if sleep_time > 0:
            time.sleep(sleep_time)
        prev_nanos = cur_nanos

        for event in pygame.event.get():
            if event.type == pygame.JOYDEVICEADDED:
                print("gamepad found")
                gamepad = pygame.joystick.Joystick(event.device_index)
            
        if gamepad is not None:
            if gamepad.get_button(0):
                if not prev_button0:
                    prev_button0 = True
                    grabber_state = 0 if grabber_state == 1 else 1
                    cmd_q.put(("G", "move_angle", ["g", grabber_state]))

            else:
                prev_button0 = False
            
            lx = gamepad.get_axis(0)
            ly = -gamepad.get_axis(1)
            ry = -gamepad.get_axis(4)

            move_cmd = [0, 0, 0, 0]
            moved = False
            if lx ** 2 + ly ** 2 > joystick_deadband_sqrd:
                move_cmd[0] = lx * max_pos_speed * dt
                move_cmd[1] = ly * max_pos_speed * dt
                moved = True
            if ry**2 > joystick_deadband_sqrd:
                move_cmd[2] = ry * max_pos_speed * dt
                moved = True
            
            # TODO: find correct dpad codes
            if gamepad.get_button(1):
                move_cmd[3] = max_pitch_speed * dt
                moved = True
            elif gamepad.get_button(2):
                move_cmd[3] = -max_pitch_speed * dt
                moved = True
            
            if moved:
                cmd_q.put(("G", "move_coord", move_cmd))
                print_list(gamepad_response_q.get())
            