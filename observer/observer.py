import hardware
import utility
import input
import calibration
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2
import numpy
import random
import keyboard
import os
import sys

import config

configs = [config.Config() for x in range(10)]
config.process_configs(configs)
cfg = configs[0]

res = (320, 240)
calib = [0, 0]
focus = [0, 320, 0, 240]

stream = None
stream_img = None

synchro = None


# camera settings (don't use auto mode...)
# iso, brightness and contrast have to be adjusted for lens - monitor - environment conditions

camera = PiCamera()
camera.resolution = res
camera.framerate = 60
camera.awb_mode = 'off'
camera.awb_gains = (3.625, 1.40)
camera.iso = cfg.iso
camera.brightness = cfg.brightness
camera.contrast = cfg.contrast
camera.analog_gain
camera.shutter_speed = 16667  # 1 / (t / s * 10^6)
raw_capture = PiRGBArray(camera, size=(res))

# calculate cut boundaries based on the active config


def focus_area():
    global focus
    focus = (int(res[0] / 2 - cfg.obs_x / 2) + calib[0],
             int(res[0] / 2 + cfg.obs_x / 2) + calib[0],
             int(res[1] / 2 - cfg.obs_y / 2) + calib[1],
             int(res[1] / 2 + cfg.obs_y / 2) + calib[1])

# check if flashed
# only required for absolute difference of frames + (this method is not reliable)


def flashed(img):
    col = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    sat = col[:, :, 1].mean()
    bri = col[:, :, 2].mean() / 2.55
    if sat < 20 and bri > 99.0:
        return True
    else:
        return False

# check if in scope, based on color detection at the crosshair middle
# checks for config-defined color in the vertical and horizontal second third of the focus area
# uses secondary LED as an indicator for its state


def crosshair_indicator(img):
    if cfg.marker_check == False:
        return True
    x_1 = int(cfg.obs_x / 3)
    x_2 = int(cfg.obs_x * 2 / 3)
    y_1 = int(cfg.obs_y / 3)
    y_2 = int(cfg.obs_y * 2 / 3)
    img = img[x_1:x_2, y_1:y_2]
    col = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    low = numpy.array(
        [cfg.col_marker_hue_low, cfg.col_marker_sat_low, cfg.col_marker_bri_low])
    high = numpy.array(
        [cfg.col_marker_hue_high, cfg.col_marker_sat_high, cfg.col_marker_bri_high])
    mask = cv2.inRange(col, low, high)
    pxsum_marker = int(sum(cv2.sumElems(mask / 2.550))) / \
        ((x_2 - x_1) * (y_2 - y_1))
    if pxsum_marker > 1:
        hardware.gpio.led_red(False)
        return True
    else:
        hardware.gpio.led_red(True)
        return False

# keyboard input / control


def keypress(data):

    global cfg
    global calib
    global log_dir

    # calibration, 'enter' + numbers on numpad arrow keys
    # (num lock doesn't work for me and I'm only using a numpad for the Raspberry Pi)
    # shifting the focus area can be viewed in the stream
    # 'enter' + '5' resets the calibration
    if keyboard.is_pressed('enter'):
        time.sleep(0.02)
        if keyboard.is_pressed('4'):
            calib[0] -= 1
        elif keyboard.is_pressed('6'):
            calib[0] += 1
        elif keyboard.is_pressed('8'):
            calib[1] -= 1
        elif keyboard.is_pressed('2'):
            calib[1] += 1
        elif keyboard.is_pressed('5'):
            calib = (0, 0)
        return True

    # config selection
    for key in range(0, 9):
        if keyboard.is_pressed(str(key)):
            cfg = configs[key]
            print('active config changed: [' + str(key) + '] ' + cfg.name)
            time.sleep(2.0)
            return True

    # shut down the program
    if keyboard.is_pressed('+'):
        print("observer shutting down")
        for x in range(0, 10):
            hardware.gpio.led_green(x % 2 == 0)
            hardware.gpio.led_red(x % 2 == 0)
            time.sleep(0.05)
        sys.exit(0)

    # save last positive for inspection
    if keyboard.is_pressed('-'):
        if os.path.isdir("./data/" + str(data.log_dir)):
            os.rename("./data/" + str(data.log_dir), "data/" +
                      str(data.log_dir) + "_inspection")
            print("last positive marked for inspection")
            time.sleep(1.0)

    # print(keyboard.read_key())
    return False


