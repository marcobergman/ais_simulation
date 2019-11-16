# ais_simulation
Simulates moving AIS targets by creating NMEA AIVD messages and sending them off by TCP

prerequisites:
- python 2 or 3  installed with wxpython (install with pip install -U wxPython)
- some nmea listener listening on localhost tcp/20220

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
port=20220
direction=both
strict=no
```
![example](https://github.com/marcobergman/ais_simulation/blob/master/ais_simulator.png)
