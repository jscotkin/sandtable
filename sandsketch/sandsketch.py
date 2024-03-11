from pydualsense import *
import time
import asyncio, telnetlib3
import math
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int

TABLE_IP_ADDRESS = "192.168.1.55"
TABLE_PORT = 8080

CW = True # clockwise direction
CCW = False # counter clockwise direction

X_MIN = 5
X_MAX = 525

Y_MIN = 5
Y_MAX = 1280

SPEED = 2000
WIPE_SPEED = 4000


# create dualsense
dualsense = pydualsense()
# find device and initialize
dualsense.init()

async def send_gcode(gcode, reader, writer, gcodeFile, save_gcode = False):
    reply = ""
    for line in gcode.split("\n"):
        if (line == ""):
            continue
        if (save_gcode):
            gcodeFile.write(line + "\n")
        #print(line)
        writer.write(line + "\n")
        reply = await reader.read(128)
        #print('reply:', reply)
    
    return reply # last reply only


async def main():
    print("Welcome to SandSketch!")
    print("SandSketch requires a PC and a PlayStation 5 DualSense controller.")
    print("You should be facing the long side of your table (so Y=0 is to your right, and max Y to your left)")
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


    # Create filename with timestamp
    gcodeFilename = "sketch_" + time.strftime("%Y%m%d-%H%M%S") + ".gcode" 
    gcodeFile = open(gcodeFilename, "w")

    reader, writer = await telnetlib3.open_connection(TABLE_IP_ADDRESS, TABLE_PORT)
    reply = await reader.read(128) # read the GRBL header
    print('reply:', reply)

    gcode = f"?\n"
    writer.write(gcode)
    reply = await reader.read(128) # should show status and location
    print('reply:', reply)

    x = float(reply.split('|')[1].split(':')[1].split(',')[0]) # get current xpos
    y = float(reply.split('|')[1].split(':')[1].split(',')[1]) # get current ypos

    reply = await reader.read(128) # should be "ok"

    rate = 2

    wipe_lower_left = Point(X_MIN, 600)
    wipe_upper_right = Point(X_MAX, 500)

    arc_center = Point(x, y)

    await send_gcode(f"G1 F{SPEED}\n", reader, writer, gcodeFile, save_gcode=False) # set speed

    # read controller state until PlayStation button is pressed
    while not dualsense.state.ps:
        time.sleep(0.06)
        points = []
        gcode = ""
        gcode_post = ""
        save_gcode = True

        if dualsense.state.options:
            print("Homing!")
            gcode += "$X\n" # unlock alarms so we can home Y before X
            gcode += "$HY\n" # home Y
            gcode += "$HX\n" # home X
            save_gcode = False
        elif dualsense.state.circle:
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
            print(x, y, arc_center.x, arc_center.y, points) 
        elif dualsense.state.L3:
            points = arc(x, y, arc_center, direction=CCW)
            print(x, y, arc_center.x, arc_center.y, points) 
        elif dualsense.state.DpadLeft:
            wipe_lower_left.y = y
            print(wipe_lower_left.y)
        elif dualsense.state.DpadRight:
            wipe_upper_right.y = y
            print(wipe_upper_right.y)
        elif dualsense.state.share:
            #Wipe right
            print(wipe_lower_left.x, wipe_lower_left.y, wipe_upper_right.x, wipe_upper_right.y)
            gcode = f"G1 F{WIPE_SPEED}\n" # set speed
            points = wipeRight(wipe_lower_left, wipe_upper_right)
            gcode_post = f"G1 F{SPEED}\n" # reset speed
            save_gcode = False
            print("Wiping")
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

        await send_gcode(gcode, reader, writer, gcodeFile, save_gcode)
#        for line in gcode.split("\n"):
#           if (line == ""):
#               continue
#            #print(line)
#            writer.write(line + "\n")
#            reply = await reader.read(128)
#            #print('reply:', reply)

    gcodeFile.close()


def wipeRight(wipe_lower_left, wipe_upper_right, num_lines=8, gap=6):
    points = []
    points.append(wipe_lower_left)

    x, y = (wipe_lower_left.x, wipe_lower_left.y)
    x_end, y_end = (wipe_upper_right.x, wipe_upper_right.y)
    print(x, y, x_end, y_end)

    while(y > y_end):
        y = y - gap
        points.append(Point(X_MIN, y))
        points.append(Point(X_MAX, y))

        y = y - gap
        points.append(Point(X_MAX, y))
        points.append(Point(X_MIN, y))

    print(points)
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

        #angle = arc_angle + 0.1 * (i + 1)

        # 1/radius scales the radians down as the radius gets longer so we don't buffer too inputs
        # We add 1 to the radius so we can't divide by 0.
        arc_change = (1/(radius+1) * 3) 
        angle = arc_angle + arc_change * 3 * (i + 1) 
        if (direction == CW):
            a = math.sin(angle)
            b = math.cos(angle)
        else:
            a = math.cos(angle)
            b = math.sin(angle)

        #print(angle, a, b, radius*a, radius*b)

        x1 = center.x + radius * a
        y1 = center.y + radius * b

        points.append(Point(x1, y1))
    return points

asyncio.run(main())

# close device
dualsense.close()
