import json
import time
import network
import urequests
from galactic import GalacticUnicorn
from picographics import PicoGraphics, DISPLAY_GALACTIC_UNICORN as DISPLAY

'''
Make request for text
'''
def connect_to_wifi():
    print("Connecting to Wifi")
    try:
        from secrets import WIFI_SSID, WIFI_PASSWORD
        wifi_available = True
        print("wifi available")
    except ImportError:
        print("Create secrets.py with your WiFi credentials to get time from NTP")
        wifi_available = False
        print("no wifi")

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    print("Connected to wifi")

def get_next_arrivals():
    print("Getting next arrivals")
    url = "https://api.tfl.gov.uk/StopPoint/490007732N/arrivals"
    print(url)
    response = urequests.get(url)
    print(response.status_code)
    if response.status_code == 200 and response.json != "[]":
        nextArrivals = response.json()
        nextArrivals.sort(key=lambda k: k['timeToStation'], reverse=False)

    print("Got next arrivals")
    print(nextArrivals)
    return nextArrivals


def build_message_text(arrivals):
    messageTxt = ""
    if(len(arrivals) == 0):
        messageTxt = "No idea when the next bus is..."
    else:
        busArrivals = []
        for bus in arrivals:
            bus_arrival = {}
            bus_arrival['timeToStation'] = bus['timeToStation']
            bus_arrival['lineName'] = bus['lineName']
            #bus_arrival['ttl'] = isoparse(bus['timeToLive'])
            bus_arrival['ttl'] = bus['timeToLive']
            bus_arrival['destinationName'] = bus['destinationName']
            bus_arrival['stopName'] = bus['stationName']
            bus_arrival['stopCode'] = bus['platformName']
            busArrivals.append(bus_arrival)

    for bus in arrivals:

        minutes = bus['timeToStation']//60
        seconds = bus['timeToStation']%60
        messageTxt = messageTxt + '{} {:02d}m{:02d}s {}'.format(bus['lineName'], minutes, seconds, bus['destinationName']) + ' - '

    print(messageTxt)
    return messageTxt

'''
Display scrolling wisdom, quotes or greetz.

You can adjust the brightness with LUX + and -.
'''

connect_to_wifi()

print("set up constants")
# constants for controlling scrolling text
PADDING = 5
MESSAGE_COLOUR = (255, 255, 255)
OUTLINE_COLOUR = (0, 128, 0)
BACKGROUND_COLOUR = (255, 0, 0)
#MESSAGE = "Merry Christmas, Love Ben, Simone, Albi, Liberty, Tipsy and the Tortoises. xxx"
#MESSAGE = messageTxt
HOLD_TIME = 2.0
STEP_TIME = 0.075

# create galactic object and graphics surface for drawing
gu = GalacticUnicorn()
graphics = PicoGraphics(DISPLAY)

width = GalacticUnicorn.WIDTH
height = GalacticUnicorn.HEIGHT


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


gu.set_brightness(0.5)

# state constants
STATE_PRE_SCROLL = 0
STATE_SCROLLING = 1
STATE_POST_SCROLL = 2

shift = 0
state = STATE_PRE_SCROLL

# set the font
graphics.set_font("bitmap8")



last_time = time.ticks_ms()
messageTxt = ""
while True:
    print("Entering loop")
    
    time_ms = time.ticks_ms()
    time_gap = time_ms - last_time
    print("Current time gap = ")
    print(time_gap)
    
    #if time_gap > 300000:
    #    messageTxt = build_message_text(get_next_arrivals())
    #    print("Getting new arrivals loop on time")
    
    if messageTxt=="":
        print("Getting new arrivals loop on text")
        messageTxt = build_message_text(get_next_arrivals())
    # calculate the message width so scrolling can happen
    print("continuing loop")
    
    msg_width = graphics.measure_text(messageTxt, 1)
    print(msg_width)

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