import mathutils
import time
from netplay import Component, Pack


def SPAWN_PLAYER(mgr, playername):
    comp = mgr.spawnComponent('Player')
    comp._attributes['playername'] = playername
    comp._attributes['pos_x'] = 0.0
    comp._attributes['pos_y'] = 0.0
    comp._send_attributes()
    return comp


class Player(Component):
    def c_register(self):
        # Attributes are used for spawning the object on other clients
        self.registerAttribute('playername', Pack.STRING)
        self.registerAttribute('pos_x', Pack.FLOAT)
        self.registerAttribute('pos_y', Pack.FLOAT)

        # Up to 32 inputs can be registered.
        # This merely abstracts a built-in RPC
        self.registerInput('up_held')
        self.registerInput('down_held')
        self.registerInput('left_held')
        self.registerInput('right_held')

        # We periodically send the xy position to ensure clients are in sync
        self.registerRPC('position', self.setPosition,
                [Pack.FLOAT, Pack.FLOAT], reliable=False)

    def c_setup(self):
        # Runs when the object is spawned
        attr = self.getAttribute
        owner = self.mgr.owner

        ob = owner.scene.addObject('player', owner)
        ob.worldPosition = [attr('pos_x'), attr('pos_y'), 0.0]
        ob.children['player_name']['Text'] = attr('playername')

        ob['component'] = self
        self.ob = ob
        print ("Object created...")

        # Used by the server for position correction
        self.next_update = time.monotonic() + 0.5
        self.last_updated_position = mathutils.Vector()

    def c_refresh_attributes(self):
        # Runs on the server when new clients need information
        # Only need to update attributes that could have changed since creation
        # For example position but not playername
        pos = self.ob.worldPosition
        self.setAttribute('pos_x', pos[0])
        self.setAttribute('pos_y', pos[1])

    def c_destroy(self):
        self.ob.endObject()

    def c_update(self, dt):
        speed = 6.0  # Units per second
        getInput = self.getInput
        resetInput = self.resetInput

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
        self.ob.applyMovement(move * speed * dt, False)

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
                self._packer.pack('position', [pos[0], pos[1]])

    def setPosition(self, data):
        pos = mathutils.Vector((data[0], data[1], 0.0))
        diff = pos - self.ob.worldPosition
        dist = diff.length

        variance = 1.0
        if self.mgr.hostmode == 'client':
            if self.mgr.game.systems['Input'].input_target is self:
                ping = self.mgr.game.systems['Client'].getPing()
                self.ob.children['player_name']['Text'] = "".join([self.getAttribute('playername'), " - ", str(ping), "ms"])
                sec = ping / 1000.0
                variance += (6.0 * sec) * 2.0

        if dist > variance:
            self.ob.worldPosition = pos

