import json
import time
import network
import urequests
from galactic import GalacticUnicorn
from picographics import PicoGraphics, DISPLAY_GALACTIC_UNICORN as DISPLAY
from local_secrets import WIFI_SSID, WIFI_PASSWORD, URL, password

# --- Setup display ---
graphics = PicoGraphics(DISPLAY)
gu = GalacticUnicorn()

WIDTH = GalacticUnicorn.WIDTH
HEIGHT = GalacticUnicorn.HEIGHT

# --- Colour Constants ---
RED, GREEN, BLUE, YELLOW, ORANGE, PINK, WHITE, BLACK = range(8)

COLOURS = {
    RED: (255, 0, 0),
    GREEN: (0, 255, 0),
    BLUE: (0, 0, 255),
    YELLOW: (255, 255, 0),
    ORANGE: (255, 140, 0),
    PINK: (255, 20, 147),
    WHITE: (255, 255, 255),
    BLACK: (0, 0, 0),
}

# --- State Constants ---
STATE_PRE_SCROLL = 0
STATE_SCROLLING = 1
STATE_POST_SCROLL = 2

# --- Helper Functions ---
def get_pen(rgb):
    return graphics.create_pen(*rgb)

def blink(colour):
    fg = COLOURS.get(colour, (255, 0, 0))  # fallback to red
    bg = COLOURS[BLACK]

    fg_pen = get_pen(fg)
    bg_pen = get_pen(bg)

    for _ in range(3):
        for i in range(2):
            for j in range(2):
                graphics.set_pen(fg_pen)
                graphics.pixel(i, j)
        gu.update(graphics)
        time.sleep(0.2)

        for i in range(2):
            for j in range(2):
                graphics.set_pen(bg_pen)
                graphics.pixel(i, j)
        gu.update(graphics)
        time.sleep(0.2)

def connect_to_wifi():
    print("Connecting to WiFi...")
    blink(RED)

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    print("Connected to WiFi")
    blink(GREEN)

def get_text_from_web():
    print("Getting text from web...")
    blink(ORANGE)

    url = f"{URL}/?pword={password}"
    response = urequests.get(url)
    my_message = response.json().get('text', '')

    print(f"Got text: {my_message}")
    blink(WHITE)
    return my_message

def outline_text(text, x, y, properties):
    message_colour = properties["message_colour"]
    outline_colour = properties["outline_colour"]

    outline_pen = get_pen(outline_colour)
    message_pen = get_pen(message_colour)

    graphics.set_pen(outline_pen)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx != 0 or dy != 0:
                graphics.text(text, x + dx, y + dy, -1, 1)

    graphics.set_pen(message_pen)
    graphics.text(text, x, y, -1, 1)

def default_setup():
    return {
        "padding": 5,
        "message_colour": (255, 255, 255),
        "outline_colour": (0, 0, 0),
        "background_colour": (0, 0, 0),
        "hold_time": 2.0,
        "step_time": 0.075,
    }

def display_text(initial_text="", initial_brightness=0.5, setup_values=None):
    if setup_values is None:
        setup_values = default_setup()

    last_time = time.ticks_ms()
    last_request = int(time.time())
    message_text = initial_text
    shift = 0
    state = STATE_PRE_SCROLL

    gu.set_brightness(initial_brightness)
    graphics.set_font("bitmap8")

    while True:
        time_ms = time.ticks_ms()
        now = int(time.time())

        if now - last_request > 30:
            print("Re-getting text from web...")
            message_text = get_text_from_web()
            last_request = now

        msg_width = graphics.measure_text(message_text, 1)

        if gu.is_pressed(GalacticUnicorn.SWITCH_BRIGHTNESS_UP):
            gu.adjust_brightness(+0.01)

        if gu.is_pressed(GalacticUnicorn.SWITCH_BRIGHTNESS_DOWN):
            gu.adjust_brightness(-0.01)

        if state == STATE_PRE_SCROLL and time_ms - last_time > setup_values["hold_time"] * 1000:
            if msg_width + setup_values["padding"] * 2 >= WIDTH:
                state = STATE_SCROLLING
            last_time = time_ms

        if state == STATE_SCROLLING and time_ms - last_time > setup_values["step_time"] * 1000:
            shift += 1
            if shift >= (msg_width + setup_values["padding"] * 2) - WIDTH - 1:
                state = STATE_POST_SCROLL
            last_time = time_ms

        if state == STATE_POST_SCROLL and time_ms - last_time > setup_values["hold_time"] * 1000:
            state = STATE_PRE_SCROLL
            shift = 0
            last_time = time_ms

        bg_colour = setup_values["background_colour"]
        graphics.set_pen(get_pen(bg_colour))
        graphics.clear()

        outline_text(message_text, x=setup_values["padding"] - shift, y=2, properties=setup_values)
        gu.update(graphics)

        time.sleep(0.001)

# --- Main Program ---
connect_to_wifi()
display_text(initial_text=get_text_from_web())
