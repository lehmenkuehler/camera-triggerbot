import time
import numpy as np
import os
import cv2
import shutil

global cfg, ACT_CFG, focus, calib

first_run = True
benchmarks = []
time_last_loop = 0

# print benchmarks every 1000 frames
# for 60 fps the minimum value is 16.667 ms


def run_benchmark(cfg):
    if not cfg.benchmark:
        return
    global first_run
    global benchmarks
    global time_last_loop
    t = time.time() * 1000.0
    d_t = round(t - time_last_loop, 0)
    if first_run != True:
        benchmarks.append(d_t)
    if len(benchmarks) == 1000:
        print("1000f benchmark:", np.average(benchmarks), "ms")
        benchmarks = []
    time_last_loop = t
    first_run = False

# allows to log what the camera sees shortly before and after the relay is opened (10 frames)
# to analyze false positives or adjust sensitivity etc.


class Data:
    frames = []
    diffs = []
    log_dir = None

    def __init__(self):
        self.frames = []
        self.diffs = []
        if not os.path.exists('./data'):
            os.makedirs('./data')

    def update_diffs(self, img):
        self.diffs.append(img)
        if len(self.diffs) > 10:
            self.diffs.pop(0)

    def update_frames(self, img):
        self.frames.append(img)
        if len(self.frames) > 10:
            self.frames.pop(0)

    # save frame buffer for analysis
    # called upon key press
    def save_data(self):
        t = str(int(time.time() * 1000))
        self.log_dir = t
        os.makedirs('./data/' + t)
        n = 0
        for frame in self.frames:
            if len(self.diffs) > 0:
                diff = cv2.resize(self.diffs[n], (320, 240))
                concat = cv2.hconcat([frame, diff])
                cv2.imwrite('./data/' + t + '/concat_' +
                            t + '_' + str(n) + '.jpg', concat)
            else:
                cv2.imwrite('./data/' + t + '/img_' + t +
                            '_' + str(n) + '.jpg', frame)
            n += 1

    # delete frame log from previous session unless directory is marked for analysis
    def clear_data(self):
        for root, dirs, files in os.walk("./data/"):
            for name in dirs:
                if not name.endswith(("_inspection")):
                    shutil.rmtree(os.path.join(root, name), ignore_errors=True)

# draw focus area and center (including calibration)
# draw pxsum


def label_frame(img, pxsum, focus, calib, active):
    cv2.putText(img, "px/% : " + str(round(pxsum, 1)), (20, 220),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.line(img, (focus[0], focus[2]),
             (focus[0], focus[3]), (0, 255, 0), thickness=1)
    cv2.line(img, (focus[1], focus[2]),
             (focus[1], focus[3]), (0, 255, 0), thickness=1)
    cv2.line(img, (focus[0], focus[2]),
             (focus[1], focus[2]), (0, 255, 0), thickness=1)
    cv2.line(img, (focus[0], focus[3]),
             (focus[1], focus[3]), (0, 255, 0), thickness=1)
    cv2.rectangle(img, pt1=(158 + calib[0], 118 + calib[1]), pt2=(
        162 + calib[0], 122 + calib[1]), color=(0, 0, 255), thickness=-1)
    if active:
        col = (0, 255, 0)
    else:
        col = (128, 128, 128)
    cv2.rectangle(img, pt1=(4, 4), pt2=(24, 24), color=col, thickness=-1)
