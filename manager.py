import sys
import signal
import argparse
import threading

from asyncio import Queue
from flask import Flask, render_template

from controller import Controller


parser = argparse.ArgumentParser(description="two water pump controller")
parser.add_argument('-d', '--duration', type=int, default=5, help='duration time to turn on the pump (default 5 second)')
parser.add_argument('-i', '--interval', type=int, default=10, help='interval time to the next run (default 10 second)')
args = parser.parse_args()


pump_wait = threading.Event()


class Worker(threading.Thread):
    def __init__(self, controller1, controller2, queue):
        super().__init__()
        self.controller1 = controller1
        self.controller2 = controller2
        self.interval = 1
        self.duration = 0
        self.queue = queue
        self.terminate = False

    def setInterval(self, interval: int) -> None:
        print("set the pump interval to ", interval)
        self.interval = interval

    def setDuration(self, duration: int) -> None:
        print("set the pump duration to ", duration)
        self.duration = duration

    def softTerminate(self):
        self.terminate = True

    def run(self):
        while not pump_wait.is_set():
            if self.terminate:
                break
            if not self.queue.empty():
                self.duration = int(self.queue.get())

            ############# pump1 running ###############
            self.controller1.start()
            pump_wait.wait(self.duration)
            self.controller1.stop()
            ###########################################
            pump_wait.wait(self.interval)
            ############# pump2 running ###############
            self.controller2.start()
            pump_wait.wait(self.duration)
            self.controller2.stop()
            ###########################################
            pump_wait.wait(self.interval)
        else:
            print("Terminate all pumps immediately")
            self.controller1.stop()
            self.controller2.stop()


if __name__ == '__main__':

    def handler(signo, frame):
        print("Interrupted by %d, shutting down" % signo)
        pump_wait.set()
        sys.exit()

    for sig in ('TERM', 'INT'):
        signal.signal(getattr(signal, 'SIG'+sig), handler)


    queue = Queue(1)
    controller1 = Controller(18)
    controller2 = Controller(19)
    worker = Worker(controller1, controller2, queue)
    worker.setInterval(args.interval)
    worker.setDuration(args.duration)

    app = Flask(__name__)

    @app.route("/")
    def hello_world():
        return render_template('index.html')

    print("start waterpump manager")
    worker.start()
    # With debug mode on, print message in Worker class will be printed twice.
    # https://stackoverflow.com/questions/57344224/thread-is-printing-two-times-at-same-loop
    #app.run(host="0.0.0.0", port=5000, debug=True)
    app.run(host="0.0.0.0", port=5000, debug=False)
