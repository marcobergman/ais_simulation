# ais_simulation
Simulates moving AIS targets by creating NMEA AIVD messages and sending them off by TCP; tested both on raspberry linux and windows.

prerequisites:
- python 2 or 3 installed with wxpython (install with sudo apt-get install gtk+-3.0 libjpeg-dev zlib1g-dev; pip install -U wxPython)
- udp clients listening to broadcasts (0.0.0.0) on socket 10110

to install:
- git clone https://github.com/marcobergman/ais_simulation

to run:
- cd ais_simulation/
- python simulate_ais.py

hints:
- The default ais_simulation.gpx file was exported from OpenCPN. It should contain waypoints with HEADING, SPEED, and MMSI name=value pairs in the description field; see the examples. The waypoint named AIS-OWN is the waypoint that is used for your own boat.

- For a simple nmea listener, install kplex and configure with this file; direct your plotter to this socket 
```
#/etc/kplex.conf
[tcp]
mode=server
port=30330
direction=both
strict=no
```
- create windows executable with pyinstaller --onefile simulate_ais.py --distpath .

![example](https://github.com/marcobergman/ais_simulation/blob/master/ais_simulator.png)

# wind simulation
The script allows setting a true wind direction, and converts this in apparent wind data sent off in NMEA messages. This facilitates off-boat testing of e.g. dashboard and tactics plugins. Note: third field is supposed to be 'variance', but not implemented yet. Calculation of wind is not always correct - have been struggeling with quadrant ambiguity.

# track simulation
The 'own boat' will normally follow the heading initially set in the waypoint, and manually adjusted by the direction arrows. If NMEA APB sentences are sent to TCP/20220, the heading will be taken from 'heading to steer to waypoint' field instead. This simulates a boat equipped with an autopilot. Linked to opencpn, this facilitates testing of various track following algorithms. For these purposes,  water current direction and speed has also been made available, adjusting the boat movements accordingly.

![example](https://github.com/marcobergman/ais_simulation/blob/master/autopilot_tester.png)

