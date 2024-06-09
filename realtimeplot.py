import argparse
import threading
import time
import serial
from flask import Flask, render_template
from flask_socketio import SocketIO
import argparse

parser = argparse.ArgumentParser(description="realtime plot app on a web browser")
parser.add_argument('-d', '--device', type=str, default='/dev/serial0', help='a device file connected to arduino')
args = parser.parse_args()

readSer = serial.Serial(args.device, 9600, timeout=3)
value = 0

def bgTask():
    while(True):
        global value
        value = float(readSer.readline().strip())
        time.sleep(0.1)

if __name__ == '__main__':
    app = Flask(__name__)
    socketio = SocketIO(app)

    @app.route("/chart")
    def hello_world():
        return render_template('chart.html')
    
    @socketio.on('req_data')
    def handle_req_data():
        global value
        #value = float(readSer.readline().strip())
        socketio.emit('ack', {'value': value})
    
    #socketio.start_background_task(bgTask)
    thread = threading.Thread(target=bgTask, name='background task', daemon=True)
    thread.start()

    # With debug mode on, print message in Worker class will be printed twice.
    # https://stackoverflow.com/questions/57344224/thread-is-printing-two-times-at-same-loop
    #app.run(host="0.0.0.0", port=5000, debug=True)
    socketio.run(app, host="0.0.0.0", port=12345, allow_unsafe_werkzeug=True)