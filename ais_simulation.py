import socket
import sys
import math
import time
import xml.etree.ElementTree as ET
import threading
from datetime import datetime
from random import random


#TCP sending
#sendsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#server_address = ('localhost', 30330)
#sendsocket.connect(server_address)

#UDP broadcasting
sendsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sendsocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
print ("--- Broadcasting NMEA messges to UDP:10110")

listensocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listensocket.bind(("", 20220))
listensocket.listen(1)
print ("--- Listening to NMEA messages at TCP:20220")




def nmeaChecksum(s): # str -> two hex digits in str
    chkSum = 0
    subStr = s[1:len(s)] # clip off the leading $ or !

    for e in range(len(subStr)):
        chkSum ^= ord((subStr[e]))

    hexstr = str(hex(chkSum))[2:4].upper()
    if len(hexstr) == 2:
        return hexstr
    else:
        return '0'+hexstr


def joinNMEAstrs(payloadstr): #str -> str
    tempstr = '!AIVDM,1,1,,A,' + payloadstr + ',0'
    result = tempstr + '*' + nmeaChecksum(tempstr) + "\r\n"
    return result


def num2bin (num, bitWidth):
    # deal with 2's complement
    # thx to https://stackoverflow.com/questions/12946116/twos-complement-binary-in-python
    num = int(num)
    num &= (2 << bitWidth-1)-1 # mask
    formatStr = '{:0'+str(bitWidth)+'b}'
    return formatStr.format(int(num))


def string2bin (myString, i_width):
    enc=''
    for i in range (len(myString)):
        enc += num2bin(ord(myString[i].upper()), 6)
        
    return enc.ljust(i_width, '0')[:i_width]



mapping = "0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVW`abcdefghijklmnopqrstuvw"
   
   
def ais_message1 (i_mtype, i_repeat, i_mmsi, i_status, i_turn, i_speed, i_accuracy, i_lat, i_lon, i_course, 
            i_heading, i_second, i_maneuver, i_spare, i_raim, i_radio):
    bits = num2bin(i_mtype,6) + num2bin(i_repeat,2) + num2bin(i_mmsi, 30) + num2bin(i_status, 4) + \
        num2bin(int(4.733*math.sqrt(float(i_turn))), 8) + num2bin(i_speed*10, 10) + num2bin(i_accuracy, 1) + num2bin(int(600000*float(i_lon)), 28) + \
        num2bin(int(600000*float(i_lat)), 27) + num2bin(i_course*10, 12) + num2bin(i_heading, 9) + num2bin(i_second, 6) + \
        num2bin(i_maneuver, 2) + num2bin(i_spare, 3) + num2bin(i_raim, 1) + num2bin(i_radio, 19)
    #print ("type..r.mmsi..........................sta.turn....speed.....alon.........................lat........................course......heading..sec...m.sp.rradio..............")
    #print (bits)
    enc = ''
    while bits:
        n=int(bits[:6],2)
        enc = enc + mapping[n:n+1]
        bits = bits[6:]

    return '' + joinNMEAstrs(enc)
    

def ais_message5 (i_mtype, i_repeat, i_mmsi, i_version, i_imo, i_callsign, i_name, i_shiptype, i_to_bow, i_to_stern, i_to_port, i_to_stbd, 
            i_fixtype, i_eta_month, i_eta_day, i_eta_hour, i_eta_minute, i_draught, i_destination, i_dte, i_spare, i_filler):
    bits = num2bin(i_mtype, 6) + num2bin(i_repeat, 2) + num2bin(i_mmsi, 30) + num2bin(i_version, 2) + \
        num2bin(i_imo, 30) + string2bin(i_callsign, 42) + string2bin(i_name, 120) + num2bin(i_shiptype, 8) + \
        num2bin(i_to_bow, 9) + num2bin(i_to_stern, 9) + num2bin(i_to_port, 6) + num2bin(i_to_stbd, 6) + \
        num2bin(i_fixtype, 4) + num2bin(i_eta_month, 4) + num2bin(i_eta_day, 5) + num2bin(i_eta_hour, 5) + \
        num2bin(i_eta_minute, 6) + num2bin(i_draught, 8) + string2bin(i_destination, 120) + num2bin(i_dte, 1) + \
        num2bin(i_spare, 1) + num2bin(i_filler, 2)
    #print ("type..r.mmsi..........................v.imo...........................callsign..................................name..........................................................................................................stype...tobow....stern....port..stbd..fix.m...d....hour.min...draught.destination.............................................................................................................dsff")
    #print (bits)
    enc = ''
    while bits:
        n=int(bits[:6],2)
        enc = enc + mapping[n:n+1]
        bits = bits[6:]
        
    tempstr1 = '!AIVDM,2,1,3,A,' + enc[:59] + ',0'
    tempstr2 = '!AIVDM,2,2,3,A,' + enc[59:] + ',0'
    return  tempstr1 + '*' + nmeaChecksum(tempstr1) + "\r\n" + tempstr2 + '*' + nmeaChecksum(tempstr2) + "\r\n"
    # return '' + joinNMEAstrs(enc) 

    

