import collections
import threading
import time

try:
    from . import enet


    # Wrapper stuff
    EVENT_TYPE_CONNECT = enet.EVENT_TYPE_CONNECT
    EVENT_TYPE_DISCONNECT = enet.EVENT_TYPE_DISCONNECT
    EVENT_TYPE_RECEIVE = enet.EVENT_TYPE_RECEIVE
except:
    enet = None


class Sleeper:

    def __init__(self, rate):
        self.loop_delta = 1.0 / rate
        self.current_time = self.target_time = time.time()

    def sleep(self):
        self.target_time += self.loop_delta
        sleep_time = self.target_time - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
        self.current_time = self.target_time = time.time()


class ENetWrapper:

    def __init__(self, server, interface='', port=54303, maxclients=10):

        self.threaded = False
        self.thread = None

        if server:
            self._host = enet.Host(enet.Address(interface, port),
                                   maxclients, 0, 0, 0)
        else:
            self._host = enet.Host(None, 1, 0, 0, 0)

        # When threading, events are stored here until joined
        self.pending_events = collections.deque()

        # More wrapper stuff
        #self.service = self._host.service

    def connect(self, server_ip, server_port):
        # For clients
        return self._host.connect(enet.Address(server_ip, server_port), 1)

    def send(self, peer, buff, reliable=True, channel=0):
        if reliable:
            flag = enet.PACKET_FLAG_RELIABLE
        else:
            flag = enet.PACKET_FLAG_UNSEQUENCED

        packet = enet.Packet(buff, flag)
        peer.send(channel, packet)

    def enableThreading(self, timeout=60.0):
        """
        Moves the network stuff to another thread, ideal for keeping your spot
        while loading the map.  Events will backlog until threading is
        automatically disabled by the next update call.

        Default timeout is 60 seconds.  Pass timeout=None for no timeout.
        """
        if self.threaded:
            print ("Already threaded")
            return False

        self.data = collections.deque()

        self.threaded = True
        self.thread_timeout = timeout
        self.thread = threading.Thread(target=self._update_thread)
        self.thread.start()
        return True

    def disableThreading(self):
        if not self.threaded:
            print ("Not currently threaded")
            return []

        self.threaded = False
        self.thread.join()
        self.thread = None

        pending_events = collections.deque(self.pending_events)
        self.pending_events.clear()
        return pending_events

    def _update_thread(self):
        # Thread
        if self.thread_timeout is not None:
            timeout = time.time() + self.thread_timeout

        sleeper = Sleeper(10)  # 10 tics/second
        while self.threaded:
            while True:
                event = self._host.service(0)
                if event.type != 0:
                    self.pending_events.append(event)
                else:
                    break

            sleeper.sleep()

            if self.thread_timeout is not None:
                if time.time() > timeout:
                    # Assume game crashed and didn't get to terminate the thread
                    return
