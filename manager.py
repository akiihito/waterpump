from enum import Enum
from flask_socketio import SocketIO
import sys
import signal
import argparse
import threading

from asyncio import Queue
from flask import Flask, render_template

from controller import Controller


parser = argparse.ArgumentParser(description="two water pump controller")
parser.add_argument('-d', '--duration', type=int, default=2, help='duration time to turn on the pump (default 2 second)')
parser.add_argument('-i', '--interval', type=int, default=2, help='interval time to the next run (default 2 second)')
parser.add_argument('-t', '--test', action='store_true', default=False, help='Dry run mode')
args = parser.parse_args()


pump_wait = threading.Event()

class State(Enum):
    NONE = 0
    READY = 1
    RUNNING = 2

class Worker(threading.Thread):
    def __init__(self, controller1, controller2, queue):
        super().__init__()
        self.controller1 = controller1
        self.controller2 = controller2
        self.interval = 1
        self.duration = 0
        self.queue = queue
        self.terminate = False
        self.state = State.NONE

    def setInterval(self, interval: int) -> None:
        print("set the pump interval to ", interval)
        self.interval = interval

    def setDuration(self, duration: int) -> None:
        print("set the pump duration to ", duration)
        self.duration = duration

    def getSettings(self):
        return {"duration": self.duration, "interval": self.interval}

    def softTerminate(self):
        self.terminate = True

    def getState(self):
        return self.state
    
    def setState(self, state):
        self.state = state

    def run(self):
        self.state = State.RUNNING
        while not pump_wait.is_set():
            if self.terminate:
                print("finishing with soft terminate")
                break
            if not self.queue.empty():
                self.duration = int(self.queue.get())

            ############# pump1 running ###############
            print('----- PUMP 1 -------')
            self.controller1.start()
            pump_wait.wait(self.duration)
            self.controller1.stop()
            ###########################################
            pump_wait.wait(self.interval)
            ############# pump2 running ###############
            print('----- PUMP 2 -------')
            self.controller2.start()
            pump_wait.wait(self.duration)
            self.controller2.stop()
            ###########################################
            pump_wait.wait(self.interval)
        else:
            print("Terminate all pumps immediately")
            self.controller1.stop()
            self.controller2.stop()
            pump_wait.clear()
        self.state = State.READY


if __name__ == '__main__':

    def initWorker(controller1, controller2, current_settings):
        queue = Queue(1)
        worker = Worker(controller1, controller2, queue)
        worker.setInterval(current_settings['interval'])
        worker.setDuration(current_settings['duration'])
        worker.setState(State.READY)
        return worker

    def handler(signo, frame):
        print("Interrupted by %d, shutting down" % signo)
        pump_wait.set()
        sys.exit()

    for sig in ('TERM', 'INT'):
        signal.signal(getattr(signal, 'SIG'+sig), handler)


    current_settings = {'duration': args.duration, 'interval': args.interval}
    controller1 = Controller(motorid=1, m1pin=6, m2pin=13, pwmpin=12, testmode=args.test)
    controller2 = Controller(motorid=2, m1pin=20, m2pin=21, pwmpin=26, testmode=args.test)

    worker = initWorker(controller1, controller2, current_settings)

    app = Flask(__name__)
    socketio = SocketIO(app)

    @app.route("/")
    def hello_world():
        return render_template('index.html')
    
    @socketio.on('req_settings')
    def handle_req_settings(data):
        global worker
        global current_settings
        if worker.getState() == State.RUNNING:
            worker.softTerminate()
            worker.join()
            worker = initWorker(controller1, controller2, current_settings)
        try:
            worker.setDuration(float(data['duration']))
        except ValueError:
            print("invalid number as duration: ", data['duration'])
        try:
            worker.setInterval(float(data['interval']))
        except ValueError:
            print("invalid number as interval: ", data['interval'])
        current_settings = worker.getSettings()
        socketio.emit('current_settings', current_settings)
        socketio.emit('current_state',  {'state': worker.getState().name})

    @socketio.on('req_start')
    def handle_req_start(msg):
        global worker
        print('received req_start')
        if worker.getState() == State.RUNNING:
            print("Worker has already been running")
        else:
            worker.start()
            socketio.emit('current_state', {'state': worker.getState().name})

    @socketio.on('req_reset')
    def handle_req_reset(msg):
        global worker
        global current_settings
        print('received req_reset')
        if worker.getState() == (State.READY or State.NONE):
            print("Worker is not working, skip the reset request")
        else:
            worker.softTerminate()
            worker.join()
            worker = initWorker(controller1, controller2, current_settings)
            socketio.emit('current_state',  {'state': worker.getState().name})

    @socketio.on('req_shutdown')
    def handle_req_shutdown(msg):
        global worker
        global current_settings
        print('received req_shutdown')
        if worker.getState() == State.READY:
            print("Worker is not working, skip the reset request")
        else:
            pump_wait.set()
            worker.join()
            worker = initWorker(controller1, controller2, current_settings)
            socketio.emit('current_state',  {'state': worker.getState().name})

    @socketio.on('req_current_settings')
    def handle_req_current_settings(msg):
        print('received req_current_settings')
        socketio.emit('current_settings', worker.getSettings())

    @socketio.on('req_current_state')
    def handle_req_current_stete(msg):
        print('received req_current_state')
        socketio.emit('current_state',  {'state': worker.getState().name})

    print("start waterpump manager")
    #worker.start()
    # With debug mode on, print message in Worker class will be printed twice.
    # https://stackoverflow.com/questions/57344224/thread-is-printing-two-times-at-same-loop
    #app.run(host="0.0.0.0", port=5000, debug=True)
    socketio.run(app, host="0.0.0.0", port=22331)
