####################################################################
# Simple script to control temperateu based on heat sensor reading #
####################################################################
import time
import sys
import signal
import datetime
import pigpio
import math
import multiprocessing

pi = pigpio.pi()

# HTU21D-F Address
addr = 0x40

# i2c bus, if you have a Raspberry Pi Rev A, change this to 0
bus = 1

# GPIO's
gpio_heating1 = 24
gpio_fan1 = 22
gpio_allneutral = 23
gpio_pwm_fan1 = 18

def htu_reset():
	handle = pi.i2c_open(bus, addr) 
	pi.i2c_write_byte(handle, 0xFE) 
	pi.i2c_close(handle) 
	time.sleep(0.2)

def read_environment():
	handle = pi.i2c_open(bus, addr)
	pi.i2c_write_byte(handle, 0xE5) # read humidity
	time.sleep(0.055) # Reading can take up to 50ms
	(count, humByteArray) = pi.i2c_read_device(handle, 3)
	pi.i2c_write_byte(handle, 0xE3) # read temp
	time.sleep(0.055) # Reading can take up to 50ms
	(count, tempByteArray) = pi.i2c_read_device(handle, 3)
	pi.i2c_close(handle)

	temp_reading = (tempByteArray[0] * 256) + tempByteArray[1]
	temp_reading = math.fabs(temp_reading)
	temp = ((temp_reading / 65536) * 175.72 ) - 46.85

	hum_reading = (humByteArray[0] * 256) + humByteArray[1]
	hum_reading = math.fabs(hum_reading)
	hum_reading = ((hum_reading / 65536) * 125) - 6
	humidity = ((25 - temp) * -0.15) + hum_reading
	return (temp, humidity)
	

def IsNeutral():
	if (pi.read(gpio_allneutral) == 1):
		return False
	else:
		return True

def Neutral(onOff):
	if (onOff == True):
		pi.write(gpio_allneutral, 0)
	else:
		pi.write(gpio_allneutral, 1)

def Fan1(speed):
	if (IsNeutral() == False):
		print "Trying to switch on fan but neutral is off"
		return False
	
	if (speed < 10):
		pi.write(gpio_fan1, 0)
		print "[Fan1] Turning off."
	else:
		pi.write(gpio_fan1, 1)
		pi.hardware_PWM(gpio_pwm_fan1, 25000, speed*10000)
		print "[Fan1] Setting to", speed,"%"

def FanSpeed1():
	if (IsNeutral() == False or pi.read(gpio_fan1) == 0):
		return 0

	speed = pi.get_PWM_dutycycle(gpio_pwm_fan1)
	return (speed / 10000)


def Heating(onOff):
	if (IsNeutral() == False):
		print "Truing to switch on heating but neutral is off"
		return False

	if (onOff == True):
		pi.write(gpio_heating1, 1)
		print "[Heat] Turning on"
	else:
		pi.write(gpio_heating1, 0)
		print "[Heat] Turning off"


def IsHeating():
	if (IsNeutral() == False or pi.read(gpio_heating1) == 0):
		return False
	else:
		return True

def startup():
	# Setup our GPIO's
	pi.set_mode(gpio_heating1, pigpio.OUTPUT)
	pi.set_mode(gpio_fan1, pigpio.OUTPUT)
	pi.set_mode(gpio_allneutral, pigpio.OUTPUT)

	htu_reset()
	Neutral(True)




def makeBiltong(cmds):
	# Targets
	target_temp = 21
	fan1_heatspeed=70
	fan1_nonheatspeed=10


	i = 0
	while True:
		if (i > 10):
			(temp, hum) = read_environment()
			now = datetime.datetime.today()	
			line = "%s,%s,%s\n" %(now, temp, hum)
			with open("test.txt", "a") as myfile:
				myfile.write(line)

			if (temp < target_temp and IsHeating() == False):
				Heating(True)
				Fan1(fan1_heatspeed)
			if (temp >= (target_temp+0.5) and IsHeating() == True):
				Heating(False)
				Fan1(fan1_nonheatspeed)
			i=0
		
		if (cmds.empty() == False):
			line = cmds.get()
			print "Parsing: ", line
			if line == 'quit':
				Heating(False)
				Fan1(0)
				Neutral(False)
				break

			if line.startswith('temp') == True:
				target_temp = int(line[5:])
				print "Setting target temp to ", target_temp
			

			if line.startswith('fanspeedon') == True:
				fan1_heatspeed = int(line[11:])
				print "Setting heating on fan speed to ", fan1_heatspeed

			if line.startswith('fanspeedoff') == True:
				fan1_nonheatspeed = int(line[12:])
				print "Setting heating on fan speed to ", fan1_nonheatspeed

			if line == 'status':
				(temp, hum) = read_environment()
				print "Current temperateure/humid:", temp,"/",hum
				print "Heating is:", IsHeating()
				print "FanSpeed  :", FanSpeed1()

		time.sleep(1)
		i = i+1

def main():
	startup()
	cmdQueue = multiprocessing.Queue()
	
	proc = multiprocessing.Process(target=makeBiltong, args=(cmdQueue,))
	proc.start()
	line = ''
	while line != 'quit':
		line = raw_input("Biltongbox: ")
		cmdQueue.put(line)
	proc.join()

if __name__ == "__main__":
	main()
