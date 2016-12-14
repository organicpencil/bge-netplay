import bge
import mathutils
from netplay import packer, component


def define_tables():
    if 'tables' in bge.logic.globalDict:
        return
    bge.logic.globalDict['tables'] = 0

    tabledef = packer.TableDef('CubeSetup', template='_RigidGameObject')
    tabledef.component = Cube

    # Silly workaround to prevent cubes from spawning on clients
    if bge.logic.netplay.server:
        bge.logic.getCurrentScene().objects['Empty'].state = 2


class Cube(component.GameObject):
    obj = 'Cube'

    def serialize(self):
        owner = self.owner
        table = packer.Table('CubeSetup')
        table['id'] = self.net_id

        pos = owner.worldPosition
        table['pos_x'] = pos[0]
        table['pos_y'] = pos[1]
        table['pos_z'] = pos[2]

        rot = owner.worldOrientation.to_quaternion()
        table['rot_x'] = rot[0]
        table['rot_y'] = rot[1]
        table['rot_z'] = rot[2]
        table['rot_w'] = rot[3]

        lv = owner.getLinearVelocity(False)
        table['lv_x'] = lv[0]
        table['lv_y'] = lv[1]
        table['lv_z'] = lv[2]

        av = owner.getAngularVelocity(False)
        table['av_x'] = av[0]
        table['av_y'] = av[1]
        table['av_z'] = av[2]

        return packer.to_bytes(table)

    def deserialize(self, table):
        pos = mathutils.Vector((table['pos_x'], table['pos_y'], table['pos_z']))
        rot = mathutils.Quaternion((table['rot_x'], table['rot_y'],
                                    table['rot_z'], table['rot_w']))
        lv = mathutils.Vector((table['lv_x'], table['lv_y'], table['lv_z']))
        av = mathutils.Vector((table['av_x'], table['av_y'], table['av_z']))

        owner = self.owner
        owner.worldPosition = pos
        owner.worldOrientation = rot
        owner.setLinearVelocity(lv, False)
        owner.setAngularVelocity(av, False)

    def update_client(self):
        return

    def CubeSetup(self, table):
        # We just brute force the setup table for now
        self.deserialize(table)

    def update_server(self):
        # Brute force everything each frame (TODO: Optimize)
        buff = self.serialize()
        net = bge.logic.netplay

        # This seriously needs an abstraction
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