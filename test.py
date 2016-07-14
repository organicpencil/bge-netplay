import bge
import collections

from netplay import bitstring, packer, component


"""
def define_tables():
    ### Need to call this before gameplay starts
    ### Needs a separate function too, otherwise it gets defined on component load
    tabledef = packer.TableDef('PlayerSetup')
    # uint16 id is required by netplay for every NetComponent
    tabledef.define('uint16', 'id')
    tabledef.define('json', 'name', 'unnamed')
    tabledef.define('float', 'x', 0.0)
    tabledef.define('float', 'y', 0.0)
    tabledef.define('float', 'z', 0.0)
    tabledef.define('float', 'pitch', 0.0)
    tabledef.define('float', 'yaw', 0.0)
    tabledef.define('uint8', 'input', 0)
    # Netplay needs this on tables used to spawn components
    tabledef.component = Player

    tabledef = packer.TableDef('Position')
    # Table name also determines the function to call
    tabledef.define('uint16', 'id')
    tabledef.define('float', 'x', 0.0)
    tabledef.define('float', 'y', 0.0)
    tabledef.define('float', 'z', 0.0)


class Player(component.NetComponent):
    obj = 'Cube'  # Object that gets spawned at component init

    def start(self):
        # Called on both client and server before start_server and PlayerSetup
        self.cam_empty = self.owner.children['cam_empty']
        self.keystate = bitstring.BitArray(bin='00000000')

    def start_server(self):
        self.playername = "unnamed"

    def PlayerSetup(self, table):
        # When a table is received, it will call the function that matches
        # the table name.  In this case PlayerSetup.

        self.net_id = table.get('id')
        self.playername = table.get('name')

        pos = [table.get('x'), table.get('y'), table.get('z')]
        self.owner.worldPosition = pos

        rot = self.cam_empty.localOrientation.to_euler()
        rot[0] = table.get('pitch')
        self.cam_empty.localOrientation = rot

        rot = self.owner.worldOrientation.to_euler()
        rot[2] = table.get('yaw')
        self.owner.worldOrientation = rot

    def serialize(self):
        # Called when the object is first created and when new clients connect
        table = packer.Table('PlayerSetup')

        # Netplay needs 'id' in the component state table
        table.set('id', self.net_id)

        # Everything else can be whatever
        table.set('name', self.playername)

        pos = self.owner.worldPosition
        table.set('x', pos[0])
        table.set('y', pos[1])
        table.set('z', pos[2])

        table.set('pitch', self.cam_empty.localOrientation.to_euler()[0])
        table.set('yaw', self.owner.worldOrientation.to_euler()[2])

        table.set('input', self.keystate.int)
        #self.keystate.set(1, (0, 4, 5))

        return packer.to_bytes(table)

    def update(self):
        # Physics stuff or whatever, happens on both client and server
        return

    def update_client(self):
        # Client-only
        if self.permission:
            # Process input
            None

    def update_server(self):
        # Server only
        # For now we're just gonna brute-force all clients with position
        pos = self.owner.worldPosition
        table = packer.Table('Position')
        table.set('id', self.net_id)
        table.set('x', pos[0])
        table.set('y', pos[1])
        table.set('z', pos[2])

        buff = packer.to_bytes(table)

        net = bge.logic.netplay
        for c in net.clients:
            if c is not None:
                # Queues for sending
                c.send_unreliable(buff)

    def Position(self, table):
        # When a table is received, it will call the function that matches
        # the table name.  In this case Position.

        pos = [table.get('x'), table.get('y'), table.get('z')]
        self.owner.worldPosition = pos
"""


def register_player(cont):
    owner = cont.owner

    p = owner.get('_component', None)
    if p is None:
        if not bge.logic.netplay.server:
            owner.endObject()
            return

        owner['_component'] = component.NetComponent(owner)