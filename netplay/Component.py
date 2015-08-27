import collections
import mathutils
from . import Pack


def all_subclasses(cls):
    return cls.__subclasses__() + [g for s in cls.__subclasses__()
                                    for g in all_subclasses(s)]


class ServerComponentSystem:

    def __init__(self, game):
        self.game = game
        self.owner = game.owner

        self.server = True

        # List of components ordered by ID (16 bit unsigned short)
        self.active_components_ = [None] * 65535
        # Next component ID to use
        self.next_active_id_ = 0
        # List of freed component IDs ordered oldest-newest
        self.freed_active_id_ = collections.deque()

        # Indexes possible components by a user-defined value
        self.component_dict = {}
        # Indexes possible components by a generated ID for fast lookups
        self.component_list = []
        self.next_component_index_ = 0

        self.registerComponent(MainComponent)
        self.createMainComponent()

        component_subs = all_subclasses(Component)
        component_subs.sort(key=lambda x: x.__name__, reverse=False)
        for cls in component_subs:
            if cls is MainComponent:
                continue
            self.registerComponent(cls)

    def createMainComponent(self):
        net_id = self.getNewID()  # Should be 0 every time
        self.MainComponent = MainComponent(self, 0)
        self.active_components_[net_id] = self.MainComponent

        if net_id != 0:
            print ("ERROR - base component ID is not 0")

    def registerComponent(self, comp):
        comp_name = comp.__name__
        # One-time per component type, both client and server
        comp.comp_index = self.next_component_index_
        self.component_dict[comp_name] = self.next_component_index_
        self.component_list.append(comp)
        self.next_component_index_ += 1

    def getNewID(self):
        if len(self.freed_active_id_):
            return self.freed_active_id_.popleft()
        elif self.next_active_id_ <= 65535:
            cid = self.next_active_id_
            self.next_active_id_ += 1
            return cid
        else:
            return None

    def spawnComponent(self, comp_index, **kwargs):
        if type(comp_index is str):
            comp_index = self.getComponentIndex(comp_index)

        net_id = self.getNewID()
        if net_id is not None:
            comp = self.component_list[comp_index](self, net_id)
            self.active_components_[net_id] = comp

            ###### The data
            # comp_index, net_id,
            # posx, posy, posz,
            # rotx, roty, rotz,
            # inputstate

            self.MainComponent._packer.pack('addComponent',
                (net_id, comp_index))

            # Set attributes
            for key in kwargs:
                comp.setAttribute(key, kwargs[key])

            # Run server setup function
            comp._server_setup()

            comp._send_attributes()

            return comp

        else:
            print ("Component limit reached")
            return None

    def getComponentIndex(self, comp_name):
        return self.component_dict[comp_name]

    def freeComponent(self, comp):
        net_id = comp.net_id

        self.MainComponent._packer.pack('freeComponent',
                [net_id])

        # Send backlogged data before freeing
        self.game.systems['Server'].sendQueuedData()

        self.active_components_[net_id] = None
        self.freed_active_id_.append(net_id)

        comp._destroy()

    def getComponent(self, net_id):
        return self.active_components_[net_id]

    def getQueuedData(self):
        bdata_list = []

        i = 0
        for c in self.active_components_:
            if i == self.next_active_id_:
                # No point iterating over unused component slots
                break

            if c is not None:
                bdata_list.append(c._packer.queued_data)
                c._packer.queued_data = []

            i += 1

        return bdata_list

    def getGameState(self, client_id):
        bdata_list = []

        key = 'addComponent'
        packer = self.MainComponent._packer
        p_id = packer.pack_index[key]
        dataprocessor = packer.pack_list[p_id]

        i = 0
        for c in self.active_components_:
            if i == self.next_active_id_:
                # No point iterating over unused component slots
                break

            if i == 0:
                net_id = c.net_id
                comp_index = c.comp_index
                data = [client_id]

                c_p_id = packer.pack_index['setClientID']
                c_dataprocessor = packer.pack_list[c_p_id]
                bdata_list.append(
                    c_dataprocessor.getBytes(c_p_id, data))

            elif c is not None:
                net_id = c.net_id
                comp_index = c.comp_index

                #if c.ob_ is not None:
                #    pos = c.ob_.worldPosition
                #    rot = c.ob_.worldOrientation.to_euler()
                #else:
                #    pos = [0.0, 0.0, 0.0]
                #    rot = [0.0, 0.0, 0.0]

                #data = [net_id, comp_index,
                #    pos[0], pos[1], pos[2],
                #    rot[0], rot[1], rot[2],
                #    c.getInputState()]

                data = [net_id, comp_index]

                bdata_list.append(
                    dataprocessor.getBytes(p_id, data))

                ## Need to send state before continuing
                """
                statedata = c.c_getStateData()
                if statedata is not None:
                    bdata_list.append(statedata)
                """
                c._update_attributes()
                attrdata = c._get_attribute_data()
                if attrdata is not None:
                    bdata_list.append(attrdata)

                print ("FIXME - sync input state for spawned objects")

            i += 1

        return bdata_list

    def update(self, dt):
        i = 0
        for c in self.active_components_:
            if i == self.next_active_id_:
                # No point iterating over unused component slots
                break

            if c is not None:
                if not c._is_setup:
                    print ("Not setup?")
                    print (c)
                    continue

                if c.input_changed_:
                    c._input_update()

                c._update(dt)
                c._server_update(dt)

            i += 1


