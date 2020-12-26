import socket
import sys
import math
import time
import xml.etree.ElementTree as ET
import threading
from datetime import datetime


#TCP
#sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#server_address = ('localhost', 20220)
#sock.connect(server_address)

#UDP
broadcastsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
broadcastsocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
#sock.settimeout(0.2)
#sock.bind(("", 10110))
print ("--- Broadcasting NMEA messges to UDP:10110")

listensocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listensocket.bind(("", 10111))
listensocket.listen(1)
print ("--- Listening to NMEA messages at TCP:10110")




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


def joinNMEAstrs(payloadstr): #str -> str
    tempstr = '!AIVDM,1,1,,A,' + payloadstr + ',0'
    result = tempstr + '*' + nmeaChecksum(tempstr) + "\r\n"
    return result


def ais_message (i_mtype, i_repeat, i_mmsi, i_status, i_turn, i_speed, i_accuracy, i_lat, i_lon, i_course, 
            i_heading, i_second, i_maneuver, i_spare, i_raim, i_radio):
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
    #print ("type..r.mmsi..........................sta.turn....speed.....alon.........................lat........................course......heading..sec...m.sp.rradio..............")
    #print (bits)
    enc = ''
    mapping = "0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVW`abcdefghijklmnopqrstuvw"
    while bits:
        n=int(bits[:6],2)
        enc = enc + mapping[n:n+1]
        bits = bits[6:]

    return '' + joinNMEAstrs(enc)
    

def rmc_message(i_lat, i_lon, i_heading, i_speed):
    t_lat = "%02.f%07.4f" % (math.trunc(i_lat), 60*(i_lat-math.trunc(i_lat)))
    t_lon = "%03.f%07.4f" % (math.trunc(i_lon), 60*(i_lon-math.trunc(i_lon)))
    t_time = datetime.now().strftime("%H%M%S");
    t_date = datetime.now().strftime("%d%m%y");

    tempstr = '$GPRMC,%s,A,%s,N,%s,E,%s,%s,%s,,,A,C' % (t_time, t_lat, t_lon, i_speed, i_heading, t_date)
    result = tempstr + '*' + nmeaChecksum(tempstr) + "\r\n"
    return result

def gll_message(i_lat, i_lon, i_heading, i_speed):
    t_lat = "%02.f%07.4f" % (math.trunc(i_lat), 60*(i_lat-math.trunc(i_lat)))
    t_lon = "%03.f%07.4f" % (math.trunc(i_lon), 60*(i_lon-math.trunc(i_lon)))
    t_date = datetime.now().strftime("%d%m%y");
    t_time = datetime.now().strftime("%H%M%S");

    tempstr = '$GPGLL,%s,N,%s,E,%s,A,C' % (t_lat, t_lon, t_time)
    result = tempstr + '*' + nmeaChecksum(tempstr) + "\r\n"
    return result

def mwv_message(i_awa, i_aws):
    t_awa = "%03.0f" % (float(i_awa))
    t_aws = "%02.f" % (float(i_aws))
    tempstr = "$IIMWV,%s,R,%s,N,A" % (t_awa, t_aws)
    result = tempstr + '*' + nmeaChecksum(tempstr) + "\r\n"
    return result

def vhw_message(i_hdm, i_stwn):
    t_hdm = "%03.0f" % (float(i_hdm))
    t_hdt = "%03.0f" % (float(i_hdm))
    t_stwn = "%02.f" % (float(i_stwn))
    t_stwk = "%02.f" % (float(i_stwn))
    tempstr = "$IIVHW,%s,T,%s,M,%s,N,%s,K" % (t_hdm, t_hdt, t_stwn, t_stwk)
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
                            heading = float(line_elements[11])
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
                my_message = ais_message (1, 0, self.mmsi, self.status, 0, self.speed, 1, self.lat, self.lon, 
                    self.heading, self.heading, 0, self.maneuver, 0, 0, 0)
            else:
                # calcucate apparent wind:
                #print ("self.speed = %3f  self.tws=%3f  self.twd=%3f  self.heading=%3f" % (self.speed, self.tws, self.twd, self.heading))
                aws = math.sqrt(self.speed**2+self.tws**2 - 2 * self.speed*self.tws*math.cos((self.heading-self.twd-180)/180*math.pi))
                #print ("aws = " + str(aws))
                angle = math.asin(math.sin((self.heading-self.twd - 180)/180*math.pi)/aws*self.tws)/math.pi*180
                #print ("angle=" + str(angle))
                #if 90 < (self.heading - 180 - self.twd) % 360 < 270:
                    #angle = 180 - angle
                    #print ("angle=" + str(angle))
                awa = (angle) % 360 
                my_message = rmc_message (self.lat, self.lon, self.heading, self.speed) + \
                                gll_message(self.lat, self.lon, self.heading, self.speed) + \
                                mwv_message(awa, aws) + \
                                vhw_message(self.heading, self.speed)
            sys.stdout.write (my_message)                                                              

            # TCP
            #sock.sendall((my_message+"\r\n").encode('utf-8'))

            # UDP
            broadcastsocket.sendto((my_message).encode('utf-8'), ('<broadcast>', 10110))
            
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
            newBoat=self.Boat(mmsi, name, float(lat), float(lon), float(heading), float(speed), 0, 0, own)
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
        broadcastsocket.close()
        #listensocket.close()

#simulation.moveBoats()
