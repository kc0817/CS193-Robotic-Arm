
import os
import time

import numpy as np
import pygame
from dotenv import load_dotenv

load_dotenv()
set_dt = 1 / float(os.getenv("FPS"))

max_pos_speed = float(os.getenv("MAX_POS_SPEED"))
max_pitch_speed = float(os.getenv("MAX_PITCH_SPEED"))

s_pos = np.array([float(os.getenv("SHOULDER_X")), float(os.getenv("SHOULDER_Y")), float(os.getenv("SHOULDER_Z"))])
s_link_len = float(os.getenv("SHOULDER_LINK_LENGTH"))
e_link_len = float(os.getenv("ELBOW_LINK_LENGTH"))
w_link_len = float(os.getenv("WRIST_LINK_LENGTH"))

target_pos = np.array([0, 0, 5])
target_pitch = 0

pygame.init()
pygame.joystick.init()

gamepad = None
joystick_deadband_sqrd = .01

prev_nanos = time.time_ns()

while True:
    cur_nanos = time.time_ns()
    dt = (cur_nanos - prev_nanos) / 1e9
    if dt < set_dt:
        continue
    prev_nanos = cur_nanos
    for event in pygame.event.get():
        if event.type == pygame.JOYDEVICEADDED:
            print("gamepad found")
            gamepad = pygame.joystick.Joystick(event.device_index)
            print(gamepad.get_name())
            print(gamepad.get_power_level())
            print(gamepad.get_guid())
        
    if gamepad is not None:
        if gamepad.get_button(0):
            print("a button pressed")
        lx = gamepad.get_axis(0)
        ly = -gamepad.get_axis(1)

        if lx ** 2 + ly ** 2 > joystick_deadband_sqrd:
            target_pos += np.array([lx, ly, 0]) * max_pos_speed * dt

        ry = -gamepad.get_axis(4)
        if ry**2 > joystick_deadband_sqrd:
            target_pitch += ry * max_pitch_speed * dt