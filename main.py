import json
import network
import urequests
from time import ticks_ms, ticks_diff, time, sleep
from galactic import GalacticUnicorn
from picographics import PicoGraphics, DISPLAY_GALACTIC_UNICORN as DISPLAY
from local_secrets import WIFI_SSID, WIFI_PASSWORD, URL, password

# --- Setup display ---
graphics = PicoGraphics(DISPLAY)
gu = GalacticUnicorn()

WIDTH = GalacticUnicorn.WIDTH
HEIGHT = GalacticUnicorn.HEIGHT
TEXT_Y_POSITION = 2  # consistent vertical alignment for all text

# --- Scroll State Constants ---
STATE_PRE_SCROLL = 0
STATE_SCROLLING = 1
STATE_POST_SCROLL = 2

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

# --- Prebuilt Pens for Efficiency ---
PENS = {name: graphics.create_pen(*rgb) for name, rgb in COLOURS.items()}
ERROR_RED_PEN = PENS[RED]
BLACK_PEN = PENS[BLACK]

DEFAULT_LOCAL_MESSAGE = "Default message"

# --- Helper Functions ---

def blink(colour):
    fg_pen = PENS.get(colour, ERROR_RED_PEN)
    bg_pen = BLACK_PEN

    for _ in range(3):
        for i in range(2):
            for j in range(2):
                graphics.set_pen(fg_pen)
                graphics.pixel(i, j)
        gu.update(graphics)
        sleep(0.2)
        for i in range(2):
            for j in range(2):
                graphics.set_pen(bg_pen)
                graphics.pixel(i, j)
        gu.update(graphics)
        sleep(0.2)

