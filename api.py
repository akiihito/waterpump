from time import sleep
from fastapi import FastAPI
import uvicorn
import argparse
import threading
from controller import Controller
import ctypes

parser = argparse.ArgumentParser(description="two water pump controller")
parser.add_argument('-s', '--speed', type=int, default=20, help='motor speed (duty rate, default 20)')
parser.add_argument('-t', '--test', action='store_true', default=False, help='Dry run mode')
args = parser.parse_args()


class CustomThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._run = self.run
        self.run = self.set_id_and_run

    def set_id_and_run(self):
        self.id = threading.get_native_id()
        self._run()

    def get_id(self):
        return self.id
        
    def raise_exception(self):
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(self.get_id()), 
            ctypes.py_object(SystemExit)
        )
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_long(self.get_id()), 
                0
            )
            print('Failure in raising exception')

def task(ctrl: Controller, t:int):
    sleep(t)
    ctrl.stop()

app = FastAPI()

## 給水と排水の方向は後で決定する. とりあえず id=1 が給水, id=2 が排水
supply = Controller(motorid=1, m1pin=6, m2pin=13, pwmpin=12, testmode=args.test)
drain = Controller(motorid=2, m1pin=20, m2pin=21, pwmpin=26, testmode=args.test)
supply.speed(args.speed)
drain.speed(args.speed)

## 実行中のポンプ（給水 or 排水）
running_pump : Controller = None
## Timer スレッド
worker: CustomThread = None

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/api/{command}")
async def api(command: str, duration: int = 2, speed: int = 20):
    global running_pump
    global worker

    if command == 'stop':
        running_pump.stop()
        duration = 0
        speed = 0
        ## タイマースレッドの後片付け
        if worker != None:
            worker.raise_exception()
            worker = None
    
    if command == 'supply':
        running_pump = supply
    elif command == 'drain':
        running_pump = drain
    if duration != 0:
        timer = CustomThread(target=task, args=(running_pump, duration), daemon=True)
        timer.start()
        
    return {"cmd": command, "duration": duration, "speed": speed}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")