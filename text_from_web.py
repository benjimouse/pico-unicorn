import json
import time
import network
import urequests
from galactic import GalacticUnicorn
from picographics import PicoGraphics, DISPLAY_GALACTIC_UNICORN as DISPLAY

# create graphics surface for drawing
graphics = PicoGraphics(DISPLAY)
gu = GalacticUnicorn()
width = GalacticUnicorn.WIDTH
height = GalacticUnicorn.HEIGHT

# state constants
STATE_PRE_SCROLL = 0
STATE_SCROLLING = 1
STATE_POST_SCROLL = 2

# In the left-upper corner
# blink a 2x2 square
# to indicate:
# WiFi Connected:       green_
# WiFi disconnected:    red_
# sync_time successful: blue_
red_ = 0
green_ = 1
blue_ = 2
yellow_ = 3
orange_ = 4
pink_ = 5
white_ = 6
black_ = 7
clr_dict = {
    red_: (255, 0, 0),
    green_: (0, 255, 0),
    blue_: (0, 0, 255),
    yellow_: (255, 255, 0),
    orange_: (255, 140, 0),
    pink_: (255, 20, 147),
    white_: (255, 255, 255),
    black_: (0, 0, 0)
}
clr_dict_rev = {
    red_: 'RED',
    green_: 'GREEN',
    blue_: 'BLUE',
    yellow_: 'YELLOW',
    orange_: 'ORANGE',
    pink_: 'PINK',
    white_: 'WHITE',
    black_: 'BLACK'
}


def blink(clr):
    if clr in clr_dict.keys():
        fg = clr_dict[clr]
        bg = clr_dict[black_]
        fg_pen = graphics.create_pen(fg[0], fg[1], fg[2])
        bg_pen = graphics.create_pen(bg[0], bg[1], bg[2])
        for h in range(3):  # blink 3 times
            for i in range(2):  # horzontal
                for j in range(2):  # vertical
                    graphics.set_pen(fg_pen)  # green or red
                    graphics.pixel(i, j)
            gu.update(graphics)
            time.sleep(0.2)
            for i in range(2):  # horizontal
                for j in range(2):  # vertical
                    graphics.set_pen(bg_pen)  # black
                    graphics.pixel(i, j)
            gu.update(graphics)
            time.sleep(0.2)


def connect_to_wifi():
    print("Connecting to Wifi")
    blink(red_)
    from secrets import WIFI_SSID, WIFI_PASSWORD
    print("wifi available")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    print("Connected to wifi")
    blink(green_)


def get_text_from_web():
    connect_to_wifi()
    print("Getting text from web.")
    blink(orange_)
    url = "https://helloworld-k4lulsqqwa-ew.a.run.app"
    response = urequests.get(url)
    full_response = response.json()
    my_message = full_response['text']
    print("Got text - {}".format(my_message))
    blink(white_)
    return my_message


# function for drawing outlined text
def outline_text(text, x, y, properties):
    message_colour = properties["message_colour"]
    outline_colour = properties["outline_colour"]
    graphics.set_pen(graphics.create_pen(int(outline_colour[0]), int(outline_colour[1]), int(outline_colour[2])))
    graphics.text(text, x - 1, y - 1, -1, 1)
    graphics.text(text, x, y - 1, -1, 1)
    graphics.text(text, x + 1, y - 1, -1, 1)
    graphics.text(text, x - 1, y, -1, 1)
    graphics.text(text, x + 1, y, -1, 1)
    graphics.text(text, x - 1, y + 1, -1, 1)
    graphics.text(text, x, y + 1, -1, 1)
    graphics.text(text, x + 1, y + 1, -1, 1)

    graphics.set_pen(graphics.create_pen(int(message_colour[0]), int(message_colour[1]), int(message_colour[2])))
    graphics.text(text, x, y, -1, 1)


# constants for controlling scrolling text
def _defaults():
    default = {
        "padding": 5,
        "message_colour": (255, 255, 255),
        "outline_colour": (0, 0, 0),
        "background_colour": (0, 0, 0),
        "hold_time": 2.0,
        "step_time": 0.075
    }
    return default


def display_text(initial_text="", initial_brightness=0.5, setup_values=_defaults()):
    last_time = time.ticks_ms()
    last_request = int(time.time())
    message_text = initial_text
    shift = 0
    state = STATE_PRE_SCROLL

    gu.set_brightness(initial_brightness)

    # set the font
    graphics.set_font("bitmap8")

    while True:
        time_ms = time.ticks_ms()

        loop_time = int(time.time())
        time_gap = loop_time - last_request

        if time_gap > 30:
            print("Re-get text from web")
            message_text = get_text_from_web()
            print(message_text)
            last_request = int(time.time())

        # calculate the message width so scrolling can happen
        msg_width = graphics.measure_text(message_text, 1)

        if gu.is_pressed(GalacticUnicorn.SWITCH_BRIGHTNESS_UP):
            gu.adjust_brightness(+0.01)

        if gu.is_pressed(GalacticUnicorn.SWITCH_BRIGHTNESS_DOWN):
            gu.adjust_brightness(-0.01)

        if state == STATE_PRE_SCROLL and time_ms - last_time > setup_values["hold_time"] * 1000:
            if msg_width + setup_values["padding"] * 2 >= width:
                state = STATE_SCROLLING
            last_time = time_ms

        if state == STATE_SCROLLING and time_ms - last_time > setup_values["step_time"] * 1000:
            shift += 1
            if shift >= (msg_width + _defaults()["padding"] * 2) - width - 1:
                state = STATE_POST_SCROLL
            last_time = time_ms

        if state == STATE_POST_SCROLL and time_ms - last_time > _defaults()["hold_time"] * 1000:
            state = STATE_PRE_SCROLL
            shift = 0
            last_time = time_ms
        background_colour = _defaults()["background_colour"]
        graphics.set_pen(
            graphics.create_pen(int(background_colour[0]), int(background_colour[1]), int(background_colour[2])))
        graphics.clear()

        outline_text(message_text, x=_defaults()["padding"] - shift, y=2, properties=_defaults())

        # update the display
        gu.update(graphics)

        # pause for a moment (important or the USB serial device will fail)
        time.sleep(0.001)


display_text(initial_text=get_text_from_web())
