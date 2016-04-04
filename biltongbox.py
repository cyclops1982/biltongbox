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
gpio_fan1 = 27
gpio_fan2 = 17
gpio_heatingneutral = 6
gpio_pwm_fan1 = 13
gpio_pwm_fan2 = 12


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
	


def IsFanNeutral():
	if (pi.read(gpio_fanneutral) == 0):
		return True
	else:
		return False

def FanNeutral(onOff):
	print "Setting FanNeutral to ",onOff
	if (onOff == True):
		pi.write(gpio_fanneutral, 0)
	else:
		pi.write(gpio_fanneutral, 1)

def Fan1(speed):
	if (IsFanNeutral() == False):
		print "Trying to switch on fan but neutral is off"
		return False
	
	if (speed < 10):
		pi.write(gpio_fan1, 1)
		print "[Fan1] Turning off."
	else:
		pi.write(gpio_fan1, 0)
		pi.hardware_PWM(gpio_pwm_fan1, 25000, speed*10000)
		print "[Fan1] Setting to", speed,"%"


def Fan2(speed):
	if (IsFanNeutral() == False):
		print "Trying to switch on fan but neutral is off"
		return False
	
	if (speed < 10):
		pi.write(gpio_fan2, 1)
		print "[Fan2] Turning off."
	else:
		pi.write(gpio_fan2, 0)
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


def IsHeatingNeutral():
	if (pi.read(gpio_heatingneutral) == 0):
		return True
	else:
		return False


def HeatNeutral(onOff):
	print "Setting HeatNeutral to ",onOff
	if (onOff == True):
		pi.write(gpio_heatingneutral, 0)
	else:
		pi.write(gpio_heatingneutral, 1)


def IsHeating1():
	if (IsHeatingNeutral() == False):
		return False
	
	if (pi.read(gpio_heating1) == 0):
		return True
	else:
		return False

def IsHeating2():
	if (IsHeatingNeutral() == False):
		return False
	
	if (pi.read(gpio_heating2) == 0):
		return True
	else:
		return False

def IsHeating():
	if (IsHeating1() == True or IsHeating2() == True):
		return True
	else:
		return False


def Heat1(onOff):
	if (IsHeatingNeutral() == False):
		print "Trying to switch on heating but neutral is off"
		return False

	if (onOff == True):
		pi.write(gpio_heating1, 0)
		print "[Heat1] Turning on"
	else:
		pi.write(gpio_heating1, 1)
		print "[Heat1] Turning off"

def Heat2(onOff):
	if (IsHeatingNeutral() == False):
		print "Trying to switch on heating but neutral is off"
		return False

	if (onOff == True):
		pi.write(gpio_heating2, 0)
		print "[Heat2] Turning on"
	else:
		pi.write(gpio_heating2, 1)
		print "[Heat2] Turning off"


def startup():
	print "Startup."
	# Setup our GPIO's
	pi.set_mode(gpio_heating1, pigpio.OUTPUT)
	pi.set_mode(gpio_heating2, pigpio.OUTPUT)
	pi.set_mode(gpio_heatingneutral, pigpio.OUTPUT)
	pi.set_mode(gpio_fan1, pigpio.OUTPUT)
	pi.set_mode(gpio_fan2, pigpio.OUTPUT)
	pi.set_mode(gpio_fanneutral, pigpio.OUTPUT)

	htu_reset()

	FanNeutral(True)
	HeatNeutral(True)
	Fan1(0)
	Fan2(0)
	Heat1(False)
	Heat2(False)
	print "Startup completed."
	