def observe_difference():

    global stream_img

    # has to be initialized for the first run
    crop_focus_prev = numpy.zeros([cfg.obs_x, cfg.obs_y, 3], dtype=numpy.uint8)
    active = False
    t_open = time.time()

    # data object to save frames for analysis + labeling of the streamed frames
    # clears the frames from the last session except the ones marked for inspection
    data = utility.Data()
    data.clear_data()

    # to count iterations
    run = 0

    # calculate focus area based on the active config
    focus_area()

    for frame in camera.capture_continuous(raw_capture, format="bgr", use_video_port=True):

        # randomize relay opening and break duration
        cfg.randomizer()
        utility.run_benchmark(cfg)
        run += 1

        img = frame.array
        crop_focus = img[focus[2]:focus[3], focus[0]:focus[1]]

        raw_capture.truncate(0)

        # sync keyboard input, break if active config is changed
        if keypress(data):
            break

        # the absolute difference enables positives for changes in brightness from dark to bright
        # - most games tested have bright backgrounds and dark targets though
        # using just the subtraction gives a little fewer false positives
        # diff_crop = cv2.absdiff(img_crop, prev_img_crop) # for all changes

        # only for changes from bright to dark
        diff_crop = cv2.subtract(crop_focus_prev, crop_focus)
        thresh_crop = cv2.threshold(diff_crop, 30, 255, cv2.THRESH_BINARY)[1]
        pxsum_crop = int(sum(cv2.sumElems(thresh_crop / 2.55))) / \
            (3.0 * (focus[1] - focus[0]) * (focus[3] - focus[2]))

        # check if key is pressed
        synchro.sync_observer(cfg)

        # draw focus area
        utility.label_frame(img, pxsum_crop, focus, calib, synchro.active)

        # pass the current frame into a global variable (by reference) that is used in the streaming thread
        stream_img[0] = img

        # append frame to temporary stack
        data.update_frames(img)
        data.update_diffs(thresh_crop)
        if run == 0:
            data.save_data()

        # close the relay
        if active and time.time() - t_open > cfg.duration_active:
            time.sleep(random.randint(1, 17) / 1000)
            hardware.gpio.relay(False)
            print("relay closed after " +
                  str(round((time.time() - t_open) * 1000, 1)) + " ms")
            active = False

        # open the relay
        if pxsum_crop >= cfg.sens_diff and active == False and synchro.active and time.time() - t_open > cfg.duration_break and not flashed(crop_focus):
            hardware.gpio.relay(True)
            print("relay opened")
            if cfg.tap_mode == 'charge':
                synchro.active = False
            t_open = time.time()
            active = True
            run = -5

        if active:
            hardware.gpio.led_green(False)

        crop_focus_prev = crop_focus


def observe_color():

    global stream_img
    active = False
    t_open = time.time()

    # data required for consecutive mode
    cons_data = [False] * 3

    # data object to save frames for analysis + labeling of the streamed frames
    # clears the frames from the last session except the ones marked for inspection
    data = utility.Data()
    data.clear_data()

    # to count iterations
    run = 0

    # calculate focus area based on the active config
    focus_area()

    for frame in camera.capture_continuous(raw_capture, format="bgr", use_video_port=True):

        # randomize relay opening and break duration
        cfg.randomizer()
        utility.run_benchmark(cfg)
        run += 1

        img = frame.array
        crop_focus = img[focus[2]:focus[3], focus[0]:focus[1]]

        raw_capture.truncate(0)

        # sync keyboard input, break if active config is changed
        if keypress(data):
            break

        col = cv2.cvtColor(crop_focus, cv2.COLOR_BGR2HSV)
        low = numpy.array([cfg.col_hue_low, cfg.col_sat_low, cfg.col_bri_low])
        high = numpy.array(
            [cfg.col_hue_high, cfg.col_sat_high, cfg.col_bri_high])
        mask = cv2.inRange(col, low, high)
        pxsum_col = int(sum(cv2.sumElems(mask / 2.550))) / \
            ((focus[1] - focus[0]) * (focus[3] - focus[2]))

        # check if key is pressed
        synchro.sync_observer(cfg)

        # draw focus area
        utility.label_frame(img, pxsum_col, focus, calib, synchro.active)

        # pass the current frame into a global variable (by reference) that is used in the streaming thread
        stream_img[0] = img

        # append frame to temporary stack
        data.update_frames(img)
        if run == 0:
            data.save_data()

        # close the relay
        if active and time.time() - t_open > cfg.duration_active:
            time.sleep(random.randint(1, 17) / 1000)
            hardware.gpio.relay(False)
            print("relay closed after " +
                  str(round((time.time() - t_open) * 1000, 1)) + " ms")
            active = False

        # save last results in a buffer
        consecutive_positive = True
        if cfg.consecutive:
            cons_data.append(pxsum_col >= cfg.sens_color)
            cons_data.pop(0)
            consecutive_positive = not False in cons_data

        # check secondary activation condition
        still = crosshair_indicator(crop_focus)

        # open the relay
        if (synchro.active and pxsum_col >= cfg.sens_color and
                active == False and time.time() - t_open > cfg.duration_break and
                still and consecutive_positive):
            time.sleep(cfg.delay / 1000)
            hardware.gpio.relay(True)
            print("relay opened")
            if cfg.tap_mode == 'charge':
                synchro.active = False
            t_open = time.time()
            active = True
            run = -5

        if active:
            hardware.gpio.led_green(False)


def main():

    # keyboard library requires root permissions
    if os.geteuid() != 0:
        print("try again with root privileges")
        time.sleep(2)
        print("observer shutting down")
        sys.exit(0)

    # blinking LEDs as startup sign
    for x in range(0, 2):
        hardware.gpio.led_green(x % 2 == 0)
        hardware.gpio.led_red(x % 2 == 0)
        time.sleep(0.4)

    print("observer running")

    # set up the stream to calibrate
    global stream_img, stream
    stream_img = [numpy.zeros((*res, 4), numpy.uint16) + [0, 0, 0, 128]]
    stream = calibration.Stream(stream_img)
    stream.run_stream()

    # input manager
    global synchro
    synchro = input.Synchro()

    # use socket based input instead of a GPIO button
    if cfg.remote_keyboard:
        synchro.start_remote_keyboard()

    while True:
        if cfg.mode == "color":
            observe_color()
        elif cfg.mode == "difference":
            observe_difference()


if __name__ == "__main__":
    main()
