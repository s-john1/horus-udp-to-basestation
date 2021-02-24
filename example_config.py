#!/usr/bin/env python
#
# Horus UDP to BaseStation config
#

# Port for listening to incoming Horus UDP packets
HORUS_UDP_PORT = 55673

# Basestation output parameters
OUTPUT_IP = '192.168.1.100'
OUTPUT_PORT = 30000

# ICAO file parameters
ICAO_FILE = "icaos.json"  # File to store history of matches between ICAOs and radiosonde serial numbers
ICAO_LIMIT = 100  # Number of matches to keep stored in specified file
