import socket
import sys
import math
import time
import xml.etree.ElementTree as ET

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
	def __init__(self, mmsi, name, lat, lon, heading, speed, status, maneuver, own):
		self.mmsi = mmsi
		self.name = name
		self.lat = float(lat)
		self.lon = float(lon)
		self.speed = float(speed)
		self.heading = float(heading)
		self.status = status
		self.maneuver = maneuver
		self.own = own
		self.last_move = time.time()

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
		speedup = 60
		elapsed = time.time() - self.last_move
		self.lat = self.lat + elapsed * self.speed/3600/60 * speedup * math.cos(self.heading/180*math.pi)
		self.lon = self.lon + elapsed * self.speed/3600/60 * speedup * math.sin(self.heading/180*math.pi) / math.cos(self.lat/180*math.pi)
		self.show()
		self.last_move = time.time()

boats = []

tree = ET.parse('ais_simulation.xml')
root = tree.getroot()

ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}

for elem in root.findall('gpx:wpt', ns):
	lat=elem.get('lat')
	lon=elem.get('lon')
	name=elem.find('gpx:name', ns).text
	desc=elem.find('gpx:desc', ns).text
	descriptions=desc.split('\n')
	heading=0
	speed=0
	mmsi=0
	status=0
	for description in descriptions:
		tuple=description.split('=')
		if tuple[0]=='SPEED':
			speed = tuple[1]
		if tuple[0]=='HEADING':
			heading = tuple[1]
		if tuple[0]=='MMSI':
			mmsi = tuple[1]
		if tuple[0]=='STATUS':
			status = tuple[1]
	if name == 'AIS-OWN':
		own=True
	else:
		own=False
	print ('name=%s, mmsi=%s, lat=%s, lon=%s, heading=%s, speed=%s, status=%s' % (name, mmsi, lat, lon, heading, speed, status))
	boats.append(Boat(mmsi, name, float(lat), float(lon), float(heading), float(speed), 0, 0, own))

#boats.append(Boat(244123456, 'Zeehond', 52.587950545, 3.066306379, 28, 19, 0, 0, False))
#boats.append(Boat(244123457, 'Zeehond', 52.646791901, 3.009493285, 208, 21, 0, 0, False))
#boats.append(Boat(244123458, 'Zeehond', 52.701504157, 3.057951512, 208, 18, 0, 2, False))
#boats.append(Boat(244123459, 'Zeehond', 52.539194426, 3.024532045, 28, 20, 1, 1, False))
#boats.append(Boat(244123450, 'Zeehond', 52.614336667, 3.161551667, 298, 6, 0, 0, True))

for x in range (1,500):
	for boat in boats:
		boat.move()
	time.sleep(1)

