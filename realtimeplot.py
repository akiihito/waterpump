import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import serial
# Create figure for plotting
fig = plt.figure()
plt.rcParams["font.size"] = 25
ax = fig.add_subplot(1, 1, 1)
xs = []
ys = []


readSer = serial.Serial('/dev/cu.usbmodem1401',9600, timeout=3)


# This function is called periodically from FuncAnimation
def animate(i, xs, ys):

    value = int(readSer.readline().strip())
    # Add x and y to lists
    xs.append(i)
    ys.append(value)
    print(value)

    # Limit x and y lists to 20 items
    xs = xs[-100:]
    ys = ys[-100:]

    # Draw x and y lists
    ax.clear()
    ax.plot(xs, ys)

    # Format plot
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)

# Set up plot to call animate() function periodically
ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys), interval=500, cache_frame_data=False)
plt.show()
