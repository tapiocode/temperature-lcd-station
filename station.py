# Copyright (c) 2021 tapiocode
# https://github.com/tapiocode
# MIT License

from machine import I2C, Pin, Timer
from machine_i2c_lcd import I2cLcd
from temperature_meter import temperature_meter
import time

BACKLIGHT_ON_IN_SECONDS         = 6.0
READY_AFTER_RESET_IN_SECONDS    = 3.0
REFRESH_INTERVAL_IN_SECONDS     = 1.0
KEEP_BACKLIGHT_ON               = True

GPIO_LCD_SDA            = 20
GPIO_LCD_SCL            = 21
GPIO_DS18X20            = 22
GPIO_BUTTON_BACKLIGHT   = 27
GPIO_BUTTON_RESET       = 28

CHAR_DEGREE = chr(0xdf)

sensor = temperature_meter(GPIO_DS18X20)
lcd: I2cLcd | None

try:
    i2c = I2C(0, scl = Pin(GPIO_LCD_SCL), sda = Pin(GPIO_LCD_SDA), freq = 400000)
    lcd = I2cLcd(i2c, 0x27, 2, 16)
except OSError:
    print('No LCD Display')
    lcd = None

if lcd:
    if KEEP_BACKLIGHT_ON:
        lcd.backlight_on()
    else:
        lcd.backlight_off()

def write_lcd(str, also_print = False) -> None:
    if lcd:
        lcd.clear()
        lcd.putstr(str)
    if lcd == None or also_print:
        print(str)

tim = Timer()
def run_backlight_timer() -> None:
    if lcd == None or KEEP_BACKLIGHT_ON:
        return
    lcd.backlight_on()
    tim.deinit()
    tim.init(
        period = int(BACKLIGHT_ON_IN_SECONDS * 1000),
        mode = Timer.ONE_SHOT,
        callback = lambda t: lcd.backlight_off()
    )

def get_time_str(seconds: int) -> str:
    # After reaching 9:59:59, overflow to 0:00:00
    seconds %= (9*3600 + 60*60)
    sec = seconds % 60
    min = int(seconds/60) % 60
    hour = int(seconds/3600) % 3600
    return 'T{:01}:{:02}:{:02}'.format(hour, min, sec)

def get_temp_str(temp: float) -> str:
    return '{:5.1f}'.format(temp)

button_backlight = Pin(GPIO_BUTTON_BACKLIGHT, Pin.IN, Pin.PULL_UP)
button_backlight.irq(lambda pin: run_backlight_timer(), Pin.IRQ_RISING)

button_reset = Pin(GPIO_BUTTON_RESET, Pin.IN, Pin.PULL_UP)
button_reset.irq(lambda pin: sensor.reset(), Pin.IRQ_RISING)

run_backlight_timer()
for i in range(1, 5):
    write_lcd('.' * i)
    time.sleep(0.5)

print('Starting...')
while True:
    time_diff = sensor.get_elapsed_time()
    is_ready = time_diff > READY_AFTER_RESET_IN_SECONDS
    temp = sensor.read_temperature()
    is_valid_reading = isinstance(temp, float)
    if sensor.is_initialized() and is_valid_reading:
        cur_temp, min_temp, max_temp = sensor.get_temps()
        reading = '{:<5.1f}{}C  H {}\n{} L {}'\
            .format(
                cur_temp,
                CHAR_DEGREE,
                get_temp_str(min_temp) if is_ready else ' --.-',
                get_time_str(time_diff) if is_ready else '--:--:--',
                get_temp_str(max_temp) if is_ready else ' --.-',
            )
        write_lcd(reading)
    elif is_valid_reading == False:
        write_lcd('No sensor', True)
        sensor.init_sensor()
    time.sleep(REFRESH_INTERVAL_IN_SECONDS)
