from pydualsense import *
import time
import asyncio, telnetlib3
import math
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int

CW = True # clockwise direction
CCW = False # counter clockwise direction

X_MIN = 5
X_MAX = 525

Y_MIN = 5
Y_MAX = 1280

SPEED = 1500
WIPE_SPEED = 4000

# create dualsense
dualsense = pydualsense()
# find device and initialize
dualsense.init()

async def main():
    print("Welcome to SandSketch!")
    print()
    print("Use left and right joysticks like an etch-a-sketch.")
    print()
    print("To draw arcs, circles, or spirals, press the circle button to set the center point, then move a distance away which will set the radius.")
    print()
    print("Press and hold the left joystick to draw a counterclockwise arc or circle.")
    print("Press and hold the right joystick to draw a clockwise arc or circle.")
    print()
    print("You can then move further away from the center point to draw concentric circles.")
    print("Press the R1 or L1 buttons to draw tight spirals.")
    print("Press the R2 or L2 buttons to draw loose spirals.")
    print()
    print("Press the options button (the one with the three lines) to home the table.")
    print()


    reader, writer = await telnetlib3.open_connection("192.168.1.55", 8080)
    reply = await reader.read(128) # read the GRBL header
    print('reply:', reply)

    gcode = f"G1 F{SPEED}\n" # set speed
    writer.write(gcode)
    reply = await reader.read(128)
    print('reply:', reply)

    gcode = f"?\n"
    writer.write(gcode)
    reply = await reader.read(128) # should show status and location
    print('reply:', reply)

    x = float(reply.split('|')[1].split(':')[1].split(',')[0]) # get current xpos
    y = float(reply.split('|')[1].split(':')[1].split(',')[1]) # get current ypos

    reply = await reader.read(128) # should be "ok"

    rate = 3

    arc_center = Point(x, y)

    # read controller state until PlayStation button is pressed
    while not dualsense.state.ps:
        time.sleep(0.06)
        points = []
        gcode = ""
        gcode_post = ""

        if dualsense.state.options:
            print("Homing!")
            gcode += "$X\n" # unlock alarms so we can home Y before X
            gcode += "$HY\n" # home Y
            gcode += "$HX\n" # home X
        if dualsense.state.circle:
            # set current x,y as center point for future circles or spirals
            arc_center = Point(x, y)
            #print(x, y, arc_center.x, arc_center.y)
        elif dualsense.state.R1:
            points = arc(x, y, arc_center, direction=CW, spiral=True, spiral_growth=0.1) # Tight cw spiral
        elif dualsense.state.L1:
            points = arc(x, y, arc_center, direction=CCW, spiral=True, spiral_growth=0.1) # Tight ccw spiral 
        elif dualsense.state.R2:
            points = arc(x, y, arc_center, direction=CW, spiral=True, spiral_growth=0.3) # Loose cw spiral
        elif dualsense.state.L2:
            points = arc(x, y, arc_center, direction=CCW, spiral=True, spiral_growth=0.3) # Loose ccw spiral
        elif dualsense.state.R3:
            points = arc(x, y, arc_center, direction=CW)
            #print(x, y, arc_center.x, arc_center.y, points) 
        elif dualsense.state.L3:
            points = arc(x, y, arc_center, direction=CCW)
            #print(x, y, arc_center.x, arc_center.y, points) 
        elif dualsense.state.DpadRight:
            #Wipe right
            gcode = f"G1 F{WIPE_SPEED}\n" # set speed
            points = wipeRight(x, y)
            gcode_post = f"G1 F{SPEED}\n" # reset speed
        else:
            if dualsense.state.LX > 90:
                y -= rate
                points = [Point(x, y)]
            if dualsense.state.LX < -90:
                y += rate
                points = [Point(x, y)]
            if dualsense.state.RY > 90:
                x -= rate
                points = [Point(x, y)]
            if dualsense.state.RY < -90:
                x += rate
                points = [Point(x, y)]

        # adjust points for table limits and generate gcode
        for point in points:
            point.x = min(point.x, X_MAX)
            point.x = max(point.x, X_MIN)
            point.y = min(point.y, Y_MAX)
            point.y = max(point.y, Y_MIN)

            #print(f'x: {point.x} y: {point.y}')
            gcode += f"G1 X{point.x:.0f} Y{point.y:.0f}\n"

        # set location to last point
        if points != []:
            x = points[-1].x
            y = points[-1].y

        gcode += gcode_post

        for line in gcode.split("\n"):
            if (line == ""):
                continue
            #print(line)
            writer.write(line + "\n")
            reply = await reader.read(128)
            #print('reply:', reply)


def wipeRight(x, y, num_lines=5):
    points = []

    for i in range(num_lines):
        y = y - 5
        points.append(Point(X_MIN, y))

        y = y - 5
        points.append(Point(X_MAX, y))

    return points


def arc(x, y, center, num_points=1, direction=CW, spiral=False, spiral_growth=0.1):
    radius = ((x - center.x)**2 + (y - center.y)**2)**0.5
    if direction == CW:
        arc_angle = math.atan2(x - center.x, y - center.y)
    else:
        arc_angle = math.atan2(y - center.y, x - center.x)

    points = []
    for i in range(num_points):
        if spiral:
            radius += spiral_growth

        angle = arc_angle + 0.1 * (i + 1)
        if (direction == CW):
            a = math.sin(angle)
            b = math.cos(angle)
        else:
            a = math.cos(angle)
            b = math.sin(angle)
        #a = math.sin(angle) if left else math.cos(angle)
        #b = math.cos(angle) if left else math.sin(angle)

        #print(angle, a, b, radius*a, radius*b)

        x1 = center.x + radius * a
        y1 = center.y + radius * b

        points.append(Point(x1, y1))
    return points

asyncio.run(main())

# close device
dualsense.close()
