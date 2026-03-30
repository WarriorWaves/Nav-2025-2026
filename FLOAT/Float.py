import time
import sys
import platform
import serial
from serial.tools import list_ports
import matplotlib.pyplot as plt

def splitString(string, pref, end):
    """Extract a substring between two markers"""
    try:
        return string.split(pref)[1].split(end)[0]
    except IndexError:
        print(f"Error parsing string: {string}")
        return "0"

class _WindowsKB:
    def kbhit(self):
        import msvcrt
        return msvcrt.kbhit()
    def getch(self):
        import msvcrt
        return msvcrt.getch()
    def cleanup(self):
        return

class _PosixKB:
    def __init__(self):
        import sys, termios, tty
        self.fd = sys.stdin.fileno()
        self.termios = termios
        self.old = termios.tcgetattr(self.fd)
        tty.setcbreak(self.fd)
    def kbhit(self):
        import select, sys
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        return bool(dr)
    def getch(self):
        import sys
        return sys.stdin.read(1)
    def cleanup(self):
        self.termios.tcsetattr(self.fd, self.termios.TCSADRAIN, self.old)

class Keyboard:
    def __init__(self):
        if platform.system() == 'Windows':
            self.impl = _WindowsKB()
            self.is_windows = True
        else:
            self.impl = _PosixKB()
            self.is_windows = False
    def kbhit(self):
        return self.impl.kbhit()
    def getch(self):
        return self.impl.getch()
    def cleanup(self):
        try:
            self.impl.cleanup()
        except Exception:
            pass

def choose_serial_port(default_windows='COM8'):
    system = platform.system()
    if system == 'Windows':
        return default_windows
    # macOS / Linux: try to auto-detect USB/ACM/serial ports
    ports = list(list_ports.comports())
    if not ports:
        raise serial.SerialException('No serial ports found')
    # Prefer common usb/arduino devices
    for p in ports:
        dev = p.device.lower()
        desc = (p.description or '').lower()
        if 'usb' in desc or 'arduino' in desc or 'usb' in dev or 'acm' in dev or 'modem' in desc:
            return p.device
    # fallback: if only one port, use it
    if len(ports) == 1:
        return ports[0].device
    # ask user to choose
    print('Multiple serial ports detected:')
    for i, p in enumerate(ports):
        print(f"{i}: {p.device} ({p.description})")
    while True:
        sel = input('Select port index: ')
        try:
            idx = int(sel)
            return ports[idx].device
        except Exception:
            print('Invalid selection, try again')


if __name__ == "__main__":
    # Initialize data storage
    depthData = []
    timeData = []
    
    # Setup real-time plotting
    plt.ion()  # Turn on interactive mode
    fig, ax = plt.subplots()
    ax.set_title("Depth vs Time")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Depth (m)")
    ax.grid(True)
    
    # Setup serial connection (auto-detect port for mac / use COM for Windows)
    try:
        port = choose_serial_port('COM8')
        ser = serial.Serial(port, 9600, timeout=10)
        if hasattr(ser, 'reset_input_buffer'):
            try:
                ser.reset_input_buffer()
            except Exception:
                pass
        # send initial stop command
        try:
            ser.write(b"s\n")
        except Exception:
            pass
        print(f"Connected to serial port {port}")
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        sys.exit(1)

    dataString = ""
    kb = Keyboard()
    
    print("Type commands and press Enter to send. Press Ctrl+C to exit.")
    
    try:
        while True:
            # Check for incoming serial data
            if ser.in_waiting > 0:
                line = ser.readline().decode("utf-8", errors="replace").rstrip()
                print(f"Received: {line}") 
                
                # Process data lines
                if "DATA" in line:
                    try:
                        parts = line.split(',')
                        if len(parts) == 4 and parts[0] == 'DATA':
                            pressure = int(parts[1])
                            depth = int(parts[2])
                            time_val = int(parts[3])

                            # Store data
                            depthData.append(depth / 100.0)
                            timeData.append(time_val / 10.0)
 
                            ax.clear()
                            ax.plot(timeData, depthData, "ro-")
                            ax.set_ylim(-1, 5)
                            ax.set_title("Depth vs Time")
                            ax.set_xlabel("Time (s)")
                            ax.set_ylabel("Depth (m)")
                            ax.grid(True)

                            plt.draw()
                            plt.pause(0.01)

                    except (ValueError, IndexError) as e:
                        print(f"Error parsing data line: {line}")
            
            # Check for keyboard input (cross-platform)
            try:
                if kb.kbhit():
                    key = kb.getch()
                    # Normalize to string
                    if isinstance(key, bytes):
                        # Windows msvcrt.getch returns bytes
                        if key == b"\r":
                            ch = '\n'
                        else:
                            try:
                                ch = key.decode('utf-8')
                            except Exception:
                                ch = ''
                    else:
                        ch = key

                    # Handle Enter key (CR or LF)
                    if ch in ('\r', '\n'):
                        print(f"\nSending: {dataString}")
                        try:
                            ser.write(f"{dataString}\n".encode("utf-8"))
                        except Exception:
                            pass
                        dataString = ""
                    # Handle backspace (DEL or backspace)
                    elif ch in ('\x7f', '\b'):
                        if dataString:
                            dataString = dataString[:-1]
                            print(f"\rCommand: {dataString}", end="", flush=True)
                    # Handle Ctrl+C
                    elif ch == '\x03':
                        raise KeyboardInterrupt
                    # Regular characters
                    else:
                        dataString += ch
                        print(f"\rCommand: {dataString}", end="", flush=True)
            except (IOError, OSError):
                pass
    
    except KeyboardInterrupt:
        print("\nExiting program...")
    finally:
        try:
            ser.close()
        except Exception:
            pass
        try:
            kb.cleanup()
        except Exception:
            pass
        print("Serial port closed")