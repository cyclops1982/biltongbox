# Not done. References:
# https://www.adafruit.com/datasheets/PCA9685.pdf
# https://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code/blob/master/Adafruit_PWM_Servo_Driver/Adafruit_PWM_Servo_Driver.py
# https://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code/blob/master/Adafruit_PWM_Servo_Driver/Servo_Example.py
# https://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code/blob/master/Adafruit_I2C/Adafruit_I2C.py

import time
import datetime
import pigpio
import math

pi = pigpio.pi()

# HTU21D-F Address
addr = 0x40

# i2c bus, if you have a Raspberry Pi Rev A, change this to 0
bus = 1


  # Registers/etc.
MODE1              = 0x00
MODE2              = 0x01
SUBADR1            = 0x02
SUBADR2            = 0x03
SUBADR3            = 0x04
PRESCALE           = 0xFE
LED0_ON_L          = 0x06
LED0_ON_H          = 0x07
LED0_OFF_L         = 0x08
LED0_OFF_H         = 0x09
ALL_LED_ON_L       = 0xFA
ALL_LED_ON_H       = 0xFB
ALL_LED_OFF_L      = 0xFC
ALL_LED_OFF_H      = 0xFD

# Bits
RESTART            = 0x80
SLEEP              = 0x10
ALLCALL            = 0x01
INVRT              = 0x10
OUTDRV             = 0x04


def setAllPWM(on, off):
	handle = pi.i2c_open(bus, addr)
	pi.i2c_write_byte_data(handle, ALL_LED_ON_L, on & 0xFF)
	pi.i2c_write_byte_data(handle, ALL_LED_ON_H, on >> 8)
	pi.i2c_write_byte_data(handle, ALL_LED_OFF_L, off & 0xFF)
	pi.i2c_write_byte_data(handle, ALL_LED_OFF_L, off & 0xFF)
	pi.i2c_close(handle)


def setPWMFreq(freq):
	prescaleval = 25000000.0    # 25MHz
	prescaleval /= 4096.0       # 12-bit
	prescaleval /= float(freq)
	prescaleval -= 1.0
	prescale = math.floor(prescaleval + 0.5)
	print "Presacel will be: %02x" % prescale 

	handle = pi.i2c_open(bus, addr)
	oldmode = pi.i2c_read_byte_data(handle, MODE1)
	newmode = (oldmode & 0x7F) | 0x10             # sleep

	pi.i2c_write_byte_data(handle, MODE1, newmode)
	pi.i2c_write_byte_data(handle, PRESCALE, int(math.floor(prescale)))
	pi.i2c_write_byte_data(handle, MODE1, oldmode)
	time.sleep(0.005)
	pi.i2c_write_byte_data(handle, MODE1, oldmode | 0x80)
	pi.i2c_close(handle)

def setPWM(channel, on, off):
	handle = pi.i2c_open(bus, addr)
	pi.i2c_write_byte_data(handle, LED0_ON_L + 4*channel, on & 0xFF)
	pi.i2c_write_byte_data(handle, LED0_ON_H + 4*channel, on >> 8)
	pi.i2c_write_byte_data(handle, LED0_OFF_L + 4*channel, off & 0xFF)
	pi.i2c_write_byte_data(handle, LED0_OFF_H + 4*channel, off >> 8)
	pi.i2c_close(handle)

setAllPWM(0, 0);
setPWMFreq(1500);

print "Set channel 0 to 4096"
setPWM(0, 0, 4096)
time.sleep(10);

print "Set channel 0 to 2048"
setPWM(0, 0, 2048)
time.sleep(10);

print "Set channel 0 to 1024"
setPWM(0, 0, 1024)
