import bge
import mathutils
from netplay import packer, component, bitstring
from netplay.host import ServerHost


def define_tables():
    if 'tables' in bge.logic.globalDict:
        return
    bge.logic.globalDict['tables'] = 0

    tabledef = packer.TableDef('PlayerSetup')
    tabledef.define('uint16', 'id')
    tabledef.define('float', 'pos_x')
    tabledef.define('float', 'pos_y')
    tabledef.define('float', 'pos_z')
    tabledef.define('float', 'rot_x')
    tabledef.define('float', 'rot_y')
    tabledef.define('float', 'rot_z')
    tabledef.define('float', 'rot_w')
    tabledef.define('uint8', 'input', 0)
    tabledef.component = Player

    tabledef = packer.TableDef('ClientState')
    tabledef.define('uint16', 'id')
    tabledef.define('uint8', 'input', 0)
    tabledef.define('float', 'rot_x')
    tabledef.define('float', 'rot_z')

    tabledef = packer.TableDef('ClientStatePos')
    tabledef.define('uint16', 'id')
    tabledef.define('uint8', 'input', 0)
    tabledef.define('float', 'rot_x')
    tabledef.define('float', 'rot_z')
    tabledef.define('float', 'pos_x')
    tabledef.define('float', 'pos_y')
    tabledef.define('float', 'pos_z')

    # There should probably be a built-in means of destroying components
    tabledef = packer.TableDef('Destroy')
    tabledef.define('uint16', 'id')

    # on_connect and on_disconnect callbacks for spawning players on the server
    ServerHost.on_connect = on_connect
    ServerHost.on_disconnect = on_disconnect


def on_connect(self, peer_id):
    comp = Player(None)
    comp.give_permission(peer_id)


def on_disconnect(self, peer_id):
    for comp in self.components:
        if comp is not None and peer_id in comp.permissions:
            comp.permissions.remove(peer_id)
            if len(comp.permissions) == 0:
                # Destroy the component
                self.components[comp.net_id] = None
                comp.owner.endObject()
                table = packer.Table('Destroy')
                table.set('id', comp.net_id)
                buff = packer.to_bytes(table)

                for client in self.clients:
                    if client is not None and client.peer.incomingPeerID != peer_id:
                        client.send_reliable(buff)


