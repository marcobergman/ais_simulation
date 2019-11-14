import socket
import sys
import math
import time

# https://softwaredevelopmentperestroika.wordpress.com/2013/11/27/more-fun-with-python-navigational-tricks-ais-nmea-encodingdecoding/


def nmeaChecksum(s): # str -> two hex digits in str
	chkSum = 0
	subStr = s[1:len(s)]

	for e in range(len(subStr)):
		chkSum ^= ord((subStr[e]))

	hexstr = str(hex(chkSum))[2:4]
	if len(hexstr) == 2:
		return hexstr
	else:
		return '0'+hexstr

	# join NMEA pre- and postfix to payload string

def joinNMEAstrs(payloadstr): #str -> str
	tempstr = '!AIVDM,1,1,,A,' + payloadstr + ',0'
	chksum = nmeaChecksum(tempstr)
	tempstr += '*'
	tempstr += chksum 
	return tempstr


def ais_message (i_mtype, i_repeat, i_mmsi, i_status, i_turn, i_speed, i_accuracy, i_lat, i_lon, i_course, i_heading, i_second, i_maneuver, i_spare, i_raim, i_radio):
	def binform (num, bitWidth):
		# deal with 2's complement
		# thx to https://stackoverflow.com/questions/12946116/twos-complement-binary-in-python
		num = int(num)
		num &= (2 << bitWidth-1)-1 # mask
		formatStr = '{:0'+str(bitWidth)+'b}'
		return formatStr.format(int(num))

	bits = binform(i_mtype,6) + binform(i_repeat,2) + binform(i_mmsi, 30) + binform(i_status, 4) + \
		binform(int(4.733*math.sqrt(float(i_turn))), 8) + binform(i_speed*10, 10) + binform(i_accuracy, 1) + binform(int(600000*float(i_lon)), 28) + \
		binform(int(600000*float(i_lat)), 27) + binform(i_course*10, 12) + binform(i_heading, 9) + binform(i_second, 6) + \
		binform(i_maneuver, 2) + binform(i_spare, 3) + binform(i_raim, 1) + binform(i_radio, 19)
	#print "type..r.mmsi..........................sta.turn....speed.....alon.........................lat........................course......heading..sec...m.sp.rradio.............."
	#print bits
	enc = ''
	mapping = "0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVW`abcdefghijklmnopqrstuvw"
	while bits:
		n=int(bits[:6],2)
		enc = enc + mapping[n:n+1]
		bits = bits[6:]

	return '' + joinNMEAstrs(enc)
	

def rmc_message(i_lat, i_lon, i_heading, i_speed):
	lat = "%02.f%07.4f" % (math.trunc(i_lat), 60*(i_lat-math.trunc(i_lat)))
	lon = "%03.f%07.4f" % (math.trunc(i_lon), 60*(i_lon-math.trunc(i_lon)))
	tempstr = '$GPRMC,123519,A,%s,N,%s,E,%s,%s,230394,,,A,C' % (lat, lon, i_speed, i_heading)
	chksum = nmeaChecksum(tempstr)
	tempstr += '*'
	tempstr += chksum 
	return tempstr


class Boat(object):
	def __init__(self, mmsi, name, lat, lon, speed, heading, status, maneuver, own):
		self.mmsi = mmsi
		self.name = name
		self.lat = float(lat)
		self.lon = float(lon)
		self.speed = float(speed)
		self.heading = float(heading)
		self.status = status
		self.maneuver = maneuver
		self.own = own
		self.last_move = float(time.time())

	def show(self):
		if self.own == False:
			my_message = ais_message (1, 0, self.mmsi, self.status, 0, self.speed, 1, self.lat, self.lon, self.heading, self.heading, 0, self.maneuver, 0, 0, 0)
		else:
			my_message = rmc_message (self.lat, self.lon, self.heading, self.speed)
		print my_message

		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server_address = ('localhost', 20220)
		sock.connect(server_address)
		sock.sendall(my_message+"\r\n")
		sock.close()

	def move(self):
		elapsed = time.time() - self.last_move
		offset=10
		self.lat = self.lat + elapsed*self.speed/3600/6* math.cos((self.heading+offset)/180*math.pi)
		self.lon = self.lon + elapsed*self.speed/3600/6* math.sin((self.heading+offset)/180*math.pi) #* math.cos(self.lat/180*math.pi)
		self.show()
		self.last_move = float(time.time())

boats = []

boats.append(Boat(244123456, 'Zeehond', 52.587950545, 3.066306379, 19, 28, 0, 0, False))
boats.append(Boat(244123457, 'Zeehond', 52.646791901, 3.009493285, 21, 208, 0, 0, False))
boats.append(Boat(244123458, 'Zeehond', 52.701504157, 3.057951512, 18, 208, 0, 0, False))
boats.append(Boat(244123459, 'Zeehond', 52.539194426, 3.024532045, 20, 28, 1, 1, False))
boats.append(Boat(244123450, 'Zeehond', 52.614336667, 3.161551667, 6, 298, 0, 2, True))

for boat in boats:
	print("Showing boat %s" % (boat.name))
	boat.show()

for x in range (1,500):
	time.sleep(1)
	for boat in boats:
		boat.move()

