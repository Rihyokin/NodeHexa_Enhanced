import time
import sensor
import struct
from pyb import Servo, UART, LED

pan_servo = Servo(1)
tilt_servo = Servo(2)
pan_servo.calibration(500, 2500, 1500)
tilt_servo.calibration(500, 2500, 1500)

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA)
sensor.skip_frames(10)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)

uart = UART(3, 115200, timeout_char=1000)
uart.init(115200, bits=8, parity=None, stop=1)

led = LED(1)
FRAME_START = b'\xff\xaa'
FRAME_END = b'\xff\xbb'
frame_count = 0

gimbal_target_pan = 0.0
gimbal_target_tilt = 0.0
gimbal_current_pan = 0.0
gimbal_current_tilt = 0.0

GIMBAL_MAX_SPEED = 53.0
last_gimbal_time = time.ticks_ms()

serial_buf = ""

print("=== Self-Test ===")
print("Angle reference: standard servo angles (0-180)")
led.on()

print("Pan: 90 -> 150 -> 90")
for a in range(0, 61, 2):
    pan_servo.angle(a)
    print("  %d" % (90 + a))
    time.sleep(0.08)
for a in range(60, -1, -2):
    pan_servo.angle(a)
    print("  %d" % (90 + a))
    time.sleep(0.08)
print("  pause 1s")
time.sleep(1)
print("Pan: 90 -> 30 -> 90")
for a in range(0, -61, -2):
    pan_servo.angle(a)
    print("  %d" % (90 + a))
    time.sleep(0.08)
for a in range(-60, 1, 2):
    pan_servo.angle(a)
    print("  %d" % (90 + a))
    time.sleep(0.08)

print("  pause 1s")
time.sleep(1)

print("Tilt: 90 -> 150 -> 90")
for a in range(0, 61, 2):
    tilt_servo.angle(a)
    print("  %d" % (90 + a))
    time.sleep(0.08)
for a in range(60, -1, -2):
    tilt_servo.angle(a)
    print("  %d" % (90 + a))
    time.sleep(0.08)
print("  pause 1s")
time.sleep(1)
print("Tilt: 90 -> 30 -> 90")
for a in range(0, -61, -2):
    tilt_servo.angle(a)
    print("  %d" % (90 + a))
    time.sleep(0.08)
for a in range(-60, 1, 2):
    tilt_servo.angle(a)
    print("  %d" % (90 + a))
    time.sleep(0.08)

pan_servo.angle(0)
tilt_servo.angle(0)
led.off()
print("=== Self-Test Done ===")

print("=== Image Sender + Gimbal Control ===")
clock = time.clock()
while True:
    clock.tick()

    img = sensor.snapshot()

    jpeg = img.compress(quality=50)
    uart.write(FRAME_START)
    uart.write(struct.pack('<I', len(jpeg)))
    uart.write(jpeg)
    uart.write(FRAME_END)
    frame_count += 1
    fps = clock.fps()
    print("Frame %d sent: %d bytes (%.1f fps)" % (frame_count, len(jpeg), fps))

    while uart.any():
        c = uart.readchar()
        if c == ord('\n'):
            if serial_buf.startswith("$G,"):
                parts = serial_buf[3:].split(",")
                if len(parts) == 2:
                    try:
                        gimbal_target_pan = float(parts[0])
                        gimbal_target_tilt = float(parts[1])
                        gimbal_target_pan = max(-80.0, min(80.0, gimbal_target_pan))
                        gimbal_target_tilt = max(-80.0, min(80.0, gimbal_target_tilt))
                    except:
                        pass
            serial_buf = ""
        elif c == ord('\r'):
            pass
        else:
            serial_buf += chr(c)
            if len(serial_buf) > 32:
                serial_buf = ""

    now = time.ticks_ms()
    dt = time.ticks_diff(now, last_gimbal_time) / 1000.0
    if dt > 0.1:
        dt = 0.1
    last_gimbal_time = now

    max_delta = GIMBAL_MAX_SPEED * dt

    diff = gimbal_target_pan - gimbal_current_pan
    if abs(diff) > max_delta:
        gimbal_current_pan += max_delta if diff > 0 else -max_delta
    else:
        gimbal_current_pan = gimbal_target_pan

    diff = gimbal_target_tilt - gimbal_current_tilt
    if abs(diff) > max_delta:
        gimbal_current_tilt += max_delta if diff > 0 else -max_delta
    else:
        gimbal_current_tilt = gimbal_target_tilt

    pan_servo.angle(int(gimbal_current_pan))
    tilt_servo.angle(int(gimbal_current_tilt))