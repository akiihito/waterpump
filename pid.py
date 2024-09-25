import json
import math
import random
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn
import time
import datetime
import statistics
import threading, ctypes
import urllib.request
from paho.mqtt import client as mqtt_client


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


app = FastAPI()
templates = Jinja2Templates(directory="templates")

## 目標水位 [cm]
target_waterlevel = 0
## 目標時刻
deadline = 0
## 現在の水位 [cm]
current_waterlevel = 0
## 目標注水速度 [cm/s]
target_speed = 0
## 現在の注水速度 [cm/s]
current_speed = 0
## バルブの解放率 [%]
release_rate = 0
## 注水方向（注水・排水）
direction = None
## PID制御実行中タスク
working = None

## PID 制御の平均収束時間 [s]
avg_convergence = 0


def request_valve_control(open_rate):
    url = 'http://localhost:8000/api2/servo?ratio=' + str(open_rate)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as res:
        print(res.read())


def request_pump_start():
    if direction == None:
        print("no direction defined...")
        return
    ## TODO: speed を 100 で設定できるように controller.py を変更する
    url = 'http://localhost:8000/api2/' + direction + '?duration=' + str(deadline) + '&speed=100&ratio=0'
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as res:
        print(res.read())


def request_pump_stop():
    url = 'http://localhost:8000/api2/stop'
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as res:
        print(res.read())


############ PID control ########################
# -------------------------------------- PID制御関連 ----------------------------------------
def valve_release_rate(m):
    ## 操作量 m を バルブの解放値に変換
    ## （本来は PID 関数の中で実施すべきかも？）
    return (abs(m) * 30) % 100


def PID(kp, ki, kd, theta_goal, theta_current, error_sum, error_pre):
    error = theta_goal - theta_current# 偏差（error）を計算
    error_sum += error # 偏差の総和（積分）を計算
    error_diff = error-error_pre # PI制御からの追加：1時刻前の偏差と現在の偏差の差分（微分）を計算
    m = (kp * error) + (ki * error_sum) + (kd*error_diff) # 操作量を計算
    return m, error_sum, error


def PIDcontrol():
    global working
    global target_speed
    global current_speed
    global target_waterlevel
    ## 注水速度の履歴（標準偏差を算出するのに利用）
    speed_data = []
    ## 標準偏差を計算する際に利用されるデータ数
    datanum = 10
    ## 注水速度の安定制御を示す指標(標準偏差の閾値)
    stable_control = 0.5
    ## 注水速度の履歴に対する標準偏差
    speed_stdev = stable_control * 100

    # 係数設定 --------------------
    theta_start = 0  # 注水速度の初期値 [cm/s]
    theta_goal = target_speed  # 目標注水速度 [cm/s]
    offset = 0
    kp = 0.15
    ki = 0.4
    kd = 0.2
    # その他初期設定
    error_sum = 0.0
    error_pre = 0.0
    theta_current = theta_start

    print("---------------------- PID control start -----------------------------")
    print('target waterlevel[cm]: ', target_waterlevel)
    print('target speed   [cm/s]: ', target_speed)
    print('current speed  [cm/s]: ', current_speed)

    # PID制御 -----------------------
    while speed_stdev > stable_control: ## 制御が収束したら終了
        m, error_sum, error = PID(kp, ki, kd, theta_goal, theta_current, error_sum, error_pre) # 操作量を計算
        # 操作量 m に基づいてバルブの解放率を決定・バルブ操作をリクエスト
        request_valve_control(valve_release_rate(m))
        theta_current -= offset
        speed_data.append(current_speed)
        error_pre = error # 一時刻前の偏差として保存しておく（D制御用）
        # 一定時間停止して制御が反映されるまで待つ
        time.sleep(0.5)

        theta_current = current_speed
        # 現在の注水速度に対して標準偏差を計算しておく
        if len(speed_data) > datanum:
            speed_stdev = statistics.stdev(speed_data[-datanum:])
        print('------ theta_current: ', theta_current)
        print('------ m: ', m)
        print('------ stddev: ', speed_stdev)