def rmc_message(i_lat, i_lon, i_heading, i_speed):
    t_ns = 'N' if i_lat > 0 else 'S'
    t_ew = 'E' if i_lon > 0 else 'W'
    i_lat = abs(i_lat)
    i_lon = abs(i_lon)
    t_lat = "%02.f%07.4f" % (math.trunc(i_lat), 60*(i_lat-math.trunc(i_lat)))
    t_lon = "%03.f%07.4f" % (math.trunc(i_lon), 60*(i_lon-math.trunc(i_lon)))
    t_time = datetime.utcnow().strftime("%H%M%S");
    t_date = datetime.utcnow().strftime("%d%m%y");

    tempstr = '$GPRMC,%s,A,%s,%s,%s,%s,%s,%s,%s,,,A,C' % (t_time, t_lat, t_ns, t_lon, t_ew, i_speed, i_heading, t_date)
    result = tempstr + '*' + nmeaChecksum(tempstr) + "\r\n"
    return result

def gll_message(i_lat, i_lon, i_heading, i_speed):
    t_ns = 'N' if i_lat > 0 else 'S'
    t_ew = 'E' if i_lon > 0 else 'W'
    i_lat = abs(i_lat)
    i_lon = abs(i_lon)
    t_lat = "%02.f%07.4f" % (math.trunc(i_lat), 60*(i_lat-math.trunc(i_lat)))
    t_lon = "%03.f%07.4f" % (math.trunc(i_lon), 60*(i_lon-math.trunc(i_lon)))
    t_date = datetime.utcnow().strftime("%d%m%y");
    t_time = datetime.utcnow().strftime("%H%M%S");

    tempstr = '$GPGLL,%s,%s,%s,%s,%s,A,C' % (t_lat, t_ns, t_lon, t_ew, t_time)
    result = tempstr + '*' + nmeaChecksum(tempstr) + "\r\n"
    return result

def mwv_message(i_awa, i_aws):
    t_awa = "%03.0f" % (float(i_awa))
    t_aws = "%03.1f" % (float(i_aws))
    tempstr = "$IIMWV,%s,R,%s,N,A" % (t_awa, t_aws)
    result = tempstr + '*' + nmeaChecksum(tempstr) + "\r\n"
    return result

def vhw_message(i_hdm, i_stwn):
    t_hdm = "%03.0f" % (float(i_hdm))
    t_stwn = "%03.1f" % (float(i_stwn))
    tempstr = "$IIVHW,,,%s,M,%s,N,," % (t_hdm, t_stwn)
    result = tempstr + '*' + nmeaChecksum(tempstr) + "\r\n"
    return result


def hdm_message(i_hdm):
    t_hdm = "%03.1f" % (float(i_hdm))
    
    tempstr = "$KKHDM,%s,M" % (t_hdm)
    result = tempstr + '*' + nmeaChecksum(tempstr) + "\r\n"
    return result


def dbk_message(i_dbk):
    t_dbk = "%03.1f" % (float(i_dbk))
    
    tempstr = "$INDBK,,f,%s,M,,F" % (t_dbk)
    result = tempstr + '*' + nmeaChecksum(tempstr) + "\r\n"
    return result


