import argparse
import serial

parser = argparse.ArgumentParser(description="realtime plot app on a web browser")
parser.add_argument('-d', '--device', type=str, default='/dev/serial0', help='a device file connected to arduino')
args = parser.parse_args()

readSer = serial.Serial(args.device, 9600, timeout=3)

while(True):
    value = int(readSer.readline().strip())
    print(value)