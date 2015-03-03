import collections
import threading
import time
import json

from .enet import enet



"""
This wrapper serves to:
    -Abstract calls to send
    -Allow seamless switching to and from background threads
"""


class Clock:

    def __init__(self, rate):
        self.loop_delta = 1.0 / rate
        self.current_time = self.target_time = time.time()

    def tick(self):
        self.target_time += self.loop_delta
        sleep_time = self.target_time - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
        self.current_time = self.target_time = time.time()


class ENetWrapper:

    def __init__(self, server,
            maxclients=10, interface='', port=54303):

        self.threaded = False
        self.thread = None

        if server:
            self.host = enet.Host(enet.Address(interface, port),
                maxclients, 0, 0, 0)
        else:
            self.host = enet.Host(None, 1, 0, 0, 0)

        # When threading, events are stored here until joined
        self.pending_events = collections.deque()

    def send_old(self, peer, bdata, reliable=True, channel=0):
        if reliable:
            packet = enet.Packet(bdata, enet.PACKET_FLAG_RELIABLE)
        else:
            packet = enet.Packet(bdata, enet.PACKET_FLAG_UNSEQUENCED)

        peer.send(channel, packet)

    def createPacket(self, bdata, reliable=True):
        if reliable:
            return enet.Packet(bdata, enet.PACKET_FLAG_RELIABLE)
        else:
            return enet.Packet(bdata, enet.PACKET_FLAG_UNSEQUENCED)

    def send(self, peer, packet, channel=0):
        peer.send(channel, packet)

    def sendData(self, peer, data, packed=False, channel=0):
        if packed:
            bdata = data
        else:
            bdata = bytes(json.dumps(data), 'UTF-8')

        packet = self.createPacket(bdata)
        peer.send(channel, packet)

    def enableThreading(self):
        # Threading is only enabled during long blocking operations
        if self.threaded:
            print ("Already threaded")
            return False

        self.data = collections.deque()

        self.threaded = True
        self.thread = threading.Thread(target=self.update_thread)
        self.thread.start()
        return True

    def disableThreading(self):
        if not self.threaded:
            print ("Not currently threaded")
            return False

        self.threaded = False
        self.thread.join()
        self.thread = None

        pending_events = collections.deque(self.pending_events)
        self.pending_events.clear()
        return pending_events

    def update_thread(self):
        timeout = time.time() + 30.0
        clock = Clock(30)
        while self.threaded:
            event = self.host.service(0)
            if event.type != 0:
                self.pending_events.append(event)

            clock.tick()

            if time.time() > timeout:
                # Assume game crashed and didn't get to terminate the thread
                return
