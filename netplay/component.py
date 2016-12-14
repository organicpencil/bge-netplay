import logging
import bge
import mathutils
from . import packer


class GameObject:
    obj = None

    def __init__(self, owner, ref=None):
        net = bge.logic.netplay
        # Weirdass workaround for network-enabled objects in the editor
        if owner is None:
            if self.obj is not None:
                if ref is None:
                    owner = bge.logic.getCurrentScene().addObject(self.obj)
                else:
                    owner = bge.logic.getCurrentScene().addObject(self.obj, ref)
                owner['_component'] = self
        elif not net.server and not '_component' in owner:
            logging.warning("{}: You shouldn't directly add network-enabled objects on clients.".format(owner.name))
            owner.endObject()
            return

        self.owner = owner

        self.start()

        if net.server:
            # On the server we spawn components by placing objects in the editor
            # or spawning with scene.addObject
            self.permissions = []
            net.assign_component_id(self)
            self.start_server()

            buff = self.serialize()
            for c in net.clients:
                if c is not None:
                    c.send_reliable(buff)

        else:
            # Clients can only get new network objects from the server
            self.permission = False
            # Setup function defined by serialize will run after construction
            self.start_client()

    def give_permission(self, peer_id):
        if peer_id in self.permissions:
            logging.warning('Client already has access to this component')
            return

        self.permissions.append(peer_id)

        # Notify the client
        table = packer.Table('_permission')
        table.set('id', self.net_id)
        table.set('state', 1)

        buff = packer.to_bytes(table)
        bge.logic.netplay.clients[peer_id].send_reliable(buff)

    def takePermission(self, peer_id):
        if peer_id not in self.permissions:
            # Didn't have permission
            logging.warning('Client did not have access to this component')
            return

        self.permissions.remove(peer_id)

        # Notify the client
        table = packer.Table('_permission')
        table.set('id', self.net_id)
        table.set('state', 0)

        buff = packer.to_bytes(table)
        bge.logic.netplay.clients[peer_id].send_reliable(buff)

    def _permission(self, table):
        if bge.logic.netplay.server:
            logging.warning('Permission flag is not used on the server')
            return

        self.permission = bool(table.get('state'))

    def _destroy(self, table):
        host = bge.logic.netplay
        if host.server:
            # Lets you call _destroy directly on server
            # Also allows clients with permission to self-destruct their object
            buff = packer.to_bytes(table)
            for c in host.clients:
                if c is not None:
                    c.send_reliable(buff)

        if self.owner is not None:
            self.owner.endObject()

    def start(self):
        """
        Called on both client and server
        """
        return

    def start_server(self):
        return

    def start_client(self):
        return

    def update(self):
        """
        Called before update_client and update_server
        """
        return

    def update_client(self):
        return

    def update_server(self):
        return

    def serialize(self):
        # Runs on server when object is spawned or client connects
        # See builtin_tables.py
        table = packer.Table('_GameObject')
        table['id'] = self.net_id  # Netplay always requires an ID

        pos = self.owner.worldPosition
        table['pos_x'] = pos[0]
        table['pos_y'] = pos[1]
        table['pos_z'] = pos[2]

        rot = self.owner.worldOrientation.to_quaternion()
        table['rot_x'] = rot[0]
        table['rot_y'] = rot[1]
        table['rot_z'] = rot[2]
        table['rot_w'] = rot[3]

        return packer.to_bytes(table)

    def deserialize(self, table):
        # Runs on client when object is spawned
        pos = mathutils.Vector((table['pos_x'], table['pos_y'], table['pos_z']))
        rot = mathutils.Quaternion((table['rot_x'], table['rot_y'],
                                    table['rot_z'], table['rot_w']))

        self.owner.worldPosition = pos
        self.owner.worldOrientation = rot


class RigidGameObject(GameObject):
    # Not totally functional
    obj = None

    def serialize(self):
        owner = self.owner
        table = packer.Table('_RigidGameObject')
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