class Simulation(object):

    boats = []
    ownBoat = []
    paused = False
    speedup = 60

    c=0 # progress counter
    
    def read_nmea_thread(self):
        while True:
            print ("Awaiting connection...")
            c,a = listensocket.accept()
            print ("Connection from: " + str(a) )
            while True:
                try:
                    m,x = c.recvfrom(1024)
                    if m:
                        first_line = m.decode().split("\r\n")[0]
                        line_elements = first_line.split(",")
                        if line_elements[0][3:] == "APB":
                            heading = float(line_elements[13])
                            print ("Set heading to " + str(heading))
                            self.ownBoat.heading = heading
                        else:
                            print (f"Unknown message '{str(first_line)}'")
                    else:
                        break;
                except Exception as e:
                    print ("exception: " + str(e))
                    pass
            print ("Disconnected")
        print ("Ending thread")


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
            self.twd = 0
            self.tws = 0
            self.twv = 0
            self.curs = 0
            self.curd = 0


        def show(self):
            if self.own == False:
                my_message = ais_message1 (1, 0, self.mmsi, self.status, 0, self.speed, 1, self.lat, self.lon, 
                    self.heading, self.heading, 0, self.maneuver, 0, 0, 0) + \
                    ais_message5 (i_mtype=5, i_repeat=1, i_mmsi=self.mmsi, i_version=0, i_imo=0, i_callsign="PB1234", i_name=self.name, \
                        i_shiptype=79, i_to_bow=100, i_to_stern=50, i_to_port=15, i_to_stbd=15, i_fixtype=3, i_eta_month=0, i_eta_day=0, \
                        i_eta_hour=24, i_eta_minute=60, i_draught=50, i_destination="Timbuktu", i_dte=1, i_spare=0, i_filler=0)
            else:
                # calculate apparent wind:
                #print ("self.speed = %3f  self.tws=%3f  self.twd=%3f  self.heading=%3f" % (self.speed, self.tws, self.twd, self.heading))
                twa = (((self.twd + random() * 10 - self.heading + 180) %360) - 180)/180*math.pi
                aws = math.sqrt(self.speed**2+self.tws**2 + 2 * self.speed*self.tws*math.cos(twa))
                try:
                    angle = math.acos((self.tws * math.cos(twa) + self.speed)/(math.sqrt(self.tws**2 + self.speed**2 + 2*self.tws*self.speed*math.cos(twa))))/math.pi*180
                except:
                    angle = 0
                if (twa < 0):
                    angle = -(angle)
                #print ("angle=" + str(angle))
                awa = (angle) % 360 
                depth = 4-(math.sin(time.time()/20)+1)**2;
                my_message = rmc_message (self.lat, self.lon, self.heading, self.speed) + \
                                gll_message(self.lat, self.lon, self.heading, self.speed) + \
                                mwv_message(awa, aws) + \
                                hdm_message(self.heading) + \
                                vhw_message(self.heading, self.speed) + \
                                dbk_message(depth)
            sys.stdout.write (my_message)    

            # TCP
            #sendsocket.sendall((my_message+"\r\n").encode('utf-8'))

            # UDP
            sendsocket.sendto((my_message).encode('utf-8'), ('<broadcast>', 10110))
            
        def move(self, speedup):
            elapsed = time.time() - self.last_move
            self.lat = self.lat + elapsed * self.speed/3600/60 * speedup * math.cos(self.heading/180*math.pi)
            self.lon = self.lon + elapsed * self.speed/3600/60 * speedup * math.sin(self.heading/180*math.pi) / math.cos(self.lat/180*math.pi)
            
            if self.own == True: # apply current only to own boat
                self.lat = self.lat + elapsed * self.curs/3600/60 * speedup * math.cos(self.curd/180*math.pi)
                self.lon = self.lon + elapsed * self.curs/3600/60 * speedup * math.sin(self.curd/180*math.pi) / math.cos(self.lat/180*math.pi)

            self.last_move = time.time()


    def loadBoats(self, filename):

        print("--- Loading boats from %s" % filename)
        self.boats = []

        try:
            tree = ET.parse(filename)
        except:
            print ("*** Could not open file %s. Consider downloading example file ais_simulation.gpx from github." % filename)
            return False

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
            newBoat=self.Boat(mmsi, name, float(lat), float(lon), float(heading), float(speed), status, 0, own)
            self.boats.append(newBoat)
            if own:
                global nmea_thread
                self.ownBoat = newBoat
                nmea_thread = threading.Thread(target = self.read_nmea_thread, daemon=True)
                nmea_thread.start()
                
        return True


    def processBoats(self):
        if self.paused == False:
            self.moveBoats()
        else:
            self.showBoats()
        self.timer = threading.Timer(1, self.processBoats)
        self.timer.start()
    


    def moveBoats(self):
        for boat in self.boats:
            boat.move(self.speedup)
            boat.show()
            self.c+=1
        print (self.c)


    def showBoats(self):
        for boat in self.boats:
            boat.show()


    def startBoats(self, event):
        filename=event.GetEventObject().filename
        self.loadBoats(filename)

        try:
            self.timer.cancel()
        except:
            pass
        if self.boats:
            print ("--- Starting simulation")
            self.timer = threading.Timer(1, self.processBoats)
            self.timer.start()
            self.paused = False
        else:
            print ("*** No boats")


    def stopBoats(self, event):
        try:
            self.timer.cancel()
            print ("--- Stopping simulation, stop sending NMEA messages")
        except:
            pass


    def pauseBoats(self, event):
        print ("--- Pausing simulation; keep on sending NMEA messages")
        self.paused = True


    def resumeBoats(self, event):
        print ("--- Resuming simulation")
        for boat in self.boats:
            boat.last_move = time.time()
        self.paused = False


    def steerBoat(self, event):
        steerValue = event.GetEventObject().steerValue
        print (steerValue)
        self.ownBoat.heading = self.ownBoat.heading + steerValue

    def getHeading(self):
        return str(self.ownBoat.heading)

    def setTrueWind(self, event):
        self.ownBoat.twd = float(event.GetEventObject().twd)
        self.ownBoat.tws = float(event.GetEventObject().tws)
        self.ownBoat.twv = float(event.GetEventObject().twv)

    def setTrueCurrent(self, event):
        self.ownBoat.curd = float(event.GetEventObject().curd)
        self.ownBoat.curs = float(event.GetEventObject().curs)
        self.ownBoat.curv = float(event.GetEventObject().curv)
        
    def setSpeedup(self, speedup):
        self.speedup = speedup
        
    def wrapup(self):
        print ("--- Closing UDP socket")
        sendsocket.close()
        #listensocket.close()

#simulation.moveBoats()
