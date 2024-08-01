import serial


class AWSClient:
    def __init__(self, port, baudrate):
        self.ser = serial.Serial(port, baudrate)

    def send_supply(self):
        self.ser.write(b"supply\0")
    
    def send_drain(self):
        self.ser.write(b"drain\0")


if __name__ == "__main__":
    # temporally use serial line, instead of updating AWS IoT shadow
    client = AWSClient('/dev/ttyS0', 115200)
    client.send_drain()