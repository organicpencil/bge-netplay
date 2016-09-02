from . import network, packer, builtin_tables
import bge
import logging

logging.basicConfig(level=logging.INFO)


class ServerHost:

    server = True

    def __init__(self, interface='', port=54303, version=0, maxclients=10):
        builtin_tables.define()

        # Handy for server lists
        self.port = port
        self.version = version
        self.maxclients = maxclients

        # Client ID == enet peer ID
        self.clients = [None] * maxclients
        self.components = [None] * 65535
        self.last_component = 0 # Saves some iteration while looping

        if network.enet is None:
            # No compatible network library was supplied
            self.network = None
            logging.warning('Enet not found.  Network play is disabled.')
        else:
            self.network = network.ENetWrapper(
                server=True, interface=interface, port=port,
                maxclients=maxclients)

            logging.info('Server started')

    def assignComponentID(self, component):
        i = 0
        for comp in self.components:
            if comp is None:
                self.components[i] = component
                component.net_id = i
                if i > self.last_component:
                    self.last_component = i
                return

            i += 1

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

        # Send everything!
        i = 0
        for comp in self.components:
            if i > self.last_component:
                break

            i += 1

            if comp is None:
                continue

            client.send_reliable(comp.serialize())

        # User-defined
        self.onConnect(peerID)

    def _removeClient(self, peerID):
        # Assumes peer was already disconnected
        if self.clients[peerID] is None:
            logging.error('Client was already removed')
            return

        self.clients[peerID] = None

        # User-defined
        self.onDisconnect(peerID)

    def _update_components(self):
        i = 0
        last = self.last_component
        for comp in self.components:
            if i > last:
                return

            i += 1

            if comp is None:
                continue

            comp.update()
            comp.update_server()

    def update(self):
        self._update_components()

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
                peerID = event.peer.incomingPeerID
                self._removeClient(peerID)

            elif event.type == network.EVENT_TYPE_RECEIVE:
                peerID = event.peer.incomingPeerID
                bufflist = packer.unjoin_buffers(event.packet.data)

                for buff in bufflist:
                    table = packer.to_table(buff)
                    table.source = peerID
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
        builtin_tables.define()

        self.server_ip = server_ip
        self.server_port = server_port

        self.connected = False
        self.network = network.ENetWrapper(server=False)
        self.serverPeer = self.network.connect(server_ip, server_port)

        self.components = [None] * 65535
        self.last_component = 0 # Saves some iteration while looping

        # Works the same, may as well re-use this code
        self._wrapper = _Client(self.serverPeer)

    def send_unreliable(self, buff):
        self._wrapper.send_unreliable(buff)

    def send_reliable(self, buff, channel=0):
        self._wrapper.send_reliable(buff, channel)

    def onConnect(self):
        print ("Connected")

    def onDisconnect(self):
        print ("Disconnected")

    def getPing(self):
        return self.serverPeer.roundTripTime

    def _update_components(self):
        i = 0
        last = self.last_component
        for comp in self.components:
            if i > last:
                return

            i += 1

            if comp is None:
                continue

            comp.update()
            comp.update_client()

    def update(self):
        self._update_components()

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
                    net_id = table.get('id')
                    component = self.components[net_id]

                    if component is None:
                        # Component doesn't exist.  Assume this is for creation.
                        comp = getattr(table._tabledef, 'component', None)
                        if comp is None:
                            logging.error('Missing expected component in table {}'.format(table.tableName()))
                        else:
                            component = comp(None)
                            component.net_id = net_id
                            self.components[net_id] = component
                            if net_id > self.last_component:
                                self.last_component = net_id

                            # Run the associated method (defined in serialize)
                            getattr(component, table.tableName())(table)
                    else:
                        # Run the associated method
                        getattr(component, table.tableName())(table)

        self.sendQueuedData()

    def sendQueuedData(self):
        c = self._wrapper
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