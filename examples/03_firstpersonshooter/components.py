import math
import mathutils
import time
from netplay import Component, Pack


def SPAWN_PLAYER(mgr, playername):
    comp = mgr.spawnComponent('Player')
    comp._attributes['playername'] = playername
    comp._attributes['pos_x'] = 0.0
    comp._attributes['pos_y'] = 0.0
    comp._attributes['pos_z'] = 0.0
    comp._attributes['rot_x'] = 0
    comp._attributes['rot_z'] = 0
    comp._send_attributes()
    return comp


class Player(Component):
    def c_register(self):
        # Attributes are used for spawning the object on other clients
        self.registerAttribute('playername', Pack.STRING)
        self.registerAttribute('pos_x', Pack.FLOAT)
        self.registerAttribute('pos_y', Pack.FLOAT)
        self.registerAttribute('pos_z', Pack.FLOAT)
        self.registerAttribute('rot_x', Pack.SHORT)
        self.registerAttribute('rot_z', Pack.SHORT)

        # Up to 32 inputs can be registered.
        # This merely abstracts a built-in RPC
        self.registerInput('up_held')
        self.registerInput('down_held')
        self.registerInput('left_held')
        self.registerInput('right_held')
        self.registerInput('jump_held')
        self.registerInput('primary_held')

        # Periodically send position to ensure clients are in sync
        # Signalled server-side
        self.registerRPC('position', self.setPosition,
                [Pack.FLOAT, Pack.FLOAT, Pack.FLOAT], reliable=False)

        # Re-send rotation whenever it changes, at a max rate of 4 per second
        # Signalled only on the controlling client
        self.registerRPC('rotation', self.setRotation,
                [Pack.SHORT, Pack.SHORT], reliable=False)

    def c_setup(self):
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

        # Used by the server for position correction
        self.next_update = time.monotonic() + 0.5
        self.last_updated_position = mathutils.Vector()

        self.last_rot_x = 0
        self.last_rot_z = 0

        self.next_rot_update = time.monotonic() + 0.25

    def c_refresh_attributes(self):
        # Runs on the server when new clients need information
        # Only need to update attributes that could have changed since creation
        # For example position but not playername
        pos = self.ob.worldPosition
        self.setAttribute('pos_x', pos[0])
        self.setAttribute('pos_y', pos[1])
        self.setAttribute('pos_z', pos[2])

    def c_destroy(self):
        self.ob.endObject()

    def c_update(self, dt):
        speed = 6.0  # Units per second
        getInput = self.getInput

        move = mathutils.Vector()

        if getInput('up_held'):
            move[1] += 1.0

        if getInput('down_held'):
            move[1] -= 1.0

        if getInput('left_held'):
            move[0] -= 1.0

        if getInput('right_held'):
            move[0] += 1.0

        move.normalize()
        self.ob.applyMovement(move * speed * dt, True)

        if self.mgr.game.systems['Input'].input_target is self:
            now = time.monotonic()
            if now > self.next_rot_update:
                euler = self.ob.worldOrientation.to_euler()
                rot_x = int(math.degrees(euler[0]))
                rot_z = int(math.degrees(euler[2]))

                if rot_x != self.last_rot_x or rot_z != self.last_rot_z:
                    self.next_rot_update = now + 0.25

                    self.last_rot_x = rot_z
                    self.last_rot_y = rot_z
                    self._packer.pack('rotation', [rot_x, rot_z])

    def c_server_update(self, dt):
        now = time.monotonic()
        if now > self.next_update:
            self.next_update = now + 0.5

            pos = self.ob.worldPosition
            diff = pos - self.last_updated_position
            dist = diff.length
            if dist > 0.1:
                self.last_updated_position[0] = pos[0]
                self.last_updated_position[1] = pos[1]
                self.last_updated_position[2] = pos[2]
                self._packer.pack('position', [pos[0], pos[1], pos[2]])

    def setPosition(self, data):
        pos = mathutils.Vector((data[0], data[1], 0.0))
        diff = pos - self.ob.worldPosition
        dist = diff.length

        variance = 1.0
        if self.mgr.hostmode == 'client':
            if self.mgr.game.systems['Input'].input_target is self:
                ping = self.mgr.game.systems['Client'].getPing()
                sec = ping / 1000.0
                variance += (6.0 * sec) * 2.0

        if dist > variance:
            self.ob.worldPosition = pos

    def setRotation(self, data):
        rot_x = data[0]
        rot_z = data[1]
        euler = mathutils.Euler((math.radians(rot_x), 0.0, math.radians(rot_z)))
        self.ob.worldOrientation = euler