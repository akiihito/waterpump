import serial
import time

#ser = serial.Serial('/dev/ttyACM0', 9600)
ser = serial.Serial('/dev/serial0', 9600)
time.sleep(5)

while True:
    String_data = ser.readline()
    #print(String_data)
    print(String_data.strip().decode())
ser.close()
