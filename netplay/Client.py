from . import enetwrapper
import struct
enet = enetwrapper.enet


class Client:
    def __init__(self, game, server_ip='127.0.0.1', server_port=54303):

        self.game = game
        self.owner = game.owner
        self.server_ip = server_ip
        self.server_port = server_port

        self.connected = False
        self.network = ENetWrapper.ENetWrapper(server=False)
        self.serverPeer = self.network.host.connect(
                enet.Address(server_ip, server_port), 1)

    def onConnect(self):
        print ("Connected")

    def onDisconnect(self):
        print ("Disconnected")

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
                bdata = event.packet.data

                # Get the component and processor IDs
                header = struct.unpack('!HH', bdata[:4])
                c_id = header[0]
                p_id = header[1]

                component = cmgr.getComponent(c_id)
                if component is not None:
                    # Strip the IDs and process
                    data = bdata[4:]
                    component.packer.process(p_id, data)

                else:
                    print (("Invalid component ID %d" % c_id))

        # Get queued data and ship to server
        bdata_list = cmgr.getQueuedData()
        for bdata_packer in bdata_list:
            for bdata in bdata_packer:
                packet = self.network.createPacket(bdata)
                self.network.send(self.serverPeer, packet)
