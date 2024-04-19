import time


class Controller:
    def __init__(self, pinNo: int, mode: bool) -> None:
        self.pinno = pinNo
        self.mode = mode ## True: test mode (does not run an actual device)
        print("Controller initialized with a pin number: ", pinNo, )
        if (self.mode):
            print(' -- (TEST MODE) --')

    def start(self) -> None:
        print("No.", self.pinno, "Pump Start Pump Controll")
    
    def stop(self) -> None:
        print("No.", self.pinno, "Pump Stop Pump Controll")
