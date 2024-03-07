import numpy as np
import cv2 as cv
from collections import namedtuple
from matplotlib import pyplot as plt
import asyncio, telnetlib3
import math

# return contours based on closest to the origin
def get_contours_in_distance_order(image):
    contours, hierarchy = cv.findContours(image, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)

    width = image.shape[1]

    cnt_distance = []
    for c in contours:
        x,y,w,h=cv.boundingRect(c)
        x = width - x # frame transform to flip x to lower left instead of lower right
        cnt_distance.append(math.sqrt(x**2+y**2))

    cnt_distance = np.array(cnt_distance)

    # Sort in ascending order
    sorted_contours = [contours[i] for i in np.argsort(cnt_distance)]
    return sorted_contours

def get_contours_in_size_order(image):
    contours, hierarchy = cv.findContours(image, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)

    cnt_area = []
    for c in contours:
        cnt_area.append(cv.contourArea(c))

    cnt_area = np.array(cnt_area)
    # Sort in descending order
    sorted_contours = [contours[i] for i in np.argsort(cnt_area)[::-1]]
    return sorted_contours


def fill_contour(image, contour):
    black = np.zeros((image.shape[0], image.shape[1]), np.uint8)
    mask = cv.drawContours(black,[contour],0,255, -1)
    return mask

# pass in index of contour to fill, 0 for largest
def get_filled_contour(image, index):
    contour = get_contours_in_size_order(image)[index]
    return fill_contour(image, contour)

Point = namedtuple('Point', 'x y')
Box = namedtuple('Box', 'x y w h')

plotrows = 2
plotcols = 7
plotindex = 1

plt.figure(figsize=(20,10))
img = cv.imread('img3.jpg')
plt.subplot(plotrows,plotcols,plotindex),plt.imshow(img)
plt.title('Original'), plt.xticks([]), plt.yticks([])
plotindex += 1

img_gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
plt.subplot(plotrows,plotcols,plotindex),plt.imshow(img_gray, cmap='gray')
plt.title('Gray '), plt.xticks([]), plt.yticks([])
plotindex += 1

th = cv.threshold(img_gray, 75, 255, cv.THRESH_BINARY_INV)[1]
plt.subplot(plotrows,plotcols,plotindex),plt.imshow(th, cmap='gray')
plt.title('TH '), plt.xticks([]), plt.yticks([])
plotindex += 1

table = get_filled_contour(th, 0)
plt.subplot(plotrows,plotcols,plotindex),plt.imshow(table, cmap='gray')
plt.title('table '), plt.xticks([]), plt.yticks([])
plotindex += 1

sand_dirty = cv.subtract(table,th)
plt.subplot(plotrows,plotcols,plotindex),plt.imshow(sand_dirty, cmap='gray')
plt.title('sand_dirty '), plt.xticks([]), plt.yticks([])
plotindex += 1

sand = get_filled_contour(sand_dirty, 0)
plt.subplot(plotrows,plotcols,plotindex), plt.imshow(sand, cmap='gray')
plt.title('sand '), plt.xticks([]), plt.yticks([])
plotindex += 1

sand_contours = cv.findContours(sand, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
sand_contour = sand_contours[0][0]
print(cv.contourArea(sand_contour))

sand_contour_image = img.copy()

#cv.drawContours(sand_contour_image, [sand_contour], -1, (255, 0, 0), 12)
x,y,w,h = cv.boundingRect(sand_contour)
cv.rectangle(sand_contour_image, (x, y), (x+w, y+h), (255, 0, 0), 12)
sand_box = Box(x,y,w,h)

sand_table_drawable_width = 550 # hardcoded to my sand table
sand_table_drawable_height = 1280 # hardcoded to my sand table

sand_table_visible_width = 550 # hardcoded to my sand table
sand_table_visible_height = 1360 # hardcoded to my sand table

sand_x_scale_factor = w / sand_table_visible_width
sand_y_scale_factor = h / sand_table_visible_height

print(sand_box)

plt.subplot(plotrows,plotcols,plotindex), plt.imshow(sand_contour_image)
plt.title('sand contour'), plt.xticks([]), plt.yticks([])
plotindex += 1

# Now find what's on the table

objects_only_inv = cv.bitwise_xor(sand_dirty, 255, mask = sand)
plt.subplot(plotrows,plotcols,plotindex), plt.imshow(objects_only_inv, cmap='gray')
plt.title('objects_only_inv '), plt.xticks([]), plt.yticks([])
plotindex += 1

xbuffer = 20
ybuffer = 20

gcode = "G1 F1500\n"
gcode += "\n"

result2 = img.copy()
plotindex = 9 
for contour in get_contours_in_distance_order(objects_only_inv):
    area = cv.contourArea(contour)
    print(area)
    if area < 30000:
        continue
    cv.drawContours(result2, [contour], -1, (255, 0, 0), 12)
    
    x,y,w,h = cv.boundingRect(contour)
    print(x,y,w,h)
    cv.rectangle(result2, (x, y), (x+w, y+h), (255, 0, 0), 12)

    # left and right look backwards but are correct given the frame transformation to gcode coords
    right = (x - sand_box.x)/sand_x_scale_factor
    right = sand_table_visible_width - right # transform into gcode coordinates
    right = right + xbuffer
    right = min(right, sand_table_drawable_width)

    left = (x + w - sand_box.x)/sand_x_scale_factor
    left = sand_table_visible_width - left # transform into gcode coordinates
    left = left - xbuffer
    left = max(left, 0)


    lower = max((y - sand_box.y)/sand_y_scale_factor - ybuffer, 0)
    upper = min((y+h - sand_box.y)/sand_y_scale_factor + ybuffer, sand_table_drawable_height)

    gcode += f"G1 X{left:.0f} Y{lower:.0f}\n"
    gcode += f"G1 X{right:.0f} Y{lower:.0f}\n"
    gcode += f"G1 X{right:.0f} Y{upper:.0f}\n"
    gcode += f"G1 X{left:.0f} Y{upper:.0f}\n"
    gcode += f"G1 X{left:.0f} Y{lower:.0f}\n"

    # repeat these two to end on the upper right to minimize breaking lines
    gcode += f"G1 X{right:.0f} Y{lower:.0f}\n"
    gcode += f"G1 X{right:.0f} Y{upper:.0f}\n"

    mask = fill_contour(objects_only_inv, contour)

    plt.subplot(plotrows,plotcols,plotindex), plt.imshow(mask, cmap='gray')
    plt.title('object '), plt.xticks([]), plt.yticks([])
    plotindex += 1


plt.subplot(plotrows,plotcols,plotindex), plt.imshow(result2)
plt.title('objects '), plt.xticks([]), plt.yticks([])
plotindex += 1

print(gcode)


plt.show()

#exit()

async def send_gcode_to_table(gcode):
  reader, writer = await telnetlib3.open_connection("192.168.1.55", 8080)
  reply = await reader.read(128) # read the GRBL header
  for line in gcode.split("\n"):
    print(line)
    writer.write(line + "\n")
    reply = await reader.read(128)
    print('reply:', reply)

asyncio.run(send_gcode_to_table(gcode))
