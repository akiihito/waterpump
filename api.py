from time import sleep
from fastapi import FastAPI
import uvicorn
import argparse
import threading
from controller import Controller
from awsclient import AWSClient
import ctypes

parser = argparse.ArgumentParser(description="two water pump controller")
parser.add_argument('-s', '--speed', type=int, default=20, help='motor speed (duty rate, default 20)')
parser.add_argument('-t', '--test', action='store_true', default=False, help='Dry run mode')
args = parser.parse_args()


class CustomThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        threading.Thread.__init__(self, group=group, target=target, name=name)
        self.args = args
        self.kwargs = kwargs
        return
    
    def run(self):
        self._target(*self.args, **self.kwargs)

    def get_id(self):
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id
    
    # 強制終了させる関数
    def raise_exception(self):
        thread_id = self.get_id()
        resu = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), ctypes.py_object(SystemExit))
        if resu > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread_id), 0)
            print('Failure in raising exception')


def task(t:int):
    global running_pump
    sleep(t)
    if running_pump != None:
        running_pump.stop()
        running_pump = None

app = FastAPI()

## 給水と排水の方向は後で決定する. とりあえず id=1 が給水, id=2 が排水
supply = Controller(motorid=1, m1pin=6, m2pin=13, pwmpin=12, testmode=args.test)
drain = Controller(motorid=2, m1pin=20, m2pin=21, pwmpin=26, testmode=args.test)
supply.speed(args.speed)
drain.speed(args.speed)

## 実行中のポンプ（給水 or 排水）
running_pump : Controller = None
## 実行中の停止タイマー
worker : CustomThread

## AWSクライアント（今の所はシリアル通信）
awsclient = AWSClient('/dev/ttyS0', 115200)

@app.get("/")
async def root():
    return {"message": "Water pump control API"}


@app.get("/api2/{command}")
async def api(command: str, duration: int = 5, speed: int = 70, ratio: int = 20):
    global running_pump
    global worker

    if command == 'stop' and running_pump != None:
        running_pump.stop()
        running_pump = None
        worker.raise_exception()
        duration = 0
        speed = 0
        msg = "stop pump"
        return {"cmd": command, "duration": duration, "speed": speed, "ratio": ratio, "message": msg}

   ## 給水・排水方向の設定
    if command == 'supply' and running_pump == None:
        awsclient.send_supply()
        running_pump = supply
        msg = "supply pump start"
    elif command == 'drain' and running_pump == None:
        awsclient.send_drain()
        running_pump = drain
        msg = "drain pump start"
    else:
        msg = "pump has already started"
        return {"cmd": command, "duration": duration, "speed": speed, "ratio": ratio, "message": msg}

    ## 実行時間の設定
    worker = CustomThread(target=task, args=(duration,))

    ## 給排水の実行と停止タイマーの起動
    running_pump.speed(speed)
    running_pump.start()
    worker.start()
 
    return {"cmd": command, "duration": duration, "speed": speed, "ratio": ratio, "message": msg}



@app.get("/api/{command}")
async def api(command: str, duration: int = 2, speed: int = 20):
    global running_pump
    global worker

    if command == 'stop' and running_pump != None:
        running_pump.stop()
        running_pump = None
        worker.raise_exception()
        duration = 0
        speed = 0
        msg = "stop pump"
        return {"cmd": command, "duration": duration, "speed": speed, "message": msg}

    
    ## 給水・排水方向の設定
    if command == 'supply' and running_pump == None:
        awsclient.send_supply()
        running_pump = supply
        msg = "supply pump start"
    elif command == 'drain' and running_pump == None:
        awsclient.send_drain()
        running_pump = drain
        msg = "drain pump start"
    else:
        msg = "pump has already started"
        return {"cmd": command, "duration": duration, "speed": speed, "message": msg}

    ## 実行時間の設定
    worker = CustomThread(target=task, args=(duration,))

    ## 給排水の実行と停止タイマーの起動
    running_pump.speed(speed)
    running_pump.start()
    worker.start()
 
    return {"cmd": command, "duration": duration, "speed": speed, "message": msg}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")