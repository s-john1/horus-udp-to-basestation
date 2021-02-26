#!/usr/bin/env python

"""
Horus UDP to BaseStation Converter

This program will receive Horus UDP packets and output SBS BaseStation messages, allowing
positions of radiosondes to be plotted with Virtual Radar Server.

This program assigns each radiosonde a Mode-S code (unique identifier within BaseStation messages)
to allow programs receiving the BaseStation messages to be able to distinguish between radiosondes. This data is stored
in the 'icaos.json' file, allowing the program to be restarted without giving changing the matched Mode-S code of a
radiosonde.

This code was based on the examples provided within radiosonde_auto_rx
(https://github.com/projecthorus/radiosonde_auto_rx/)
"""

import datetime
import json
import socket
import time

import config  # Config file
from listener import UDPListener


class HorusUDPToBasestation(object):
    TIMESTAMP_FORMAT = "%Y/%m/%d %H:%M:%S"

    def __init__(self):
        self._sondes = {}

        self._s = None

        self.connect_output()

        # Instantiate the UDP listener.
        udp_rx = UDPListener(
            port=config.HORUS_UDP_PORT,
            callback=self.handle_sonde_message
        )
        # and start it
        udp_rx.start()

        # From here, everything happens in the callback function above.
        try:
            while True:
                time.sleep(1)

        # Catch CTRL+C nicely.
        except KeyboardInterrupt:
            # Close UDP listener.
            udp_rx.close()
            self.disconnect_output()
            print("Closing.")

    def connect_output(self):
        # Connect to basestation output
        connected = False
        while not connected:
            try:
                print("Connecting")
                self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._s.connect((config.OUTPUT_IP, config.OUTPUT_PORT))
                connected = True
                print('Connection successful!\n')

            except socket.error as exception:
                print('Unable to connect to socket: {}\n'.format(exception))
                time.sleep(5)

    def disconnect_output(self):
        # Disconnect from basestation output
        print("Disconnecting")
        self._s.close()
        print("Disconnected")

    def send_output(self, message):
        data = (message + "\n").encode()

        try:
            self._s.send(data)
        except socket.error as exception:
            print("Error outputting basestation to server {}".format(exception))
            self.disconnect_output()
            self.connect_output()

            print("Retrying to send last message")
            try:
                self._s.send(data)
            except socket.error as exception:
                print("Couldn't send after reconnect {}".format(exception))

    def handle_sonde_message(self, packet):
        message_time = datetime.datetime.now()

        # Basestation message time fields
        timestamp1 = message_time.strftime("%Y/%m/%d")
        timestamp2 = message_time.strftime("%H:%M:%S.000")

        # Position fields
        callsign = packet['callsign']
        icao = self.find_icao(callsign, message_time)
        latitude = packet['latitude']
        longitude = packet['longitude']
        altitude = int(packet['altitude'] * 3.281)  # convert m to ft
        speed = packet['speed'] / 1.852  # convert kph to knots
        heading = packet['heading']

        # Add sonde to sonde dict if it doesn't already exist
        if callsign not in self._sondes:
            self._sondes[callsign] = Sonde(callsign)

        vert_speed = self._sondes[callsign].calculate_ascent_rate(altitude, message_time)

        if vert_speed is None:
            vert_speed = ""

        # Reset following values ready for the next sonde message
        self._sondes[callsign].last_alt = altitude
        self._sondes[callsign].last_message_time = message_time

        # Output basestation
        basestation = "MSG,3,,," + icao + ",," + timestamp1 + "," + timestamp2 + "," + timestamp1 + "," + timestamp2 \
                      + "," + str(callsign) + "," + str(altitude) + "," + str(speed) + "," + str(heading) + "," \
                      + str(latitude) + "," + str(longitude) + "," + str(vert_speed) + ",,,,,"
        self.send_output(basestation)
        print(basestation)

    def find_icao(self, callsign, timestamp):

        with open(config.ICAO_FILE, 'r+') as file:
            # Open file
            try:
                icaos = json.loads(file.read())
            except ValueError:
                print("Cannot decode JSON")
                icaos = {}

            # Use icao if already stored
            if callsign in icaos:
                icao = icaos[callsign]['icao']
            else:
                # Remove old icaos
                if len(icaos) >= config.ICAO_LIMIT:
                    # Sort icaos to retrieve the key of the sonde to remove
                    sorted_icaos = sorted(icaos.items(),
                                          key=lambda x: datetime.datetime.strptime(x[1]['timestamp'],
                                                                                   self.TIMESTAMP_FORMAT))
                    key = sorted_icaos[0][0]

                    # Remember icao to be used
                    icao = icaos[key]['icao']

                    # Remove previous sonde from json file
                    icaos.pop(key)
                    print("Removed", key, "from JSON file")

                # Assign new icao
                else:
                    icao = "BD" + str(len(icaos)).zfill(4)
                    print("Added new callsign to JSON file", callsign)

            # Update dictionary with icao record
            icaos[callsign] = {}
            icaos[callsign]['icao'] = icao
            icaos[callsign]['timestamp'] = timestamp.strftime(self.TIMESTAMP_FORMAT)

            # Clear current file and write current icaos to it
            file.seek(0)
            file.truncate()
            file.write(json.dumps(icaos))

            return icao


class Sonde(object):

    def __init__(self, callsign):
        self._callsign = callsign

        self.last_message_time = None

        self.last_alt = None
        self._ascent_rates = []

    def calculate_ascent_rate(self, altitude, current_time):
        # Remove old ascent values if they exist
        if len(self._ascent_rates) == 6:
            self._ascent_rates.pop(0)

        # Calculate average ascent rate
        if self.last_alt is not None and self.last_message_time is not None:
            self._ascent_rates.append(
                int((altitude - self.last_alt) / ((current_time - self.last_message_time).total_seconds() / 60)))
            ascent_rate = sum(self._ascent_rates) / len(self._ascent_rates)
        else:
            ascent_rate = None

        return ascent_rate


if __name__ == "__main__":
    # Instantiate UDP to basestation
    udp_to_bs = HorusUDPToBasestation()
