import cv2
import numpy as np
from vidgear.gears import CamGear
import re
from scipy.signal import find_peaks 
from os import getcwd

source = input("Video link: ")
path = input("Path to save tab to (leave blank to save to current folder): ")
start_time = input("Time in seconds when tab appears (leave blank for default of 2 seconds): ")

if path == "":
     path = getcwd()
if start_time == "":
     start_time = 2
else:
     start_time = float(start_time)

stream = CamGear(
    source=source,
    stream_mode=True,
    time_delay=1,
    logging=True
).start()

fps = stream.ytv_metadata["fps"]
cur_frame = -start_time * fps # Add buffer window of 2 seconds in case of fade in
frames = []
change_frames = []
largest_rect = []
last_frame = []
diffs = []
limit = 200

while True:
    cur_frame += 1
    frame = stream.read()
    if frame is None:
            break
    if cur_frame >= 0 and cur_frame % (fps // 3) == 0: # Only check every half second to save time and computation
        if cur_frame == 0: # Find sheet position
            bordered = cv2.copyMakeBorder(frame, 2, 2, 2, 2, cv2.BORDER_CONSTANT) # Add border to account for cases where tab is on sides of video
            gray = cv2.cvtColor(bordered, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, limit, 255, cv2.THRESH_BINARY)[1]

            edged = cv2.Canny(thresh, 80, 200)
            
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(4,4))
            dilated = cv2.dilate(edged, kernel)
            
            contours, hierarchy = cv2.findContours(dilated, 
                cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            
            contours = sorted(contours, key=cv2.contourArea, reverse=True)

            bounding_rects = []
            for contour in contours:
                bounding_rects.append(cv2.boundingRect(contour))

            largest_rect = max(bounding_rects, key=lambda x: x[2])

            rect_crop = thresh[largest_rect[1]:largest_rect[1] + largest_rect[3], largest_rect[0]:largest_rect[0] + largest_rect[2]]

            avg_color_per_row = np.average(thresh, axis=0)
            avg_color = np.average(avg_color_per_row, axis=0)
            if avg_color < 30: # Check if sheet is white on black, if so make system more sensitive to white
                limit = 170
                thresh = cv2.threshold(gray, limit, 255, cv2.THRESH_BINARY)[1]

                edged = cv2.Canny(thresh, 80, 200)
                
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(6,6))
                dilated = cv2.dilate(edged, kernel)
                contours, hierarchy = cv2.findContours(dilated, 
                    cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

                contours = sorted(contours, key=cv2.contourArea, reverse=True)

                bounding_rects = []
                for contour in contours:
                    bounding_rects.append(cv2.boundingRect(contour))

                largest_rect = max(bounding_rects, key=lambda x: x[2])

                rect_crop = thresh[largest_rect[1]:largest_rect[1] + largest_rect[3], largest_rect[0]:largest_rect[0] + largest_rect[2]]

            last_frame = rect_crop
            frames.append(frame[largest_rect[1]:largest_rect[1] + largest_rect[3], largest_rect[0]:largest_rect[0] + largest_rect[2]])
        else:
            bordered = cv2.copyMakeBorder(frame, 2, 2, 2, 2, cv2.BORDER_CONSTANT) #Add border to account for cases where tab is on sides of video
            gray = cv2.cvtColor(bordered, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, limit, 255, cv2.THRESH_BINARY)[1]
            rect_crop = thresh[largest_rect[1]:largest_rect[1] + largest_rect[3], largest_rect[0]:largest_rect[0] + largest_rect[2]]
            diff = cv2.absdiff(last_frame, rect_crop)
            diffs.append(np.sum(diff > 0))
            last_frame = rect_crop
            frames.append(frame[largest_rect[1]:largest_rect[1] + largest_rect[3], largest_rect[0]:largest_rect[0] + largest_rect[2]])
            
diff = cv2.absdiff(last_frame, rect_crop)
diffs.append(np.sum(diff > 0))

min_diff = min(diffs)
avg = (max(diffs) - min_diff) / 2
peaks, props = find_peaks(diffs, distance=1, height=avg) 
all_peaks, all_props = find_peaks(diffs, distance=1, height=0)
peak_heights = sorted(all_props['peak_heights'], reverse=True)
ind = 0
while len(peaks) < 3: # Account huge spikes in change that are typically from fade out
    ind += 1
    avg = (peak_heights[ind] - min_diff) / 2
    peaks, props = find_peaks(diffs, distance=1, height=avg)

for peak in peaks:
     change_frames.append(frames[peak - 1]) # Add slight buffer to prevent smudge frames

result = change_frames[0]
for frame in change_frames[1:]:
    result = cv2.vconcat([result, frame])
filename = path + "\\" + re.sub('[^A-Za-z0-9]+', '', stream.ytv_metadata["title"]) + ".jpg"
cv2.imwrite(filename, result)
print("Written to " + filename)

stream.stop()