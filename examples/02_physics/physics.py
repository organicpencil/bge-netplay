import bge
import mathutils
from netplay import packer, component


def define_tables():
    if 'tables' in bge.logic.globalDict:
        return
    bge.logic.globalDict['tables'] = 0

    tabledef = packer.TableDef('CubeSetup')
    tabledef.define('uint16', 'id')
    tabledef.define('float', 'pos_x')
    tabledef.define('float', 'pos_y')
    tabledef.define('float', 'pos_z')
    tabledef.define('float', 'rot_x')
    tabledef.define('float', 'rot_y')
    tabledef.define('float', 'rot_z')
    tabledef.define('float', 'rot_w')
    tabledef.component = Cube

    # Silly workaround to prevent cubes from spawning on clients
    if bge.logic.netplay.server:
        bge.logic.getCurrentScene().objects['Empty'].state = 2


class Cube(component.NetComponent):
    obj = 'Cube'

    def CubeSetup(self, table):
        get = table.get
        pos = (get('pos_x'), get('pos_y'), get('pos_z'))
        rot = mathutils.Quaternion((get('rot_x'),
                                    get('rot_y'),
                                    get('rot_z'),
                                    get('rot_w')))

        self.owner.worldPosition = pos
        self.owner.worldOrientation = rot

    def serialize(self):
        table = packer.Table('CubeSetup')
        pos = self.owner.worldPosition
        rot = self.owner.worldOrientation.to_quaternion()

        table.set('id', self.net_id)
        table.set('pos_x', pos[0])
        table.set('pos_y', pos[1])
        table.set('pos_z', pos[2])
        table.set('rot_x', rot[0])
        table.set('rot_y', rot[1])
        table.set('rot_z', rot[2])
        table.set('rot_w', rot[3])

        return packer.to_bytes(table)

    def update_client(self):
        return

    def update_server(self):
        # Brute force position and rotation each frame
        buff = self.serialize()
        net = bge.logic.netplay
        for c in net.clients:
            if c is not None:
                # Queues for sending
                c.send_reliable(buff)


def register_cube(cont):
    owner = cont.owner
    if 'init' in owner:
        return

    owner['init'] = True
    Cube(owner)