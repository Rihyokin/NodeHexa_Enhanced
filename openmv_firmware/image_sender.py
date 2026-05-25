import time
import sensor
import struct
from pyb import UART, LED

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA)
sensor.skip_frames(10)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)

uart = UART(3, 115200, timeout_char=1000)
uart.init(115200, bits=8, parity=None, stop=1)

led = LED(1)

print("=== OpenMV Image Sender ===")
print("Sending JPEG frames to ESP32 via UART3 (P4/P5)")

FRAME_START = b'\xff\xaa'
FRAME_END = b'\xff\xbb'

frame_count = 0

clock = time.clock()
while True:
    clock.tick()

    led.on()
    img = sensor.snapshot()
    led.off()

    jpeg = img.compress(quality=50)

    led.on()
    uart.write(FRAME_START)
    uart.write(struct.pack('<I', len(jpeg)))
    uart.write(jpeg)
    uart.write(FRAME_END)
    led.off()

    frame_count += 1
    fps = clock.fps()
    print("Frame %d sent: %d bytes (%.1f fps)" % (frame_count, len(jpeg), fps))

    while uart.any():
        uart.readchar()