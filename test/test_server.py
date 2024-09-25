import json
import random
import time
from fastapi import FastAPI
import uvicorn
import threading, ctypes
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

running_pump = None
control_duration = 0
pump_speed = 0
valve_open_ratio = 0

waterlevel = 0
interval = 0.5


############ puslish waterlevel ###############
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


def publish(client):
    topic = 'dummy/waterlevel'
    msg = json.dumps({"waterlevel": waterlevel})
    result = client.publish(topic, msg)
    status = result[0]
    if status == 0:
        print(f"Send `{msg}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")


##################################################################
# pump speed は 100 で max
# valve open rate は 0 - 100 [%]
# pump speed = 100, valve open ratio = 100 で 3cm/s
def control_task(client: mqtt_client):
    global control_duration
    global pump_speed
    global valve_open_ratio
    global waterlevel
    global interval
    while True:
        if control_duration > 0:
            if running_pump == 'supply':
                ## pump speed と valve open rate に基づいて水位を変更
                waterlevel += 3 * interval * pump_speed * 0.01 * valve_open_ratio * 0.01
            elif running_pump == 'drain':
                waterlevel += -3 * interval * pump_speed * 0.01 * valve_open_ratio * 0.01
            else:
                print("No pump running...")
            control_duration -= interval
        ## 現在水位をpublish
        publish(client)
        time.sleep(interval)


@app.get("/api2/servo")
async def api(ratio: float = 20):
    global valve_open_ratio
    if running_pump == None:
        msg = "No pump running..."
    else:
        valve_open_ratio = ratio
        msg = 'Dummy controller accepted your request.'
    return {"cmd": "api2/servo", "ratio": ratio, "message": msg}


@app.get("/api2/{command}")
async def api(command: str, duration: int = 5, speed: int = 70, ratio: int = 20):
    global running_pump
    global control_duration
    global pump_speed
    global valve_open_ratio

    if command == 'stop':
        control_duration = 0
    else:
        running_pump = command

    control_duration = duration
    pump_speed = speed
    valve_open_ratio = ratio
    msg = 'Dummy controller accepted your request.'
    return {"cmd": command, "duration": duration, "speed": speed, "ratio": ratio, "message": msg}


if __name__ == "__main__":
    ## publish スレッド実行
    client = connect_mqtt()
    CustomThread(target=control_task, args=(client,)).start()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")