class ClientComponentSystem(ServerComponentSystem):

    def __init__(self, game):
        ServerComponentSystem.__init__(self, game)
        self.server = False
        self.client_id = -1

    def spawnComponentByIndex(self, net_id, comp_index):
        comp = self.component_list[comp_index](self,
            net_id)
        self.active_components_[net_id] = comp

        if net_id >= self.next_active_id_:
            self.next_active_id_ = net_id + 1

        return comp

    def spawnComponent(self, comp_name):
        print ("WARNING - spawnComponent not implemented on client")

    def freeComponent(self, comp):
        net_id = comp.net_id
        self.active_components_[net_id] = None
        comp._destroy()

    def update(self, dt):
        i = 0
        for c in self.active_components_:
            if i == self.next_active_id_:
                # No point iterating over unused component slots
                break

            if c is not None:

                if not c._is_setup:
                    print ("Not setup?")
                    print (c)
                    continue

                #if c.input_changed_:
                #    c._input_update()

                c._client_update(dt)
                c._update(dt)

            i += 1


class Component:

    def __init__(self, mgr, net_id):
        self.mgr = mgr
        self.ob_ = None
        self.net_id = net_id

        self._is_setup = False

        # List of clients (by ID) with permission to set input
        self.client_permission_list_ = []

        # Replaces the funky input status dict with a bitmask list
        self.input_mask = [0] * 32

        # Indexes input keys by a user-defined value
        self.input_dict = {}

        # Consumed as inputs are registered, valid < 32
        self.next_input_index_ = 31

        # Current input state
        #self.input_state = {}

        # Predicted input state for clients with input permission
        # For now it's only for requesting changes
        #self.predicted_input_state = {}

        # Next input index (32 bit signed int)
        #self.next_input_index_ = 1
        # 1 must always be part of the state for the compression to work,
        # As such 1 is reserved.
        #self.next_input_index_ = 2

        # True when the input state has changed in a frame
        # Used to queue network updates
        self.input_changed_ = False

        # Data packer for network play
        self._packer = Pack.Packer(self)

        self._attributes = {}
        self._attribute_list = []

        # Register the initial attribute packer
        # Ideally replaced during c_register
        self.RPC_Client('_attributes', self._process_attributes, [Pack.UINT])

        # Register the input update packer
        self.RPC_Server('_send_input', self._process_input,
            [Pack.UCHAR])

        self.RPC_Client('_recv_input', self._process_input,
            [Pack.UCHAR])

        # Register the permission packer
        self.RPC_Client('_permission', self._process_permission,
            [Pack.USHORT, Pack.UCHAR])

        self._register()

    def register_attribute(self, key, datatype, default):
        self._attributes[key] = default

        attrs = self._attribute_list
        attrs.append([key, datatype])

        datatype_list = []
        for k, d in attrs:
            datatype_list.append(d)

        # Rebuild attribute packer
        self.RPC_Client('_attributes', self._process_attributes, datatype_list)

    def setAttribute(self, key, value):
        self._attributes[key] = value

    def getAttribute(self, key):
        #return self._attributes[key]
        return self._attributes.get(key, None)

    def _process_attributes(self, data):
        attrs = self._attribute_list

        attributes = self._attributes
        i = 0
        for k, d in attrs:
            attributes[k] = data[i]
            i += 1

        self._setup()
        self._is_setup = True

    def _get_attribute_data(self):
        p_id = self._packer.pack_index['_attributes']
        dataprocessor = self._packer.pack_list[p_id]

        attrs = self._attribute_list

        data = []
        for k, d in attrs:
            data.append(self._attributes[k])

        return dataprocessor.getBytes(p_id, data)

    def _send_attributes(self):
        data = []
        for k, d in self._attribute_list:
            data.append(self._attributes[k])

        self._packer.pack('_attributes', data)

        self._setup()
        self._is_setup = True

    def RPC_Server(self, key, callback, datatypes, reliable=True):
        server = True
        self._packer.registerRPC(key, callback, datatypes,
                server, reliable)

    def RPC_Client(self, key, callback, datatypes, reliable=True):
        server = False
        self._packer.registerRPC(key, callback, datatypes,
                server, reliable)

    def getRPCData(self, key, data):
        return self._packer.getRPCData(key, data)

    """
    def register_rpc(self, key, callback, datatypes,
            reliable=True, replicate=True, private=False, server_only=False):

        self._packer.registerRPC(key, callback, datatypes,
                reliable, replicate, private, server_only)
    """

    def call_rpc(self, key, datalist):
        if self.mgr.server:
            p_id = self._packer.pack_index[key]
            dp = self._packer.pack_list[p_id]
            # Don't auto-call client RPCs on the server, let users define
            # this behavior is necessary from the server RPC callback
            if dp.server:
                dp.callback(datalist)
                return

        self._packer.pack(key, datalist)
        """
        # Apply now if called on the server
        # This potentially wastes CPU time, for example updating position
        if self.mgr.hostmode == 'server':
            p_id = self._packer.pack_index[key]
            dataprocessor = self._packer.pack_list[p_id]
            dataprocessor.callback(datalist)
        """

    def register_input(self, input_name):
        # Run once per input key at component init
        # Creates a bitmask for the input state, allowing 32 keys and
        # consuming 1 to 4 bytes per update.
        if self.next_input_index_ > 0:
            index = self.next_input_index_
            self.input_dict[input_name] = index
            self.input_mask[index] = 0

            self.next_input_index_ -= 1

            if index == 16:  # Need to allocate 2 bytes
                self.RPC_Client('_recv_input', self._process_input,
                    [Pack.USHORT])
                self.RPC_Server('_send_input', self._process_input,
                    [Pack.USHORT])

            elif index == 8:  # Need to allocate 4 bytes
                self.RPC_Client('_recv_input', self._process_input,
                    [Pack.UINT])
                self.RPC_Server('_send_input', self._process_input,
                    [Pack.UINT])

            return True
        else:
            print ("Input limit reached")
            return False

    def assignClientInput(self, input_name, input_index):
        # The client version of registerInput
        self.input_dict[input_name] = input_index
        self.input_state[input_name] = False

    def resetInput(self, input_name):
        state = 0
        index = self.input_dict[input_name]
        if self.input_mask[index] != state:
            self.input_mask[index] = state

    def setInput(self, input_name, state):
        # Called when keys are pressed
        if state:
            state = 1
        else:
            state = 0

        index = self.input_dict[input_name]
        if self.input_mask[index] != state:
            self.input_mask[index] = state
            self.input_changed_ = True

    def getInput(self, input_name):
        #return self.input_state[input_name]
        index = self.input_dict[input_name]
        return self.input_mask[index]

    def setInputState(self, input_state):
        self.input_changed_ = True
        mask = bin(input_state)[2:].zfill(32)
        for i in range(0, len(mask)):
            self.input_mask[i] = int(mask[i])

    def getInputState(self):
        return int(''.join(map(str, self.input_mask)), 2)

    def getPredictedInputState(self):
        #state = 0
        # Input ID 1 is reserved to make it work
        state = 1
        for input_name, value in list(self.input_dict.items()):
            if self.predicted_input_state[input_name]:
                state += value

        return state

    def _process_permission(self, data):
        client_id = data[0]
        allowed = data[1]
        if allowed:
            self.givePermission(client_id)
        else:
            self.takePermission(client_id)

    def _process_input(self, data):
        state = data[0]
        self.setInputState(state)

    def hasPermission(self, client_id):
        return client_id in self.client_permission_list_

    def givePermission(self, client_id):
        if client_id in self.client_permission_list_:
            print ("Already has permission")
            return False
        else:
            print ("Giving permission")
            self.client_permission_list_.append(client_id)
            if self.mgr.server:
                self._packer.pack('_permission', [client_id, 1])
            elif client_id == self.mgr.client_id:
                self.mgr.game.systems['Input'].setTarget(self)
            return True

    def takePermission(self, client_id):
        if client_id in self.client_permission_list_:
            print ("Taking permission")
            self.client_permission_list_.remove(client_id)
            if self.mgr.server:
                self._packer.pack('_permission', [client_id, 0])
        else:
            print ("Did not have permission")
            return False

    # Virtual functions

    def _register(self):
        return

    def _server_setup(self):
        return

    def _setup(self):
        return

    def _update_attributes(self):
        return

    def _destroy(self):
        return

    def _input_update(self):
        self.input_changed_ = False
        state = self.getInputState()
        self._packer.pack('_recv_input', [state])

    def _client_update(self, dt):
        return

    def _update(self, dt):
        return

    def _server_update(self, dt):
        return


