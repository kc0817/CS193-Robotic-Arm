import pygame

pygame.init()
pygame.joystick.init()

gamepad = None

while True:
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
    