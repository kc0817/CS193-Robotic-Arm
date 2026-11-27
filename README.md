# Robotic Arm 
A 5 DoF robotic arm with a gripper at the end to move small objects around 

# the Problem 
I've always wanted to have my own robotic arm, because I think they are REALLY COOL. Especially the math to be implemented in the software to make the end effector move linearly. Also, I've worked a ton on the software side of robotics, but less so on the electrical side, and much less on the mechanical side. So, it seems obvious that in order to fill this gap of knowledge and to satiate my curiosity, I should make one. 
And so I will. 

### Project goal: 
Build, wire, and program this arm to lift objects up to 100 grams in weight 

### Minimum Viable Product: 
1. Mechanically working arm 
2. Safe and working power circuits and signal circuits to power and send data to each servo 
3. Teleoperation functionality of arm through command line input 

# How It Works 
![System diagram](docs/system_diagram.png)

### Future Plans: 
1. Upgrade reach of arm, and upgrade from servos to motors
2. Set up MuJoCo simulation to try and train a RL model to learn to pick up objects

### Tech Stack: 
Layout:
 - Python program to read generalized user input, parse it, and send to arduino
  - C++ script to read python data, parse it, and relay to servos

Modules (python):
- math: to perform ceil and trig operations, and access constants like pi
- os and dotenv: to import config environment variables
- threading: to set up separate input threads so user input is isolated from command parsing & serial IO
- numpy: to store end effector target data, because ikpy interfaces with numpy arrays
- serial: to be used to read and write data from usb ports
- ikpy, an inverse kinematics library to calculate joint angles
- queue: to act as "mailboxes" between input threads and serial thread for communication

Libraries (C++):
- Servo.h: to command servos to a position
- Adafruit_INA219.h: to read current flow from a current sensor hooked up to the grabber servo
- initializer_list: so I can declare inline list arguments when calling writeBack()
- Wire.h: to read I2C data from the current sensor plugged into the Arduino in a testing script

Tools:
- uv: a package manager to handle dependency installation and version syncing
- git: for project version control


## Setup
- Acquire my robotic arm
- For Windows, install uv with: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
- For Mac/Linux, install uv with: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- cd into the root folder and type `uv sync`
- from root folder, run `uv run python python/gatekeeper.py` to start program

## Usage
There are a lot of different commands to control this arm through the command line:
- `start`: enables servo move commands
- `stop`: disables servo move commands
- `ch_port <from> <to>`: moves servo port
- `speed <speed>`: a decimal from 0 to 1 that controls the speed of the arm
- `<joint_name> <angle> abs`: moves a joint, where joint_name is one of the following: `t`, `s`, `e`, `wr`, `wp`, `g`, (which corresponds to turret, shoulder, elbow, wrist roll, wrist pitch, grabber) and `angle` is the desired angle offset of the joint in degrees (if you want to specify an absolute angle, add `abs` as a third argument)
- `move_coord <x> <y> <z> <pitch>`: calculates joint positions to move grabber pose by specified amounts (x, y, z, is in meters, pitch is in degrees)
- `home`: moves all joints to zero position
- `gc`: auto closes grabber to grip object without stalling servo by periodically checking for current spikes

Debugging commands:
- `get_angle`: retrieves joint data
- `check_current`: retrieves grabber current sensing data

## Author
Kevin Chen, https://github.com/kc0817
