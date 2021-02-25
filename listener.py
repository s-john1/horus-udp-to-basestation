import json
import socket
import traceback
from threading import Thread


class UDPListener(object):
    ''' UDP Broadcast Packet Listener 
    Listens for Horus UDP broadcast packets, and passes them onto a callback function
    '''

    def __init__(self,
                 callback=None,
                 summary_callback=None,
                 gps_callback=None,
                 port=55673):

        self.udp_port = port
        self.callback = callback

        self.listener_thread = None
        self.s = None
        self.udp_listener_running = False

    def handle_udp_packet(self, packet):
        ''' Process a received UDP packet '''
        try:
            # The packet should contain a JSON blob. Attempt to parse it in.
            packet_dict = json.loads(packet)

            # This example only passes on Payload Summary packets, which have the type 'PAYLOAD_SUMMARY'
            # For more information on other packet types that are used, refer to:
            # https://github.com/projecthorus/horus_utils/wiki/5.-UDP-Broadcast-Messages
            if packet_dict['type'] == 'PAYLOAD_SUMMARY':
                if self.callback is not None:
                    self.callback(packet_dict)

        except Exception as e:
            print("Could not parse packet: %s" % str(e))
            traceback.print_exc()

    def udp_rx_thread(self):
        ''' Listen for Broadcast UDP packets '''

        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.settimeout(1)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except:
            pass
        self.s.bind(('', self.udp_port))
        print("Started UDP Listener Thread on port %d." % self.udp_port)
        self.udp_listener_running = True

        # Loop and continue to receive UDP packets.
        while self.udp_listener_running:
            try:
                # Block until a packet is received, or we timeout.
                m = self.s.recvfrom(1024)
            except socket.timeout:
                # Timeout! Continue around the loop...
                m = None
            except:
                # If we don't timeout then something has broken with the socket.
                traceback.print_exc()

            # If we hae packet data, handle it.
            if m != None:
                self.handle_udp_packet(m[0])

        print("Closing UDP Listener")
        self.s.close()

    def start(self):
        if self.listener_thread is None:
            self.listener_thread = Thread(target=self.udp_rx_thread)
            self.listener_thread.start()

    def close(self):
        self.udp_listener_running = False
        self.listener_thread.join()
