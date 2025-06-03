import time
import pigpio


class Servo:
    def __init__(self, pwmpin: int, testmode: bool) -> None:
        self.testmode = testmode
        self.pwmpin = pwmpin

        if self.testmode:
            print(' -- (TEST MODE) --')
            print("None of servos are set up.")
        else:
            print(' -- (REAL MODE) --')
            self.pi = pigpio.pi()
            self.pi.set_mode(pwmpin, pigpio.OUTPUT)

    def _ratio2pulsewidth(self, ratio: int) -> int:
        # 一般的な範囲：0%→500μs、100%→2500μs
        # サーボの範囲：0%→1000μs、100%→1550μs
        pulse_range = 550  # μs
        base = 1000  # μs

        try:
            pulse = int(pulse_range / 100 * ratio + base)
        except ZeroDivisionError:
            pulse = base
        return pulse

    def valve_open(self, ratio: int) -> None:
        pulse = self._ratio2pulsewidth(ratio)
        print("Valve open :", ratio, "[%] →", pulse, "μs")
        if self.testmode:
            pass
        else:
            self.pi.set_servo_pulsewidth(self.pwmpin, pulse)
            time.sleep(0.5)

    def _stop(self) -> None:
        if self.testmode:
            pass
        else:
            self.pi.set_servo_pulsewidth(self.pwmpin, 0)
            self.pi.stop()


if __name__ == "__main__":
    sv1 = Servo(pwmpin=22, testmode=False)
    sv2 = Servo(pwmpin=23, testmode=False)
    print("SV1 ",) 
    sv1.valve_open(0)
    print("SV2 ",) 
    sv2.valve_open(0)
    print("SV1 ",) 
    sv1.valve_open(30)
    time.sleep(2)
    print("SV1 ",) 
    sv1.valve_open(60)
    time.sleep(2)
    print("SV1 ",) 
    sv1.valve_open(90)
    time.sleep(2)
    print("SV2 ",) 
    sv2.valve_open(30)
    time.sleep(2)
    print("SV2 ",) 
    sv2.valve_open(60)
    time.sleep(2)
    print("SV2 ",) 
    sv2.valve_open(90)
    time.sleep(2)
    print("SV1 ",) 
    sv1._stop()
    print("SV2 ",) 
    sv2._stop()
