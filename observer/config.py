import configparser
import time
import random

cp = configparser.ConfigParser(
    converters={'list': lambda x: [i.strip() for i in x.split(',')]})
cp.read(['config.cfg'])


class Config:

    def __init__(self):
        pass

    name = "DEFAULT"

    iso = cp.getint("CAMERA", "iso")
    brightness = cp.getint("CAMERA", "brightness")
    contrast = cp.getint("CAMERA", "contrast")

    # focus area around the crosshair
    obs_x = cp.getint("PROCESSING", "obs_x")
    obs_y = cp.getint("PROCESSING", "obs_y")

    # performance and analysis
    benchmark = cp.getboolean("DEBUG", "benchmark")
    image_logger = cp.getboolean("DEBUG", "image_logger")

    # sensitivity in percent
    sens_diff = cp.getfloat("PROCESSING", "sens_diff")
    sens_color = cp.getfloat("PROCESSING", "sens_color")

    # color tracking for color mode
    col_hue_low = cp.getint("PROCESSING", "col_hue_low") / 2
    col_hue_high = cp.getint("PROCESSING", "col_hue_high") / 2
    col_sat_low = int(cp.getfloat("PROCESSING", "col_sat_low") * 255.0)
    col_sat_high = int(cp.getfloat("PROCESSING", "col_sat_high") * 255.0)
    col_bri_low = int(cp.getfloat("PROCESSING", "col_bri_low") * 255.0)
    col_bri_high = int(cp.getfloat("PROCESSING", "col_bri_high") * 255.0)

    # marker color (scoped-in marker color)
    col_marker_hue_low = cp.getint("PROCESSING", "col_marker_hue_low") / 2
    col_marker_hue_high = cp.getint("PROCESSING", "col_marker_hue_high") / 2
    col_marker_sat_low = int(cp.getfloat(
        "PROCESSING", "col_marker_sat_low") * 255.0)
    col_marker_sat_high = int(cp.getfloat(
        "PROCESSING", "col_marker_sat_high") * 255.0)
    col_marker_bri_low = int(cp.getfloat(
        "PROCESSING", "col_marker_bri_low") * 255.0)
    col_marker_bri_high = int(cp.getfloat(
        "PROCESSING", "col_marker_bri_high") * 255.0)

    remote_keyboard = cp.getboolean("CONTROL", "remote_keyboard")

    mode = cp.get("GAMEPLAY", "mode")
    delay = cp.getint("GAMEPLAY", "delay")
    tap_mode = cp.get("GAMEPLAY", "tap_mode")
    marker_check = cp.getboolean("GAMEPLAY", "marker_check")
    consecutive = cp.getboolean("GAMEPLAY", "consecutive")

    duration_active = cp.getint("GAMEPLAY", "duration_active") / 1000.0
    duration_break = cp.getint("GAMEPLAY", "duration_break") / 1000.0
    duration_active_tmp = 0
    duration_breake_tmp = 0

    tap = cp.getboolean("GAMEPLAY", "tap")
    activation_delay = cp.getint("GAMEPLAY", "activation_delay")
    tap_led_time_on = cp.getint("GAMEPLAY", "tap_led_time_on")
    tap_led_time_off = cp.getint("GAMEPLAY", "tap_led_time_off")

    # randomize mouse click and pause time
    # mean values can be set in config
    # using uniform distribution
    def randomizer(self):
        if time.time() * 1000 % 1000 < 25:
            self.duration_active_tmp = self.duration_active + \
                random.randint(-20, 20) / 1000
            self.duration_break_tmp = self.duration_break + \
                random.randint(-50, 50) / 1000


def process_configs(configs):

    NUM = [cp.getlist("KEYS", "NUM_0"), cp.getlist("KEYS", "NUM_1"), cp.getlist("KEYS", "NUM_2"),
           cp.getlist("KEYS", "NUM_3"), cp.getlist(
               "KEYS", "NUM_4"), cp.getlist("KEYS", "NUM_5"),
           cp.getlist("KEYS", "NUM_6"), cp.getlist(
               "KEYS", "NUM_7"), cp.getlist("KEYS", "NUM_8"),
           cp.getlist("KEYS", "NUM_9")]

    for idx, N in enumerate(NUM):
        configs[idx].name = N[0]
        i = 1
        while i < len(N):
            if N[i] == 'mode':
                configs[idx].mode = N[i + 1]
            elif N[i] == 'obs_x':
                configs[idx].obs_x = int(N[i + 1])
            elif N[i] == 'obs_y':
                configs[idx].obs_y = int(N[i + 1])
            elif N[i] == 'sens_diff':
                configs[idx].sens_diff = float(N[i + 1])
            elif N[i] == 'sens_color':
                configs[idx].sens_diff = float(N[i + 1])
            elif N[i] == 'duration_active':
                configs[idx].duration_active = int(N[i + 1]) / 1000.0
            elif N[i] == 'duration_break':
                configs[idx].duration_break = int(N[i + 1]) / 1000.0
            elif N[i] == 'activation_delay':
                configs[idx].activation_delay = int(N[i + 1])
            elif N[i] == 'tap':
                configs[idx].tap = bool(int(N[i + 1]))
            elif N[i] == 'tap_mode':
                configs[idx].tap_mode = N[i + 1]
            elif N[i] == 'marker_check':
                configs[idx].marker_check = bool(int(N[i + 1]))
            i += 2
