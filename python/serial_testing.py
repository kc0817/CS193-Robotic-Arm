import serial
import serial.tools.list_ports

port = None
ARDUINO_VID = 0x2341

for p in serial.tools.list_ports.comports():
    if p.vid == ARDUINO_VID:
        print(p.device, "|", p.description, "|", p.vid, p.pid)
        port = serial.Serial(p.device)
        break

if port == None:
    print("no port found")

while True:
    data = input(">") + "\n"
    port.write(data.encode())
    print(port.readline().decode().strip())