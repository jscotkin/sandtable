from pydualsense import *
import asyncio, telnetlib3
import sys

TABLE_IP_ADDRESS = "192.168.1.55"
TABLE_PORT = 8080

SPEED = 2000

async def main(gcodeFile):
    print("Welcome to Sandsender!")
    print("This program takes a gcode file and sends it to your GRBL sand table over the network.")

    if (len(sys.argv) < 2):
        print("Please specify a gcode file.")
        return

    gcode = ""
    gcode += f"G1 F{SPEED}\n" # set speed

    gcodeFile = open(sys.argv[1], "r")
    gcode += gcodeFile.read()
    gcodeFile.close()

    reader, writer = await telnetlib3.open_connection(TABLE_IP_ADDRESS, TABLE_PORT)
    reply = await reader.read(128) # read the GRBL header
    print('reply:', reply)

    for line in gcode.split("\n"):
        if (line == ""):
            continue
        #print(line)
        writer.write(line + "\n")
        reply = await reader.read(128)
        #print('reply:', reply)

asyncio.run(main())