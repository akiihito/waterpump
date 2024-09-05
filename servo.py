import time
import RPi.GPIO as GPIO


class Servo:
    def __init__(self, pwmpin: int, testmode: bool, freq: int = 50) -> None:
        
        self.testmode = testmode
        self.freq = freq

        if self.testmode:
            print(' -- (TEST MODE) --')
            print("None of servos are set up.")
        else:
            print(' -- (REAL MODE) --')
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(pwmpin, GPIO.OUT)

            self.sv = GPIO.PWM(pwmpin, self.freq)
            #Duty Cycle 0%
            #self.sv.start(0.0)

    def _ratio2duty(self, ratio: int) -> float:
        # roughly...
        # 100%->7.3, 70%->6.5, 40%->6.0, 10%->5.5, 0%->5.0
        dutyrange = 2.3
        base = 5.0
        try:
            duty = dutyrange / 100 * ratio + base
        except ZeroDivisionError:
            duty = base
        return duty
    
    def valve_open(self, ratio: int) -> None:
        duty = self._ratio2duty(ratio)
        print("Valve open :", ratio, "[%]")
        if self.testmode:
            pass
        else:
            self._start()
            self.sv.ChangeDutyCycle(duty)
            time.sleep(0.5)
            self._stop()

    def _start(self) -> None:
        if self.testmode:
            pass
        else:
            self.sv.start(0.0)

    def _stop(self) -> None:
        if self.testmode:
            pass
        else:
            self.sv.stop()


if __name__ == "__main__":
    sv1 = Servo(pwmpin=22, testmode=False)
    sv2 = Servo(pwmpin=23, testmode=False)
    sv1.valve_open(0)
    sv2.valve_open(0)
    sv1.valve_open(30)
    time.sleep(2)
    sv1.valve_open(60)
    time.sleep(2)
    sv1.valve_open(90)
    time.sleep(2)
    sv2.valve_open(30)
    time.sleep(2)
    sv2.valve_open(60)
    time.sleep(2)
    sv2.valve_open(90)
    time.sleep(2)