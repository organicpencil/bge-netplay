import bge
import collections

from netplay import bitstring, packer, component


### Need to call this before gameplay starts
### Needs a separate function too, otherwise it gets defined on component load
table = packer.TableDef('PlayerClientSetup')
# uint16 id is required by netplay for every NetComponent
table.define('uint16', 'id')
table.define('json', 'name', 'unnamed')
table.define('float', 'x', 0.0)
table.define('float', 'y', 0.0)
table.define('float', 'z', 0.0)
table.define('float', 'pitch', 0.0)
table.define('float', 'yaw', 0.0)
table.define('uint8', 'keystate', 0)

table = packer.TableDef('Position')
# Table name doubles as the function to call
table.define('uint16', 'id')
table.define('float', 'x', 0.0)
table.define('float', 'y', 0.0)
table.define('float', 'z', 0.0)

# Netplay needs the obj constant to spawn objects on clients
table.obj = 'Cube'

# You can store other constants if you want.  All 'private' variables are
# prefixed with '_' so you can use anything else.


class Player(component.NetComponent):
    args = collections.OrderedDict()

    def setup(self):
        # Called on both client and server before start_server and PlayerSetup
        self.cam_empty = self.object.children['cam_empty']
        self.keystate = bitstring.BitArray(bin='00000000')

    def start_server(self):
        return

    def PlayerClientSetup(self, table):
        self.net_id = table.get('id')
        self.playername = table.get('name')

        pos = [table.get('x'), table.get('y'), table.get('z')]
        self.object.worldPosition = pos

        rot = self.cam_empty.localOrientation.to_euler()
        rot[0] = table.get('pitch')
        self.cam_empty.localOrientation = rot

        rot = self.object.worldOrientation.to_euler()
        rot[2] = table.get('yaw')
        self.object.worldOrientation = rot

    def get_setup_data(self):
        # Called when the object is first created and when new clients connect
        table = packer.Table('PlayerClientSetup')

        # Netplay needs 'id' in the component state table
        table.set('id', self.net_id)

        # Everything else can be whatever
        table.set('name', self.playername)

        pos = self.object.worldPosition
        table.set('x', pos[0])
        table.set('y', pos[1])
        table.set('z', pos[2])

        table.set('pitch', self.cam_empty.localOrientation.to_euler()[0])
        table.set('yaw', self.object.worldOrientation.to_euler()[2])

        table.set('input', self.keystate.int)
        #self.keystate.set(1, (0, 4, 5))

        return packer.to_bytes(table)

    def update_both(self):
        # Physics stuff or whatever, happens on both client and server
        None

    def update_client(self):
        # Client-only
        if self.permission:
            # Process input
            None

    def update_server(self):
        # Server only
        # For now I'm gonna brute-force all clients with position
        pos = self.object.worldPosition
        table = packer.Table('Position')
        table.set('id', self.net_id)
        table.set('x', pos[0])
        table.set('y', pos[1])
        table.set('z', pos[2])

        buff = packer.to_bytes(table)

        net = bge.logic.netplay
        for c in net.clients:
            if c is not None:
                # Queues for aggregation + sending at the end of the frame
                c.send_unreliable(buff)

    def Position(self, table):
        # Some magic happens that calls this function when the 'Position'
        # table is received
        pos = [table.get('x'), table.get('y'), table.get('z')]
        self.object.worldPosition = pos