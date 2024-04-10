import time


class Controller:
    def __init__(self, pinNo: int) -> None:
        self.pinno = pinNo
        print("Controller initialized with a pin number: ", pinNo)

    def start(self) -> None:
        print("No.", self.pinno, "Pump Start Pump Controll")
    
    def stop(self) -> None:
        print("No.", self.pinno, "Pump Stop Pump Controll")
