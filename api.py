from time import sleep
from fastapi import FastAPI
import uvicorn
import argparse
from controller import Controller

parser = argparse.ArgumentParser(description="two water pump controller")
parser.add_argument('-s', '--speed', type=int, default=20, help='motor speed (duty rate, default 20)')
parser.add_argument('-t', '--test', action='store_true', default=False, help='Dry run mode')
args = parser.parse_args()


app = FastAPI()

controller1 = Controller(motorid=1, m1pin=6, m2pin=13, pwmpin=12, testmode=args.test)
controller2 = Controller(motorid=2, m1pin=20, m2pin=21, pwmpin=26, testmode=args.test)
controller1.speed(args.speed)
controller2.speed(args.speed)

@app.get("/")
async def root():
    controller1.start()
    controller2.start()
    sleep(2)
    controller1.stop()
    controller2.stop()
    return {"message": "Hello World"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")