class Player(component.GameObject):
    obj = 'player'

    def start(self):
        self.keystate = bitstring.BitArray(bin='00000000')

        self.speed = 6.0

        # Mouselook stuff
        self.mouseInit = 6
        self.sens = 0.001
        self.invert = 1.0
        self.cap0 = -1.4
        self.cap1 = 1.4
        self.freeMouse = False
        # Workaround for BGE's lousy input system
        self.ACCENTPRESSED = False
        self.head = self.owner.children['player-mesh'].children['head']

    def start_client(self):
        # For interpolation
        self.expected_position = self.owner.worldPosition.copy()

    def start_server(self, args):
        # Force position sync twice per second, could do more
        self.pos_timer = 30
        self.pos_timer_reset = 30

    def serialize(self):
        table = packer.Table('PlayerSetup')
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
        table.set('input', self.keystate.uint)

        return packer.to_bytes(table)

    def deserialize(self, table):
        get = table.get
        pos = (get('pos_x'), get('pos_y'), get('pos_z'))
        rot = mathutils.Quaternion((get('rot_x'),
                                    get('rot_y'),
                                    get('rot_z'),
                                    get('rot_w')))

        self.owner.worldPosition = pos
        self.owner.worldOrientation = rot

    def ClientState(self, table):
        if not bge.logic.netplay.server and self.permission:
            # Player doesn't care about his own rotation
            return

        self.keystate.uint = table.get('input')
        rot = mathutils.Euler()
        rot[2] = table.get('rot_z')
        self.owner.worldOrientation = rot
        rot[0] = table.get('rot_x')
        self.head.worldOrientation = rot

    def ClientStatePos(self, table):
        # No need to duplicate the first part
        self.ClientState(table)

        # Now interpolate the position...
        pos = self.expected_position
        pos[0] = table.get('pos_x')
        pos[1] = table.get('pos_y')
        pos[2] = table.get('pos_z')

    def Destroy(self, table):
        if bge.logic.netplay.server:
            print("Running endobject on the server?")
            return

        self.owner.endObject()
        bge.logic.netplay.components[self.net_id] = None

    def update_player_input(self):
        held = bge.logic.KX_INPUT_ACTIVE
        events = bge.logic.keyboard.events

        if events[bge.events.WKEY] == held:
            self.keystate.set(1, (0,))
        else:
            self.keystate.set(0, (0,))

        if events[bge.events.SKEY] == held:
            self.keystate.set(1, (1,))
        else:
            self.keystate.set(0, (1,))

        if events[bge.events.AKEY] == held:
            self.keystate.set(1, (2,))
        else:
            self.keystate.set(0, (2,))

        if events[bge.events.DKEY] == held:
            self.keystate.set(1, (3,))
        else:
            self.keystate.set(0, (3,))

        # Toggle mouse focus
        if events[bge.events.ACCENTGRAVEKEY] == held:
            if not self.ACCENTPRESSED:
                self.ACCENTPRESSED = True
                self.freeMouse = not self.freeMouse
                if self.freeMouse:
                    bge.render.showMouse(True)
                else:
                    bge.render.showMouse(False)
                    self.mouseInit = 6
        else:
            self.ACCENTPRESSED = False

        self.mouseLook()

        # Send key state and rotation to server
        table = packer.Table('ClientState')
        table.set('id', self.net_id)
        table.set('input', self.keystate.uint)

        rot = self.head.worldOrientation.to_euler()
        table.set('rot_x', rot[0])
        table.set('rot_z', rot[2])

        buff = packer.to_bytes(table)
        # No point sending reliable if we're brute-forcing...
        bge.logic.netplay.send_to_server(buff, reliable=False)

    def mouseLook(self):
        if self.freeMouse:
            return

        ob = self.owner
        head = self.head

        width = bge.render.getWindowWidth()
        height = bge.render.getWindowHeight()

        centerX = int(width / 2)
        centerY = int(width / 2)

        if self.mouseInit:
            self.mouseInit -= 1
            bge.render.setMousePosition(centerX, centerY)
            return

        mpos = list(bge.logic.mouse.position)

        mpos[0] = mpos[0] * width
        mpos[1] = mpos[1] * height

        if int(mpos[0]) == centerX and int(mpos[1]) == centerY:
            return

        w = centerX - mpos[0]
        h = centerY - mpos[1]

        sens = self.sens
        #wep = self.weapon
        #if wep is not None and wep.aiming:
        #    sens = sens / 4.0

        x = w * sens
        y = h * sens * self.invert

        #self.setAttackDirection(x, y)

        ### Left/Right rotation
        # applyRotation screws up momentum, don't use it on dynamic objects
        rot = ob.worldOrientation.to_euler()
        rot[2] += x
        ob.worldOrientation = rot

        ### Up/Down cap
        rad = head.worldOrientation.to_euler()

        if y < 0.0 and rad[0] < self.cap0:
            y = 0.0
        if y > 0.0 and rad[0] > self.cap1:
            y = 0.0

        ### Up/Down rotation
        head.applyRotation([y, 0.0, 0.0], True)

        # Reset mouse position
        bge.render.setMousePosition(centerX, centerY)

    def _permission(self, table):
        component.GameObject._permission(self, table)
        if self.permission:
            bge.logic.getCurrentScene().active_camera = self.head.children['player-camera']
            bge.render.showMouse(False)
        else:
            print("Uhh... which camera to use?")

    def update_client(self):
        if self.permission:
            self.update_player_input()

        # Predict movement
        self.move()

        vel = self.owner.getLinearVelocity(False)
        vel = vel * (1.0 / 60.0)
        self.expected_position += vel

        # Apply correction
        if self.permission:
            # Only apply if too far out of sync
            dist = self.owner.getDistanceTo(self.expected_position)
            t = bge.logic.netplay.get_ping() / 200.0 # Allowing time x5 variance
            if dist < self.speed * t:
                return

        self.owner.worldPosition = self.owner.worldPosition.lerp(self.expected_position, 0.1)

    def move(self):
        owner = self.owner

        # Apply input state
        keys = self.keystate.bin
        move = mathutils.Vector()

        if keys[0] == '1':
            # Forward
            move[1] += 1.0
        if keys[1] == '1':
            # Back
            move[1] -= 1.0
        if keys[2] == '1':
            # Left
            move[0] -= 1.0
        if keys[3] == '1':
            # Right
            move[0] += 1.0

        move.normalize()
        move = move * self.speed
        move[2] = owner.localLinearVelocity[2]
        owner.localLinearVelocity = move

        # More gravity
        owner.applyForce((0.0, 0.0, -9.8), False)

    def update_server(self):
        self.move()

        self.pos_timer -= 1
        pos = False
        if not self.pos_timer:
            pos = True
            self.pos_timer = self.pos_timer_reset

            # Send key state, rotation, and pos to clients
            table = packer.Table('ClientStatePos')
            table.set('id', self.net_id)
            table.set('input', self.keystate.uint)

            rot = self.head.worldOrientation.to_euler()
            table.set('rot_x', rot[0])
            table.set('rot_z', rot[2])

            pos = self.owner.worldPosition
            table.set('pos_x', pos[0])
            table.set('pos_y', pos[1])
            table.set('pos_z', pos[2])

        else:
            # Send key state and rotation to clients
            table = packer.Table('ClientState')
            table.set('id', self.net_id)
            table.set('input', self.keystate.uint)

            rot = self.head.worldOrientation.to_euler()
            table.set('rot_x', rot[0])
            table.set('rot_z', rot[2])

        # Send
        buff = packer.to_bytes(table)
        bge.logic.netplay.send_to_clients(buff)


def register_player(cont):
    owner = cont.owner
    if '_component' in owner:
        return

    # This gets discarded if the component was spawned directly.
    # We only do this so objects can be placed in the editor / add actuator
    Player(owner)