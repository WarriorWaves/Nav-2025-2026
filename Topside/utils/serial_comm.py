import threading
import serial
import time


class SerialPort:
    def __init__(self, port, baudrate=9600, timeout=1.0, name=""):
        self._lock     = threading.Lock()
        self._ser      = None
        self.port      = port
        self.name      = name or port
        self.connected = False
        try:
            self._ser = serial.Serial(port, baudrate, timeout=timeout)
            time.sleep(2)
            self._ser.reset_input_buffer()
            self.connected = True
            print(f"[Serial] Connected: {self.name} on {port}")
        except serial.SerialException as e:
            print(f"[Serial] WARNING — could not open {self.name} ({port}): {e}")
            print("[Serial] Run 'ls /dev/cu.*' and update ROV_PORT in config.py")

    def send(self, command):
        with self._lock:
            if not self.connected or self._ser is None:
                return
            try:
                self._ser.write(f"{command}\n".encode("utf-8"))
            except Exception as e:
                print(f"[Serial] Write error on {self.name}: {e}")
                self.connected = False

    def readline(self):
        with self._lock:
            if not self.connected or self._ser is None:
                return None
            try:
                if self._ser.in_waiting > 0:
                    return self._ser.readline().decode("utf-8", errors="replace").strip()
            except Exception as e:
                print(f"[Serial] Read error on {self.name}: {e}")
            return None

    def close(self):
        with self._lock:
            if self._ser and self._ser.is_open:
                self._ser.close()
            self.connected = False
            print(f"[Serial] Closed: {self.name}")