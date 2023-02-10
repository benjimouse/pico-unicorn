import json
import time
import network
import urequests
from galactic import GalacticUnicorn
from picographics import PicoGraphics, DISPLAY_GALACTIC_UNICORN as DISPLAY



def connect_to_wifi():
    print("Connecting to Wifi")
    try:
        from secrets import WIFI_SSID, WIFI_PASSWORD
        wifi_available = True
        print("wifi available")
    except ImportError:
        wifi_available = False
        print("no wifi")

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    print("Connected to wifi")

def get_text_from_web():
    print("Getting text from web.")
    url = "https://helloworld-k4lulsqqwa-ew.a.run.app"
    response = urequests.get(url)
    full_response = response.json()
    my_message = full_response['text']

    return my_message


# function for drawing outlined text
def outline_text(text, x, y):
    graphics.set_pen(graphics.create_pen(int(OUTLINE_COLOUR[0]), int(OUTLINE_COLOUR[1]), int(OUTLINE_COLOUR[2])))
    graphics.text(text, x - 1, y - 1, -1, 1)
    graphics.text(text, x, y - 1, -1, 1)
    graphics.text(text, x + 1, y - 1, -1, 1)
    graphics.text(text, x - 1, y, -1, 1)
    graphics.text(text, x + 1, y, -1, 1)
    graphics.text(text, x - 1, y + 1, -1, 1)
    graphics.text(text, x, y + 1, -1, 1)
    graphics.text(text, x + 1, y + 1, -1, 1)

    graphics.set_pen(graphics.create_pen(int(MESSAGE_COLOUR[0]), int(MESSAGE_COLOUR[1]), int(MESSAGE_COLOUR[2])))
    graphics.text(text, x, y, -1, 1)





print("set up constants")
# constants for controlling scrolling text
PADDING = 5
MESSAGE_COLOUR = (255, 255, 255)
OUTLINE_COLOUR = (0, 0, 0)
BACKGROUND_COLOUR = (0, 0, 0)
#MESSAGE = "Merry Christmas, Love Ben, Simone, Albi, Liberty, Tipsy and the Tortoises. xxx"
#MESSAGE = messageTxt
HOLD_TIME = 2.0
STEP_TIME = 0.075

# create galactic object and graphics surface for drawing
gu = GalacticUnicorn()
graphics = PicoGraphics(DISPLAY)

width = GalacticUnicorn.WIDTH
height = GalacticUnicorn.HEIGHT


# state constants
STATE_PRE_SCROLL = 0
STATE_SCROLLING = 1
STATE_POST_SCROLL = 2

shift = 0
state = STATE_PRE_SCROLL

print("Finished setting up constants")

print("Connect to wifi")
connect_to_wifi()
print("Connected")


gu.set_brightness(0.5)

# set the font
graphics.set_font("bitmap8")

last_time = time.ticks_ms()

last_request = int(time.time())
messageTxt = get_text_from_web()

while True:
    time_ms = time.ticks_ms()
    
    loop_time = int(time.time())
    time_gap = loop_time - last_request
    
    if (time_gap > 30):
        print("Re-get text from web")
        messageTxt = get_text_from_web()
        print(messageTxt)
        last_request = int(time.time())

    # calculate the message width so scrolling can happen
    msg_width = graphics.measure_text(messageTxt, 1)

    if gu.is_pressed(GalacticUnicorn.SWITCH_BRIGHTNESS_UP):
        gu.adjust_brightness(+0.01)

    if gu.is_pressed(GalacticUnicorn.SWITCH_BRIGHTNESS_DOWN):
        gu.adjust_brightness(-0.01)

    if state == STATE_PRE_SCROLL and time_ms - last_time > HOLD_TIME * 1000:
        if msg_width + PADDING * 2 >= width:
            state = STATE_SCROLLING
        last_time = time_ms

    if state == STATE_SCROLLING and time_ms - last_time > STEP_TIME * 1000:
        shift += 1
        if shift >= (msg_width + PADDING * 2) - width - 1:
            state = STATE_POST_SCROLL
        last_time = time_ms

    if state == STATE_POST_SCROLL and time_ms - last_time > HOLD_TIME * 1000:
        state = STATE_PRE_SCROLL
        shift = 0
        last_time = time_ms

    graphics.set_pen(graphics.create_pen(int(BACKGROUND_COLOUR[0]), int(BACKGROUND_COLOUR[1]), int(BACKGROUND_COLOUR[2])))
    graphics.clear()
    
    outline_text(messageTxt, x=PADDING - shift, y=2)

    # update the display
    gu.update(graphics)

    # pause for a moment (important or the USB serial device will fail)
    time.sleep(0.001)