def control_task():
    global working
    PIDcontrol()
    print("---------------------- PID control finished -----------------------------")
    print("current speed: ", current_speed)

    ## 実行中のPIDタスクを None に設定（ここで実行して良いのかは要検討）
    working = None
    return
    while True:
        ## 1.PID制御を実行
        PIDcontrol()
        ## 2.現在の注水速度から、目標到達時刻を計算
        estimated_time = (target_waterlevel - current_waterlevel) / current_speed
        ## 3.到達時間が設定された時刻からずれているようなら注水速度を変更してPID制御を再度実行
        ## （TODO: 誤差込みで条件設定できるように後で変更）
        if datetime.date.now() + datetime.timedelta(estimated_time) < deadline:
            break
        ## (TODO: 注水速度を時折監視して、変化があったらPID制御を再実行できるように変更する）
        if deadline < datetime.datetime.now():
            break


def subscribe_task(client: mqtt_client):
    subscribe(client)
    client.loop_forever()


############ subscribe waterlevel ###############
def connect_mqtt() -> mqtt_client:
    broker = 'localhost'
    port = 1883
    client_id = f'subscribe-{random.randint(0, 100)}'

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def subscribe(client: mqtt_client):
    topic = "dummy/waterlevel"
    def on_message(client, userdata, msg):
        global current_waterlevel
        global current_speed
        prev_waterlevel = current_waterlevel
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        data = json.loads(msg.payload)

        current_speed = (data['waterlevel'] - prev_waterlevel) / 0.5
        current_waterlevel = data['waterlevel']

    client.on_message = on_message
    client.subscribe(topic)


############ fastAPI ############################
@app.get("/")
async def root():
    return {"message": "Water pump control API"}


@app.get("/api2/control/stop")
async def api():
    if working != None:
        ## PID 制御の停止とポンプの停止
        msg = "stop control is accepted"
        request_pump_stop()
        working.raise_exception()
        working = None
    else:
        msg = "PID control has not been woking right now"
    return {"message": msg}


@app.get("/api2/control/waterlevel")
async def api(waterlevel: int = 0, seconds: int = 0):
    ## 目標水位
    global target_waterlevel
    ## 目標時刻
    global deadline
    ## 目標注水速度
    global target_speed
    ## PID制御実行中フラグ
    global working
    ## 注水方向
    global direction

    if waterlevel <= 0 or seconds <= 0:
        msg = "bad request: waterlevel and time must be more than zero"
    elif working != None:
        msg = "PID control has been working, this request is skipped"
    else:
        ## PID 制御のパラメータ設定
        target_waterlevel = waterlevel
        ## 速度マイナスの場合は排水・プラスの場合は給水
        direction = "supply" if current_waterlevel < waterlevel else "drain"
        #deadline = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        deadline = seconds
        target_speed = target_waterlevel / seconds
        ## 注水ポンプの始動
        request_pump_start()
        ## PIDタスクの起動
        working = CustomThread(target=control_task)
        working.start()
        msg = "This request is accepted, PID control task is generated"
    return {"message": msg, "waterlevel": waterlevel, "time": seconds}


@app.get("/api2/view/graph", response_class=HTMLResponse)
async def api(request: Request):
    return templates.TemplateResponse("graph.html", {"request": request, "message": "Hello World"})


@app.get("/api2/data/waterlevel")
async def api():
    global target_waterlevel
    global current_waterlevel
    global target_speed
    global current_speed
    global deadline

    return {"target_waterlevel": target_waterlevel,            
            "current_waterlevel": current_waterlevel,
            "current_speed": current_speed,
            "target_speed": target_speed,
            "deadline": deadline}


if __name__ == "__main__":
    client = connect_mqtt()
    CustomThread(target=subscribe_task, args=(client,)).start()
    uvicorn.run(app, host="0.0.0.0", port=12233, log_level="debug")