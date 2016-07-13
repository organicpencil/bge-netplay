from . import network, packer
import bge
import logging


class ServerHost:

    server = True

    def __init__(self, interface='', port=54303, version=0, maxclients=10):
        # Handy for server lists
        self.port = port
        self.version = version
        self.maxclients = maxclients

        # Client ID == enet peer ID
        self.clients = [None] * maxclients
        self.components = [None] * 65535

        if network is None:
            # No compatible network library was supplied
            self.network = None
            logging.warning('Enet not found.  Network play is disabled.')
        else:
            self.network = network.ENetWrapper(
                server=True, interface=interface, port=port,
                maxclients=maxclients)

            logging.info('Server started')

    def onConnect(self, peer_id):
        """
        Override this
        """
        return

    def onDisconnect(self, peer_id):
        """
        Override this
        """
        return

    def _addClient(self, peer):
        peerID = peer.incomingPeerID
        if self.clients[peerID] is not None:
            logging.error('Client ID in use: {}'.format(peerID))
            peer.reset()
            return

        client = _Client(peer)
        self.clients[peerID] = client

        self.onConnect(peerID)

    def _removeClient(self, peerID):
        # Assumes peer was already disconnected
        if self.clients[peerID] is None:
            logging.error('Client was already removed')
            return

        self.clients[peerID] = None
        self.onDisconnect(peerID)

    def update(self):
        if self.network is None:
            # Flush queued data
            return

        event_backlog = []
        if self.network.threaded:
            event_backlog = self.network.disableThreading()

        while True:
            if len(event_backlog):
                event = event_backlog.popleft()
            else:
                event = self.network._host.service(0)

            if event.type == 0:
                break

            elif event.type == network.EVENT_TYPE_CONNECT:
                logging.info("{} connecting".format(event.peer.address))
                ## TODO - check version
                self._addClient(event.peer)

            elif event.type == network.EVENT_TYPE_DISCONNECT:
                logging.info("{} disconnecting".format(event.peer.address))
                self._removeClient(event.peer)

            elif event.type == network.EVENT_TYPE_RECEIVE:
                peerID = event.peer.incomingPeerID
                bufflist = packer.unjoin_buffers(event.packet.data)

                for buff in bufflist:
                    table = packer.to_table(buff)
                    # Find the component by ID
                    component = self.components[table.get('id')]

                    if component is None:
                        logging.info('Received data for a non-existent component.  This is acceptable for unreliable data.')
                        continue

                    # Check for permissions
                    if peerID in component.permissions:
                        # Run the associated method
                        getattr(component, table.tableName())(table)
                    else:
                        logging.warning('Client does not have input permission')

        self.sendQueuedData()

    def sendQueuedData(self):
        if self.network is None:
            return

        for c in self.clients:
            if c is not None:
                if len(c.unreliable):
                    joined_buffers = packer.join_buffers(c.unreliable)
                    c.unreliable = []
                    self.network.send(c.peer, joined_buffers, reliable=False)

                channel = 0
                for ch in c.reliable:
                    if len(ch):
                        joined_buffers = packer.join_buffers(ch)
                        self.network.send(c.peer, joined_buffers, reliable=True,
                                          channel=channel)

                    channel += 1

                c.reliable = [[]] * c.channels


class _Client:

    def __init__(self, peer):
        self.peer = peer

        # Store queued data here
        self.unreliable = []

        # Pretty sure ENet supports 256 channels
        # But that's a lot of iteration.  Modify if here you need more.
        self.channels = 4
        self.reliable = [[]] * self.channels

    def send_unreliable(self, buff):
        self.unreliable.append(buff)

    def send_reliable(self, buff, channel=0):
        self.reliable[channel].append(buff)


class ClientHost:

    server = False

    def __init__(self, server_ip='127.0.0.1', server_port=54303, version=0):
        self.server_ip = server_ip
        self.server_port = server_port

        self.connected = False
        self.network = network.ENetWrapper(server=False)
        self.serverPeer = self.network.connect(server_ip, server_port)

        self.components = [None] * 65535

    def onConnect(self):
        print ("Connected")

    def onDisconnect(self):
        print ("Disconnected")

    def getPing(self):
        return self.serverPeer.roundTripTime

    def update(self):
        scene = bge.logic.getCurrentScene()

        event_backlog = []
        if self.network.threaded:
            event_backlog = self.network.disableThreading()

        while True:
            if len(event_backlog):
                event = event_backlog.popleft()
            else:
                event = self.network._host.service(0)

            if event.type == 0:
                break

            elif event.type == network.EVENT_TYPE_CONNECT:
                if self.connected:
                    logging.warning('Already connected')
                    continue

                self.connected = True
                self.onConnect()

            elif event.type == network.EVENT_TYPE_DISCONNECT:
                if not self.connected:
                    logging.warning('Already disconnected')
                    break

                self.connected = False
                self.onDisconnect()

            elif event.type == network.EVENT_TYPE_RECEIVE:
                bufflist = packer.unjoin_buffers(event.packet.data)
                for buff in bufflist:
                    table = packer.to_table(buff)
                    # Find the component by ID
                    component = self.components[table.get('id')]

                    if component is None:
                        # Component doesn't exist.  Assume this is for creation.
                        obj = getattr(table, 'obj', None)
                        if obj is None:
                            logging.warning('obj not defined')
                        else:
                            ob = scene.addObject(obj)
                            ob['_net_table'] = table
                    else:
                        # Run the associated method
                        getattr(component, table.tableName())(table)
