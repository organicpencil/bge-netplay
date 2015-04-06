from . import enetwrapper, Pack
import struct
enet = enetwrapper.enet


class Client:
    def __init__(self, game, server_ip='127.0.0.1', server_port=54303):

        self.game = game
        self.owner = game.owner
        self.server_ip = server_ip
        self.server_port = server_port

        self.connected = False
        self.network = enetwrapper.ENetWrapper(server=False)
        self.serverPeer = self.network.host.connect(
                enet.Address(server_ip, server_port), 1)

    def onConnect(self):
        print ("Connected")

    def onDisconnect(self):
        print ("Disconnected")

    def getPing(self):
        return self.serverPeer.roundTripTime

    def update(self, dt):
        backlog = []
        if self.network.threaded:
            backlog = self.network.disableThreading()

        cmgr = self.owner['Game'].systems['Component']

        while True:
            if len(backlog):
                event = backlog.popleft()
            else:
                event = self.network.host.service(0)

            if event.type == 0:
                break

            if event.type == enet.EVENT_TYPE_CONNECT:
                if self.connected:
                    print ("WARNING - already connected")
                    break

                self.connected = True
                self.onConnect()

            elif event.type == enet.EVENT_TYPE_DISCONNECT:
                if not self.connected:
                    print ("WARNING - already disconnected")
                    break

                print ("Disconnected from server")
                self.connected = False
                self.onDisconnect()

            elif event.type == enet.EVENT_TYPE_RECEIVE:
                #bdata = event.packet.data
                bdata_list = Pack.toDataList(event.packet.data)
                for bdata in bdata_list:
                    # Get the component and processor IDs
                    header = struct.unpack('!HH', bdata[:4])
                    c_id = header[0]
                    p_id = header[1]

                    component = cmgr.getComponent(c_id)
                    if component is not None:
                        # Strip the IDs and process
                        data = bdata[4:]
                        component._packer.process(p_id, data)

                    else:
                        print (("Invalid component ID %d" % c_id))

        # Get queued data and ship to server
        bdata_list = cmgr.getQueuedData()
        #"""
        reliable_data = []
        unreliable_data = []

        for bdata_packer in bdata_list:
            for bdata in bdata_packer:
                dp = bdata[0]
                d = bdata[1]
                reliable = dp.reliable

                if reliable:
                    reliable_data.append(d)
                else:
                    unreliable_data.append(d)

        if len(reliable_data):
            d = Pack.fromDataList(reliable_data)
            packet = self.network.createPacket(d, reliable=True)
            self.network.send(self.serverPeer, packet)

        if len(unreliable_data):
            d = Pack.fromDataList(unreliable_data)
            packet = self.network.createPacket(d, reliable=False)
            self.network.send(self.serverPeer, packet)

        """
        for bdata_packer in bdata_list:
            for bdata in bdata_packer:
                dp = bdata[0]
                d = bdata[1]
                reliable = dp.reliable

                packet = self.network.createPacket(d, reliable=reliable)
                self.network.send(self.serverPeer, packet)
        """