from time import sleep
import RPi.GPIO as GPIO


class Controller:
    def __init__(self, motorid:int, m1pin: int, m2pin: int, pwmpin: int, testmode: bool) -> None:

        self.motorid = motorid
        self.testmode = testmode
        self.freq = 50
        self.duty = 10
        self.m1pin = m1pin
        self.m2pin = m2pin

        if self.testmode:
            print(' -- (TEST MODE) --')
            print("None of motors are set up.")
        else:
            print(' -- (REAL MODE) --')
            GPIO.setmode(GPIO.BCM)

            GPIO.setup(m1pin,GPIO.OUT)
            GPIO.setup(m2pin,GPIO.OUT)
            GPIO.setup(pwmpin,GPIO.OUT)

            self.motor = GPIO.PWM(pwmpin, self.freq)
            self.motor.start(self.duty)

            print("Motor initialized with the following pins")
            print("M1 pin: %d, M2 pin: %d, PWM pin: %d" % (m1pin, m2pin, pwmpin))
            print("frequency: %d, duty: %d" % (self.freq, self.duty))


    def start(self) -> None:
        print("No.", self.motorid, "Start Pump Controll")
        if self.testmode:
            pass
        else:
            GPIO.output(self.m1pin, 0)
            GPIO.output(self.m2pin, 1)
    
    def stop(self) -> None:
        print("No.", self.motorid, "Stop Pump Controll")
        if self.testmode:
            pass
        else:
            GPIO.output(self.m1pin, 0)
            GPIO.output(self.m2pin, 0)

    def delete(self) -> None:
        print("Controller Deleted")
        if self.testmode:
            pass
        else:
            GPIO.cleanup()

    def speed(self, duty) -> None:
        if 0 < duty and duty < 50:
            self.motor.ChangeDutyCycle(duty)
        else:
            print("duty value exceed what we expect :", duty)


if __name__ == "__main__":
    controller1 = Controller(motorid=1, m1pin=6, m2pin=13, pwmpin=12, testmode=False)
    controller1.start()
    sleep(2)
    controller1.speed(30)
    sleep(2)
    controller1.stop()