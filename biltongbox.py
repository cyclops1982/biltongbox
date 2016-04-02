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
gpio_fanneutral = 4
gpio_heating1 = 5
gpio_heating2 = 22
gpio_fan1 = 17

gpio_fan2 = 27
gpio_heatingneutral = 6
gpio_pwm_fan1 = 12
gpio_pwm_fan2 = 13


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
	

def IsHeatingNeutral():
	if (pi.read(gpio_heatingneutral) == 1):
		return True
	else:
		return False

def IsFanNeutral():
	if (pi.read(gpio_fanneutral) == 1):
		return True
	else:
		return False

def HeatingNeutral(onOff):
	if (onOff == True):
		pi.write(gpio_heatingneutral, 0)
	else:
		pi.write(gpio_heatingneutral, 1)


def FanNeutral(onOff):
	if (onOff == True):
		pi.write(gpio_fanneutral, 0)
	else:
		pi.write(gpio_fanneutral, 1)

def Fan1(speed):
	if (IsFanNeutral() == False):
		print "Trying to switch on fan but neutral is off"
		return False
	
	if (speed < 10):
		pi.write(gpio_fan1, 0)
		print "[Fan1] Turning off."
	else:
		pi.write(gpio_fan1, 1)
		pi.hardware_PWM(gpio_pwm_fan1, 25000, speed*10000)
		print "[Fan1] Setting to", speed,"%"


def Fan2(speed):
	if (IsFanNeutral() == False):
		print "Trying to switch on fan but neutral is off"
		return False
	
	if (speed < 10):
		pi.write(gpio_fan2, 0)
		print "[Fan2] Turning off."
	else:
		pi.write(gpio_fan2, 1)
		pi.hardware_PWM(gpio_pwm_fan2, 25000, speed*10000)
		print "[Fan2] Setting to", speed,"%"


def FanSpeed1():
	if (IsFanNeutral() == False or pi.read(gpio_fan1) == 0):
		return 0

	speed = pi.get_PWM_dutycycle(gpio_pwm_fan1)
	return (speed / 10000)

def FanSpeed2():
	if (IsFanNeutral() == False or pi.read(gpio_fan2) == 0):
		return 0

	speed = pi.get_PWM_dutycycle(gpio_pwm_fan2)
	return (speed / 10000)

def IsHeating1():
	if (IsHeatingNeutral() == False):
		return False
	
	if (pi.read(gpio_heating1) == 0):
		return False
	else:
		return True

def IsHeating1():
	if (IsHeatingNeutral() == False):
		return False
	
	if (pi.read(gpio_heating2) == 0):
		return False
	else:
		return True


def Heat1(onOff):
	if (IsHeatingNeutral() == False):
		print "Trying to switch on heating but neutral is off"
		return False

	if (onOff == True):
		pi.write(gpio_heating1, 1)
		print "[Heat1] Turning on"
	else:
		pi.write(gpio_heating1, 0)
		print "[Heat1] Turning off"

def Heat2(onOff):
	if (IsHeatingNeutral() == False):
		print "Trying to switch on heating but neutral is off"
		return False

	if (onOff == True):
		pi.write(gpio_heating2, 1)
		print "[Heat2] Turning on"
	else:
		pi.write(gpio_heating2, 0)
		print "[Heat2] Turning off"


def startup():
	# Setup our GPIO's
	pi.set_mode(gpio_heating1, pigpio.OUTPUT)
	pi.set_mode(gpio_heating2, pigpio.OUTPUT)
	pi.set_mode(gpio_heatingneutral, pigpio.OUTPUT)
	pi.set_mode(gpio_fan1, pigpio.OUTPUT)
	pi.set_mode(gpio_fan2, pigpio.OUTPUT)
	pi.set_mode(gpio_fanneutral, pigpio.OUTPUT)
	pi.set_mode(gpio_pwm_fan1, pigpio.OUTPUT)
	pi.set_mode(gpio_pwm_fan2, pigpio.OUTPUT)

	htu_reset()



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
			line = "%s,%d,%d,%d,%d,%d,%d,%d,%d,%d\n" %(now, temp, hum, IsHeating1(), IsHeating2(), FanSpeed1(), FanSpeed2(), target_temp)
			with open("biltong.csv", "a") as myfile:
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
			print
			print "Parsing: ", line

			if line == 'quit':
				Heating(False)
				Fan1(0)
				Neutral(False)
				break

			if line.startswith('temp') == True:
				target_temp = int(line[5:])
				print "Setting target temp to ", target_temp
				i=10
			

			if line.startswith('fanspeedon') == True:
				fan1_heatspeed = int(line[11:])
				print "Setting heating on fan speed to ", fan1_heatspeed
				if (IsHeating() == True):
					Fan1(fan1_heatspeed)

			if line.startswith('fanspeedoff') == True:
				fan1_nonheatspeed = int(line[12:])
				print "Setting heating on fan speed to ", fan1_nonheatspeed
				if (IsHeating() == False):
					Fan1(fan1_nonheatspeed)

			if line == 'status':
				(temp, hum) = read_environment()
				print "Current temperateure/humid:", temp,"/",hum
				print "Heating is:", IsHeating()
				print "FanSpeed  :", FanSpeed1()
				print "Target temp:", target_temp
				print "Fan On Speed:", fan1_heatspeed
				print "Fan Off Speed:", fan1_nonheatspeed

			if line == 'help':
				print "Possible commands:"
				print "status - get the current biltongbox status"
				print "fanspeedoff <nr 0-100> - set the fanspeed when heating is off"
				print "fanspeedon <nr 0-100> - set the fanspeed when heating is on"
				print "temp <nr> - set the targetted temperature"

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
