import math
import mathutils
import time
import bge
from netplay import Component, RigidComponent, Pack


class Crate(RigidComponent):
    def __init__(self, mgr, net_id):
        RigidComponent.__init__(self, mgr, net_id)
        self.obj = 'crate'


class Player(Component):
    def _register(self):
        # Attributes are used for spawning the object on other clients
        self.register_attribute('username', Pack.STRING, "")
        self.register_attribute('pos_x', Pack.FLOAT, 0.0)
        self.register_attribute('pos_y', Pack.FLOAT, 0.0)
        self.register_attribute('pos_z', Pack.FLOAT, 0.0)
        self.register_attribute('rot_x', Pack.FLOAT, 0.0)
        self.register_attribute('rot_z', Pack.FLOAT, 0.0)

        # Up to 32 inputs can be registered.
        # This merely abstracts a built-in RPC
        self.register_input('forward')
        self.register_input('back')
        self.register_input('left')
        self.register_input('right')
        self.register_input('jump')
        self.register_input('primary')

        self.RPC_Client('position', self.setPosition,
                [Pack.FLOAT, Pack.FLOAT, Pack.FLOAT], reliable=False)

        # Rotation constantly updates while moving mouse
        self.RPC_Server('send_rotation', self.server_setRotation,
                [Pack.FLOAT, Pack.FLOAT], reliable=False)
        self.RPC_Client('recv_rotation', self.setRotation,
                [Pack.FLOAT, Pack.FLOAT], reliable=False)

        """
        # Periodically send position to ensure clients are in sync
        # Signalled server-side
        self.register_rpc('position', self.setPosition,
                [Pack.FLOAT, Pack.FLOAT, Pack.FLOAT], reliable=False)

        # Re-send rotation whenever it changes, at a max rate of 4 per second
        # Signalled only on the controlling client
        self.register_rpc('rotation', self.setRotation,
                [Pack.SHORT, Pack.SHORT], reliable=False)
        """

    def _setup(self):
        # Runs when the object is spawned
        attr = self.getAttribute
        owner = self.mgr.owner

        ob = owner.scene.addObject('player', owner)
        ob.worldPosition = [attr('pos_x'), attr('pos_y'), attr('pos_z')]

        ob['component'] = self
        self.ob = ob
        self.ob_camera_armature = ob.children['player_camera_armature']
        self.ob_camera = self.ob_camera_armature.children['player_camera']
        self.aiming = False

        self.update_timer = self.update_timer_max = 6

        self.last_pos = mathutils.Vector((attr('pos_x'), attr('pos_y'),
                attr('pos_z')))

        self.last_rot = mathutils.Euler((attr('rot_x'), 0.0, attr('rot_z')))

        self.new_pos = mathutils.Vector((attr('pos_x'), attr('pos_y'),
                attr('pos_z')))

        self.new_rot = mathutils.Euler((attr('rot_x'), 0.0, attr('rot_z')))

    def _update_attributes(self):
        # Runs on the server when new clients need information
        # Only need to update attributes that could have changed since creation
        # For example position but not playername
        pos = self.ob.worldPosition
        self.setAttribute('pos_x', pos[0])
        self.setAttribute('pos_y', pos[1])
        self.setAttribute('pos_z', pos[2])

        rot = self.ob_camera_armature.worldOrientation.to_euler()
        self.setAttribute('rot_x', rot[0])
        self.setAttribute('rot_z', rot[2])

    def setPosition(self, data):
        self.new_pos[0] = data[0]
        self.new_pos[1] = data[1]
        self.new_pos[2] = data[2]

        """
        self.new_rot[0] = data[3]
        self.new_rot[2] = data[4]
        """

    def setRotation(self, data):
        x = data[0]
        z = data[1]

        prot = mathutils.Euler((0.0, 0.0, z))
        crot = mathutils.Euler((x, 0.0, z))

        self.ob.worldOrientation = prot
        self.ob_camera_armature.worldOrientation = crot
        """

        ### Left/Right rotation
        # applyRotation screws up momentum, don't use it on dynamic objects
        ob = self.ob
        cam = self.ob_camera_armature

        rot = ob.worldOrientation.to_euler()
        rot[2] += z
        ob.worldOrientation = rot

        ### Up/Down rotation
        cam.applyRotation([y, 0.0, 0.0], True)
        """

    def server_setRotation(self, data):
        self.setRotation(data)
        self.call_rpc('recv_rotation', data)

    def _destroy(self):
        self.ob.endObject()

    def _client_update(self, dt):
        npos = self.new_pos
        diff = npos - self.ob.worldPosition
        self.ob.worldPosition += diff * 0.1

    def _server_update(self, dt):
        self.update_timer -= 1
        if self.update_timer == 0:
            self.update_timer = self.update_timer_max

            ob = self.ob
            pos = ob.worldPosition
            rot = self.ob_camera_armature.worldOrientation.to_euler()

            update = False
            if (pos - self.last_pos).length > 0.5:
                update = True

            if update:
                self.last_pos[0] = pos[0]
                self.last_pos[1] = pos[1]
                self.last_pos[2] = pos[2]

                pos = [pos[0], pos[1], pos[2]]

                self.call_rpc('position', pos)

    def _update(self, dt):
        speed = 6.0  # Units per second
        getInput = self.getInput

        move = mathutils.Vector()

        if getInput('forward'):
            move[1] += 1.0

        if getInput('back'):
            move[1] -= 1.0

        if getInput('left'):
            move[0] -= 1.0

        if getInput('right'):
            move[0] += 1.0

        """
        if getInput('primary'):
            ## Aim test
            c = self.ob_camera_armature
            target = c.worldPosition + (c.worldOrientation * mathutils.Vector((0, 1, 0)))
            ##
            result = c.rayCast(target, c, 500.0, '')
            if result[0] is not None:
                bge.render.drawLine(c.worldPosition, result[1], (1.0, 0.0, 0.0))
        """

        move.normalize()
        move = move * speed * dt
        self.ob.applyMovement(move, True)

        if self.new_pos is not None:
            self.new_pos += move * self.ob.worldOrientation.inverted()

    def createLocal(self):
        self.local_component = LocalPlayer(self)
        self.ob.setVisible(0)
        return self.local_component

    def destroyLocal(self):
        self.local_component.ob.endObject()
        self.local_component = None
        self.ob.setVisible(1)


class LocalPlayer(Player):
    def __init__(self, component):
        self.component = component
        Player.__init__(self, component.mgr, component.net_id)
        self.setup()

    def setup(self):
        # Runs when the object is spawned
        owner = self.mgr.owner

        ob = owner.scene.addObject('player', owner)
        ob.worldPosition = self.component.ob.worldPosition

        ob['component'] = self
        self.ob = ob
        self.ob_camera_armature = ob.children['player_camera_armature']
        self.ob_camera = self.ob_camera_armature.children['player_camera']
        self.aiming = False

        self.update_timer = self.update_timer_max = 6

        self.last_rot = ob.worldOrientation.to_euler()

        self.new_pos = None

    def update(self, dt):
        Player._update(self, dt)

        if self.input_changed_:
            self.input_changed_ = False
            state = self.getInputState()
            self.component._packer.pack('_send_input', [state])