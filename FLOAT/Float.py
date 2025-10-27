import msvcrt
import serial
import time
import matplotlib.pyplot as plt

def splitString(string, pref, end):
    """Extract a substring between two markers"""
    try:
        return string.split(pref)[1].split(end)[0]
    except IndexError:
        print(f"Error parsing string: {string}")
        return "0"

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
    
    # Setup serial connection
    try:
        ser = serial.Serial("COM8", 9600, timeout=10)
        ser.reset_input_buffer()
        ser.write(b"s\n")  # Send initial stop command
        print("Connected to serial port COM8")
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        exit(1)
    
    dataString = ""
    
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
            
            # Check for keyboard input
            if msvcrt.kbhit():
                key = msvcrt.getch()
                
                # Handle Enter key
                if key == b"\r":
                    print(f"\nSending: {dataString}")
                    ser.write(f"{dataString}\n".encode("utf-8"))
                    dataString = ""
                # Handle backspace
                elif key == b"\b":
                    if dataString:
                        dataString = dataString[:-1]
                        print(f"\rCommand: {dataString}", end="", flush=True)
                # Handle Ctrl+C
                elif key == b"\x03":
                    raise KeyboardInterrupt
                # Handle regular characters
                else:
                    try:
                        char = key.decode("utf-8")
                        dataString += char
                        print(f"\rCommand: {dataString}", end="", flush=True)
                    except UnicodeDecodeError:
                        pass
    
    except KeyboardInterrupt:
        print("\nExiting program...")
    finally:
        ser.close()
        print("Serial port closed")