def makeBiltong(cmds):
	target_temp = 25
	fan1_onspeed = 10
	fan2_onspeed = 0
	fan1_offspeed = 10
	fan2_offspeed = 0

	Fan1(10)

	i = 0
	while True:
		if (i > 10):
			(temp, hum) = read_environment()
			now = datetime.datetime.today()	
			line = "%s,%s,%s,%d,%d,%d,%d,%d\n" %(now, temp, hum, IsHeating1(), IsHeating2(), FanSpeed1(), FanSpeed2(), target_temp)
			with open("biltong.csv", "a") as myfile:
				myfile.write(line)


			if (temp < target_temp):
				if (IsHeating1() == False):
					Heat1(True)
				if (IsHeating2() == False):
					Heat2(True)
			if (temp > target_temp and IsHeating2() == True):
				Heat2(False)
			if (temp >= (target_temp+1) and IsHeating1() == True):
				Heat1(False)
				
			i=0
		
		if (cmds.empty() == False):
			line = cmds.get()
			print
			print "Parsing: ", line

			if line == 'quit':
				Fan1(0)
				Fan2(0)
				Heat1(False)
				Heat2(False)
				HeatNeutral(False)
				FanNeutral(False)
				break

			if line.startswith('temp') == True:
				target_temp = int(line[5:])
				print "Setting target temp to ", target_temp
				i=10
			

			if line.startswith('fan') == True:
				print "Onspeeds: ",fan1_onspeed,fan2_onspeed
				print "Offspeeds: ",fan1_offspeed,fan2_offspeed
				splitline = line.split(' ');
				if (len(splitline) < 3):
					print "Usage: fan <nr> <speed_below_temp> <speed_above_temp>"
				else:
					if (int(splitline[1]) == 0):
						fan1_onspeed = int(splitline[2])
						fan2_onspeed = int(splitline[2])
						if (len(splitline) == 4):
							fan1_offspeed = int(splitline[3])
							fan2_offspeed = int(splitline[3])
						else:
							fan1_offspeed = fan1_onspeed
							fan2_offspeed = fan1_onspeed

					if (int(splitline[1]) == 1):
						fan1_onspeed = int(splitline[2]) 
						if (len(splitline) == 4):
							fan1_offspeed = int(splitline[3])
						else:
							fan1_offspeed = fan1_onspeed
						
					if (int(splitline[1]) == 2):
						fan2_onspeed = int(splitline[2])
						if (len(splitline) == 4):
							fan2_offspeed = int(splitline[3])
						else:
							fan2_offspeed = fan2_onspeed

					if (IsHeating() == True):
						print "Heating is on...",fan1_onspeed,fan2_onspeed
						Fan1(fan1_onspeed)
						Fan2(fan2_onspeed)
					else:
						print "Heating is off...",fan1_offspeed,fan2_offspeed
						Fan1(fan1_offspeed)
						Fan2(fan2_offspeed)
				print "Onspeeds: ",fan1_onspeed,fan2_onspeed
				print "Offspeeds: ",fan1_offspeed,fan2_offspeed

			if line.startswith('heat') == True:
				print "Current heating: ", IsHeating()
				print "Current heat1: ", IsHeating1()
				print "Current heat2: ", IsHeating2()
				splitline = line.split(' ')
				if (len(splitline) > 2):
					onOff = False
					if (splitline[2] == "on"):
						onOff = True
					if (int(splitline[1]) == 0):
						Heat1(onOff)
						Heat2(onOff)
					if (int(splitline[1]) == 1):
						Heat1(onOff)
					if (int(splitline[1]) == 2):
						Heat2(onOff)


			if line == 'status':
				(temp, hum) = read_environment()
				print "Current temperateure/humid:", temp,"/",hum
				print "Target temp:", target_temp
				print "Heating1 is:", IsHeating1()
				print "Heating2 is:", IsHeating2()
				print "Fan1 Speed :", FanSpeed1()
				print "Fan1 Speed :", FanSpeed2()
				print "Fan1 On Speed:", fan1_onspeed
				print "Fan1 Off Speed:", fan1_offspeed
				print "Fan2 On Speed:", fan2_onspeed
				print "Fan2 Off Speed:", fan2_offspeed

			if line == 'help':
				print "Possible commands:"
				print "status - get the current biltongbox status"
				print "fan <nr> <speed_below_temp> <speed_above_temp> - fanspeed when heating is off"
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