def show_error(message):
    """Display an error message and blink."""
    print(f"ERROR: {message}")
    gu.set_brightness(1.0)
    graphics.set_font("bitmap8")

    text_width = graphics.measure_text(message, 1)
    blink_state = True

    if text_width > WIDTH:
        shift = 0
        while True:
            graphics.set_pen(BLACK_PEN)
            graphics.clear()
            graphics.set_pen(ERROR_RED_PEN if blink_state else BLACK_PEN)
            graphics.text(message, 5 - shift, TEXT_Y_POSITION, -1, 1)
            gu.update(graphics)
            shift += 1
            if shift > text_width:
                shift = 0
                blink_state = not blink_state
            sleep(0.05)
    else:
        centered_x = max(5, (WIDTH - text_width) // 2)
        while True:
            graphics.set_pen(BLACK_PEN)
            graphics.clear()
            graphics.set_pen(ERROR_RED_PEN if blink_state else BLACK_PEN)
            graphics.text(message, centered_x, TEXT_Y_POSITION, -1, 1)
            gu.update(graphics)
            blink_state = not blink_state
            sleep(1.0)

def connect_to_wifi(timeout=10):
    print("Connecting to WiFi...")
    blink(RED)

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    start_time = time()
    while not wlan.isconnected():
        if time() - start_time > timeout:
            show_error("Failed to connect to WiFi")
        sleep(0.5)

    print("Connected to WiFi")
    blink(GREEN)

def get_text_from_web():
    print("Getting text from web...")
    blink(ORANGE)

    try:
        url = f"{URL}/?pword={password}"
        response = urequests.get(url)
        full_response = response.json()

        if 'text' not in full_response:
            show_error("No text in response")

        my_message = full_response['text']
        print(f"Got text: {my_message}")
        blink(WHITE)
        return my_message

    except Exception as e:
        print(f"Exception during web request: {e}")
        show_error("Failed to fetch text")

def outline_text(text, x, y, properties):
    message_colour = properties["message_colour"]

    graphics.set_pen(graphics.create_pen(*message_colour))
    graphics.text(text, x, y, -1, 1)


def default_setup():
    return {
        "padding": 5,
        "message_colour": (255, 255, 255),
        "outline_colour": (255, 0, 0),
        "background_colour": (10, 10, 30),  # Dark blue
        "hold_time": 2.0,
        "step_time": 0.075,
    }

# --- Button Handler Function ---
def handle_buttons():
    global message_text, shift, state, message_colour_index, paused, last_button_check

    if ticks_diff(ticks_ms(), last_button_check) > 200:
        if gu.is_pressed(GalacticUnicorn.SWITCH_A):
            print("[Button A] Refresh text manually.")
            message_text = get_text_from_web()
            shift = 0
            state = STATE_PRE_SCROLL

        if gu.is_pressed(GalacticUnicorn.SWITCH_B):
            print("[Button B] Cycle text colour.")
            message_colour_index = (message_colour_index + 1) % len(message_colours)
            setup_values["message_colour"] = message_colours[message_colour_index]

        if gu.is_pressed(GalacticUnicorn.SWITCH_C):
            paused = not paused
            print(f"[Button C] {'Paused' if paused else 'Resumed'} scrolling.")

        if gu.is_pressed(GalacticUnicorn.SWITCH_D):
            print("[Button D] Show local custom message.")
            message_text = local_message
            shift = 0
            state = STATE_PRE_SCROLL

        last_button_check = ticks_ms()

# --- Main Display Function ---
def display_text(initial_text="", initial_brightness=0.5, setup=None):
    global message_text, shift, state, paused, message_colour_index, message_colours, local_message, last_button_check, setup_values
    setup_values = setup or default_setup()

    last_time = ticks_ms()
    last_request = time()
    message_text = initial_text
    shift = 0
    state = STATE_PRE_SCROLL

    gu.set_brightness(initial_brightness)
    graphics.set_font("bitmap8")

    # Heartbeat brightness
    pulse = 0.0
    pulse_direction = 1

    # Colour cycling
    outline_colours = [
        (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 20, 147), (255, 255, 0)
    ]
    outline_index = 0
    last_outline_change = time()

    # Buttons
    paused = False
    last_button_check = ticks_ms()

    message_colours = [
        (255, 255, 255), (0, 255, 255), (255, 0, 255), (255, 255, 0), (0, 255, 0)
    ]
    message_colour_index = 0
    local_message = DEFAULT_LOCAL_MESSAGE

    while True:
        now = time()

        handle_buttons()

        if now - last_request > 30:
            print("Auto-refresh text...")
            message_text = get_text_from_web()
            last_request = now

        msg_width = graphics.measure_text(message_text, 1)

        # Manual brightness buttons
        if gu.is_pressed(GalacticUnicorn.SWITCH_BRIGHTNESS_UP):
            gu.adjust_brightness(+0.01)
        if gu.is_pressed(GalacticUnicorn.SWITCH_BRIGHTNESS_DOWN):
            gu.adjust_brightness(-0.01)

        if not paused:
            if state == STATE_PRE_SCROLL and ticks_diff(ticks_ms(), last_time) > setup_values["hold_time"] * 1000:
                if msg_width + setup_values["padding"] * 2 >= WIDTH:
                    state = STATE_SCROLLING
                last_time = ticks_ms()

            if state == STATE_SCROLLING and ticks_diff(ticks_ms(), last_time) > setup_values["step_time"] * 1000:
                shift += 1
                if shift >= (msg_width + setup_values["padding"] * 2) - WIDTH - 1:
                    state = STATE_POST_SCROLL
                last_time = ticks_ms()

            if state == STATE_POST_SCROLL and ticks_diff(ticks_ms(), last_time) > setup_values["hold_time"] * 1000:
                state = STATE_PRE_SCROLL
                shift = 0
                last_time = ticks_ms()

        # Background
        graphics.set_pen(graphics.create_pen(*setup_values["background_colour"]))
        graphics.clear()

        # Outline colour cycling
        if now - last_outline_change > 10:
            outline_index = (outline_index + 1) % len(outline_colours)
            setup_values["outline_colour"] = outline_colours[outline_index]
            last_outline_change = now

        outline_text(message_text, x=setup_values["padding"] - shift, y=TEXT_Y_POSITION, properties=setup_values)

        # Heartbeat pulse
        pulse += 0.003 * pulse_direction
        if pulse > 0.05:
            pulse_direction = -1
        if pulse < -0.05:
            pulse_direction = 1
        gu.set_brightness(initial_brightness + pulse)

        gu.update(graphics)
        sleep(0.001)

# --- Main Program ---
connect_to_wifi()
display_text(initial_text=get_text_from_web())
