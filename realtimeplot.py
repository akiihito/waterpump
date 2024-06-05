import argparse
import serial
from flask import Flask, render_template
from flask_socketio import SocketIO
import argparse

parser = argparse.ArgumentParser(description="realtime plot app on a web browser")
parser.add_argument('-d', '--device', type=str, default='/dev/serial0', help='a device file connected to arduino')
args = parser.parse_args()

readSer = serial.Serial(args.device, 9600, timeout=3)

def bgTask():
    value = float(readSer.readline().strip())
    print(value)


if __name__ == '__main__':
    app = Flask(__name__)
    socketio = SocketIO(app)

    @app.route("/chart")
    def hello_world():
        return render_template('chart.html')