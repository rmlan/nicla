from time import sleep

import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import sys
import csv
import datetime
import os


# --- CONFIGURATION ---
SERIAL_PORT = 'COM10'  # !!! Át kell írni a megfelelő soros port nevére, pl. 'COM3' !!!
BAUD_RATE = 115200   # !!! írd át hogy ugyan arra amit a Arduino kódba is beállítottál ( void setup(){                )
                     #                                                                 (   Serial.begin(115200);      )
#-------------------------------------------
Logging_Enabled = True  # Ha False, akkor nem menti a log fájlokat, csak a grafikon frissül

SAVE_DIRECTORY = r"Z:\BOSCH projekt\Dashboard\NiclaSenseME-dashboard\Nicla_logs" # írd át hogy megadd hova mentse a program a log fájlokat, pl. r"C:\Users\YourUsername\Documents\NiclaLogs"
if Logging_Enabled:
    os.makedirs(SAVE_DIRECTORY, exist_ok=True)  # csinál egy új mappát ha nem létezik még


# Adjust how many data points are shown together on the X-axis
WINDOW_SIZE = 2000     

# Create a unique filename with the current date and time
current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
CSV_FILENAME = f"pressure_log_{current_time}.csv"
# ------------------------
FULL_CSV_PATH = os.path.join(SAVE_DIRECTORY, CSV_FILENAME)

# Initialize a fixed-size queue to hold the rolling window of data for the plot
data = deque([0.0] * WINDOW_SIZE, maxlen=WINDOW_SIZE)

# Initialize serial connection
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    print(f"Successfully connected to {SERIAL_PORT}")
except Exception as e:
    print(f"Error opening serial port {SERIAL_PORT}: {e}")
    print("Make sure the Serial Monitor in Arduino IDE is CLOSED.")
    sys.exit(1)

# Open the CSV file and write the header row
if Logging_Enabled:
    csv_file = open(FULL_CSV_PATH, mode='w', newline='')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["Index", "Time", "Pressure (Pa)"])  # átírhatod a fejlécet, ha más adatokat mentesz
    print(f"Logging live data to: {FULL_CSV_PATH}")

# Set up the matplotlib figure and axis
fig, ax = plt.subplots(figsize=(10, 6))
ax.set_title('Live Pressure Data (Nicla Sense ME)')
ax.set_xlabel('Time (Recent Samples)')
ax.set_ylabel('Pressure (Pa)')  #szintén átírhatod

# Create an empty line that we will update
line, = ax.plot(data, color='blue', linewidth=2)


def update(frame):
    i = 0
    # Read all available lines in the serial buffer to prevent lagging
    while ser.in_waiting:
        try:
            # Read line, decode, and strip whitespace/newlines
            raw_line = ser.readline().decode('utf-8').strip()
            
            
            if raw_line.endswith("Pa"):                  #  Ezt állítsd át annak megfelelően, hogy milyen formátumban küldi az adatot az Arduino. 
                clean_value = raw_line.replace("Pa", "") #  Például nálam ilyen adatok jönnek: "101325Pa" (string)
                pressure_val = float(clean_value)
                data.append(pressure_val)
                
                # Get current time with millisecond precision
                timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                
                # Log the data to our CSV file
                if Logging_Enabled:
                    csv_writer.writerow([i, timestamp, pressure_val])
                
        except (ValueError, UnicodeDecodeError):
            # Ignore garbled data that happens during connection/transmission
            pass
        i+=1

    # Update the graph line with the newly appended data
    line.set_ydata(data)
    
    # Autoscale the Y-axis to comfortably fit the current data window
    ax.relim()
    ax.autoscale_view(scalex=False, scaley=True)
    
    return line,

# Close the serial port and CSV file gracefully when the graph window is closed
def on_close(event):
    ser.close()
    if Logging_Enabled:
        print("Closing connection and saving log file...")
        csv_file.close()
    else:
        print("Closing connection...")

fig.canvas.mpl_connect('close_event', on_close)

# Set up the animation to refresh every 20 milliseconds (50 frames per second)
ani = animation.FuncAnimation(fig, update, interval=20, cache_frame_data=False) # Írd át az interval értékét, ha gyorsabb vagy lassabb frissítést szeretnél

plt.tight_layout()
plt.show()