class MainComponent(Component):
    def __init__(self, mgr, net_id):
        Component.__init__(self, mgr, net_id)
        self.ob_ = mgr.owner

        # new_net_id, new_net_id
        # posx, posy, posz
        # rotx, roty, rotz

        self.RPC_Client('addComponent', self.addComponent,
                [Pack.USHORT, Pack.USHORT])

        self.RPC_Client('freeComponent', self.freeComponent,
                [Pack.USHORT])

        self.RPC_Client('setClientID', self.setClientID,
                [Pack.INT])

        self._is_setup = True

    def addComponent(self, data):
        net_id = data[0]
        comp_index = data[1]
        #pos = [data[2], data[3], data[4]]
        #ori = mathutils.Euler((data[5], data[6], data[7]))
        #input_state = data[8]

        self.mgr.spawnComponentByIndex(net_id, comp_index)
        #comp.setInputState(input_state)

    def freeComponent(self, data):
        net_id = data[0]

        comp = self.mgr.active_components_[net_id]
        self.mgr.freeComponent(comp)

    def setClientID(self, data):
        self.mgr.client_id = data[0]


class MovingComponent(Component):
    def __init__(self, mgr, net_id):
        Component.__init__(self, mgr, net_id)
        self.obj = None

    def _register(self):
        self.register_attribute('_pos_x', Pack.FLOAT, 0.0)
        self.register_attribute('_pos_y', Pack.FLOAT, 0.0)
        self.register_attribute('_pos_z', Pack.FLOAT, 0.0)
        self.register_attribute('_rot_x', Pack.FLOAT, 0.0)
        self.register_attribute('_rot_y', Pack.FLOAT, 0.0)
        self.register_attribute('_rot_z', Pack.FLOAT, 0.0)

        self.RPC_Client('_physics_state', self.updatePhysics,
                [
                    Pack.FLOAT, Pack.FLOAT, Pack.FLOAT,
                    Pack.FLOAT, Pack.FLOAT, Pack.FLOAT,
                ], reliable=False)

    def _update_attributes(self):
        pos = self.ob.worldPosition
        self.setAttribute('_pos_x', pos[0])
        self.setAttribute('_pos_y', pos[1])
        self.setAttribute('_pos_z', pos[2])

        rot = self.ob.worldOrientation.to_euler()
        self.setAttribute('_rot_x', rot[0])
        self.setAttribute('_rot_y', rot[1])
        self.setAttribute('_rot_z', rot[2])

    def _setup(self):
        if self.obj is None:
            print ("Error - physics object not defined")
            return

        attr = self.getAttribute
        own = self.mgr.owner

        self.ob = ob = own.scene.addObject(self.obj, own)

        ob.worldPosition = [attr('_pos_x'), attr('_pos_y'), attr('_pos_z')]
        ob.worldOrientation = mathutils.Euler((attr('_rot_x'), attr('_rot_y'),
                attr('_rot_z')))

        ob['component'] = self

        self.update_timer = self.update_timer_max = 6
        self._last_pos = mathutils.Vector(self.ob.worldPosition)
        self._last_rot = self.ob.worldOrientation.to_euler()

        self._pos_lerp = mathutils.Vector()
        self._lerp_count = 0
        self._new_ori = None

        self._idle = True  # Handy for debugging

        if not self.mgr.server:
            self.ob.suspendDynamics()

    def _destroy(self):
        self.ob.endObject()

    def _client_update(self, dt):
        ob = self.ob

        if self._lerp_count > 0:
            self._lerp_count -= 1
            ob.worldPosition += self._pos_lerp

        if self._new_ori is not None:
            ob.worldOrientation = ob.worldOrientation.lerp(self._new_ori, 0.1)

    def updatePhysics(self, data):
        self._lerp_count = 10

        pos = mathutils.Vector((data[0], data[1], data[2]))
        self._pos_lerp = (pos - self.ob.worldPosition) * 0.1

        ori = mathutils.Euler((data[3], data[4], data[5])).to_matrix()
        self._new_ori = ori

    def _server_update(self, dt):
        self.update_timer -= 1
        if self.update_timer == 0:
            self.update_timer = self.update_timer_max

            ob = self.ob
            pos = ob.worldPosition
            rot = ob.worldOrientation.to_euler()

            update = False
            if (pos - self._last_pos).length > 0.01:
                update = True
            else:
                lastrot = self._last_rot
                for i in range(0, 3):
                    if abs(rot[i] - lastrot[i]) > 0.01:
                        update = True
                        break

            if update:
                self._last_pos = mathutils.Vector(self.ob.worldPosition)
                self._last_rot = self.ob.worldOrientation.to_euler()
                physics_state = [pos[0], pos[1], pos[2],
                        rot[0], rot[1], rot[2]]

                self.call_rpc('_physics_state', physics_state)
                self._idle = False
            else:
                self._idle = True


class CharacterComponent(Component):
    None


def SoftComponent(Component):
    None