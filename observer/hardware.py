import RPi.GPIO as GPIO

# ----------------------------------------------------------------------------------------------------
# GPIO SETUP AND FUNCTIONS
# ----------------------------------------------------------------------------------------------------

ID_LED_GREEN = 36
ID_LED_RED = 32
ID_RELAY = 18
ID_KEY = 10

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(ID_LED_GREEN, GPIO.OUT)
GPIO.setup(ID_LED_RED, GPIO.OUT)
GPIO.setup(ID_KEY, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(ID_RELAY, GPIO.OUT)


class gpio:
    @staticmethod
    def led_green(state):
        if (state == False):
            GPIO.output(ID_LED_GREEN, GPIO.LOW)
        else:
            GPIO.output(ID_LED_GREEN, GPIO.HIGH)

    @staticmethod
    def led_red(state):
        if (state == False):
            GPIO.output(ID_LED_RED, GPIO.LOW)
        else:
            GPIO.output(ID_LED_RED, GPIO.HIGH)

    @staticmethod
    def relay(state):
        if (state == False):
            GPIO.output(ID_RELAY, GPIO.LOW)
        else:
            GPIO.output(ID_RELAY, GPIO.HIGH)

    @staticmethod
    def sync_key():
        return GPIO.input(ID_KEY) == GPIO.HIGH
