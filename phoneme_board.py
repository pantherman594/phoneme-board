import math
import os
import time

import adafruit_74hc595
from adafruit_mcp3xxx.analog_in import AnalogIn
import adafruit_mcp3xxx.mcp3008 as MCP
import board
import busio
import digitalio
import pwmio

MIN = 400
MAX = 65000

colors = [
  (False, False, False), # off
  (True , False, False), # red
  (True , True , False), # yellow
  (False, True , False), # green
  (False, True , True ), # aqua
  (False, False, True ), # blue
  (True , False, True ), # purple
  (True , True , True ), # white
]

phoneset = [
  "pau", "aa", "ae", "ah", "ao", "aw", "ax", "axr", "ay", "b", "ch", "d", "dh",
  "eh", "el", "em", "en", "er", "ey", "f", "g", "hh", "hv", "ih", "iy", "jh",
  "k", "l", "m", "n", "ng", "ow", "oy", "p", "r", "s", "sh", "t", "th", "uh",
  "uw", "v", "w", "y", "z", "zh"
]
numPhones = len(phoneset)

spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D5)
mcp = MCP.MCP3008(spi, cs)

srLatch = digitalio.DigitalInOut(board.D17)
sr = adafruit_74hc595.ShiftRegister74HC595(spi, srLatch)

brightnessCtrl = pwmio.PWMOut(board.D27, frequency=5000, duty_cycle=0) # active low

pots = [AnalogIn(mcp, pin) for pin in [MCP.P0, MCP.P1, MCP.P2, MCP.P3, MCP.P4, MCP.P5, MCP.P6, MCP.P7]]
ins = [1, 2, 3, 4, 5]
buttonIn = 0

leds = [sr.get_pin(i) for i in range(6)]

sequenceButton = digitalio.DigitalInOut(board.D16)
sequenceButton.switch_to_input(pull=digitalio.Pull.UP)

def setBrightness(brightness):
    brightnessCtrl.duty_cycle = int(65535 * (1 - brightness))

def valueToThirdIndex(value):
    if value <= MIN or value >= MAX:
        return None

    index = math.floor(((value - MIN) / (MAX - MIN)) * numPhones * 3) / 3
    return index

def indexToColors(index):
    if index is None:
        index = 0
    else:
        index += 1

    if index % 1 < 0.3 or index % 1 > 0.7:
        index = 63
    index = math.floor(index)

    a = index // 8
    b = index % 8
    return list(colors[a]) + list(colors[b])

def indexToPhone(index):
    if index is None:
        index = 0
    else:
        index += 1

    index = math.floor(index)

    if index < 0 or index >= numPhones:
        index = 0

    return phoneset[index]

def getValue(ch):
    pot = pots[ch]
    _ = pot.value
    values = [pot.value for _ in range(3)]
    if max(values) - min(values) > ((MAX - MIN) / numPhones):
        return 0
    return sum(values) / 3

def getIndex(index):
    return valueToThirdIndex(getValue(index))

def sayPhones(phones):
    os.system("festival -b \"(voice_kal_diphone)\" \"(SayPhones '({}))\"".format(" ".join(phones)))

saidButton = False
saidSequence = False

brightness = 0.005

setBrightness(brightness)

for led in leds:
    led.value = True

for _ in range(3):
    setBrightness(brightness)
    time.sleep(0.5)
    setBrightness(0)
    time.sleep(0.5)

while True:
    setBrightness(brightness)
    for i, c in enumerate(indexToColors(getIndex(ins[0]))):
        leds[i].value = c

    val = getIndex(buttonIn)
    buttonPhone = indexToPhone(val)

    if buttonPhone is not None and buttonPhone != "pau":
        if not saidButton:
            saidSequence = False
            saidButton = True
            sayPhones(["pau", buttonPhone, "pau"])
            continue
    else:
        saidButton = False

    sequence = ["pau"]

    for ch in ins:
        val = getValue(ch)
        index = valueToThirdIndex(val)
        phone = indexToPhone(index)

        if phone is not None:
            sequence.append(phone)
        elif sequence[-1] != "pau":
            sequence.append("pau")

    if not sequenceButton.value:
        if not saidSequence:
            saidSequence = True
            if len(sequence) > 1:
                if sequence[-1] != "pau":
                    sequence.append("pau")
                sayPhones(sequence)
    else:
        saidSequence = False
    time.sleep(0.1)
