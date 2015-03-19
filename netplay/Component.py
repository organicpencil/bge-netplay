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

        self.hostmode = 'server'

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
        for cls in component_subs:
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

    """
    def spawnComponentByIndex(self, comp_index, pos, ori):
        net_id = self.getNewID()
        if net_id is not None:
            comp = self.component_list[comp_index](self,
                net_id, comp_index, pos, ori)
            self.active_components_[net_id] = comp

            ####### How should the client handle components?
            # comp_index, net_id
            # posx, posy, posz
            # rotx, roty, rotz

            self.MainComponent._packer.pack('addComponent',
                    [net_id, comp_index,
                    pos[0], pos[1], pos[2],
                    ori[0], ori[1], ori[2],
                    comp.getInputState()])

            return comp
        else:
            print ("Component limit reached")
            return None

    def spawnComponent(self, comp_name, pos, ori):
        # Spawns a component in the world by the user-defined index
        # Wraps spawnComponentByIndex
        comp_index = self.component_dict[comp_name]
        return self.spawnComponentByIndex(comp_index, pos, ori)
    """

    def spawnComponent(self, comp_index):

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

        comp.c_destroy()

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
        main_id = self.MainComponent.net_id
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
                    c_dataprocessor.getBytes(main_id, c_p_id, data))

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
                    dataprocessor.getBytes(main_id, p_id, data))

                ## Need to send state before continuing
                """
                statedata = c.c_getStateData()
                if statedata is not None:
                    bdata_list.append(statedata)
                """
                c.c_refresh_attributes()
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

                c.c_update(dt)
                c.c_server_update(dt)

            i += 1


class ClientComponentSystem(ServerComponentSystem):

    def __init__(self, game):
        ServerComponentSystem.__init__(self, game)
        self.hostmode = 'client'
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
        comp.c_destroy()

    def update(self, dt):
        i = 0
        for c in self.active_components_:
            if i == self.next_active_id_:
                # No point iterating over unused component slots
                break

            if c is not None:

                if c.input_changed_:
                    c._input_update()

                c.c_update(dt)

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
        self.next_input_index_ = 0

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
        self.registerRPC('_attributes', self._process_attributes, [Pack.UINT])

        # Register the input update packer
        self.registerRPC('_input', self._process_input,
            [Pack.UINT], ignoreOwner=True)

        # Register the permission packer
        self.registerRPC('_permission', self._process_permission,
            [Pack.USHORT, Pack.UCHAR])

        self.c_register()

    def registerAttribute(self, key, datatype):
        attrs = self._attribute_list
        attrs.append([key, datatype])

        datatype_list = []
        for k, d in attrs:
            datatype_list.append(d)

        # Rebuild attribute packer
        self.registerRPC('_attributes', self._process_attributes, datatype_list)

    def setAttribute(self, key, value):
        self._attributes[key] = value

    def getAttribute(self, key):
        return self._attributes[key]

    def _process_attributes(self, data):
        attrs = self._attribute_list

        attributes = self._attributes
        i = 0
        for k, d in attrs:
            attributes[k] = data[i]
            i += 1

        self.c_setup()
        self._is_setup = True

    def _get_attribute_data(self):
        p_id = self._packer.pack_index['_attributes']
        dataprocessor = self._packer.pack_list[p_id]

        attrs = self._attribute_list

        data = []
        for k, d in attrs:
            data.append(self._attributes[k])

        return dataprocessor.getBytes(self.net_id, p_id, data)

    def _send_attributes(self):
        data = []
        for k, d in self._attribute_list:
            data.append(self._attributes[k])

        self._packer.pack('_attributes', data)

        self.c_setup()
        self._is_setup = True

    def registerRPC(self, key, callback, datatypes,
            reliable=True, ignoreOwner=False):

        self._packer.registerRPC(key, callback, datatypes,
                reliable, ignoreOwner)

    def registerInput(self, input_name):
        # Run once per input key at component init
        # The idea is that we can compress the state
        #     of ~30 predefined keys into a single integer
        """
        if self.next_input_index_ < 2147483647:
            self.input_dict[input_name] = self.next_input_index_
            self.input_state[input_name] = False
            self.predicted_input_state[input_name] = False
            self.next_input_index_ *= 2
            return True
        else:
            print ("Input limit reached")
            return False
        """
        if self.next_input_index_ < 32:
            index = self.next_input_index_
            self.input_dict[input_name] = index
            self.input_mask[index] = 0

            self.next_input_index_ += 1
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
        """
        if self.mgr.hostmode == 'server':
            if self.input_state[input_name] != state:
                self.input_state[input_name] = state
                self.input_changed_ = True

        else:
            if self.predicted_input_state[input_name] != state:
                self.predicted_input_state[input_name] = state
                self.input_changed_ = True
        """
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
        """
        self.input_changed_ = True

        keyList = []
        while input_state > 0:
            lastBase = 1
            base = 1
            while input_state > base:
                lastBase = base
                base *= 2

            input_state -= lastBase
            keyList.append(lastBase)

        for input_name, value in list(self.input_dict.items()):
            if value == 1:
                # 1 is reserved
                continue

            if value in keyList:
                self.input_state[input_name] = True
            else:
                self.input_state[input_name] = False
        """

        mask = bin(input_state)[2:].zfill(32)
        for i in range(0, len(mask)):
            self.input_mask[i] = int(mask[i])

    def getInputState(self):
        """
        #state = 0
        # Input ID 1 is reserved to make it work
        state = 1
        for input_name, value in list(self.input_dict.items()):
            if self.input_state[input_name]:
                state += value

        return state
        """

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
            if self.mgr.hostmode == 'server':
                self._packer.pack('_permission', [client_id, 1])
            elif client_id == self.mgr.client_id:
                self.mgr.game.systems['Input'].setTarget(self)
            return True

    def takePermission(self, client_id):
        if client_id in self.client_permission_list_:
            print ("Taking permission")
            self.client_permission_list_.remove(client_id)
            if self.mgr.hostmode == 'server':
                self._packer.pack('_permission', [client_id, 0])
        else:
            print ("Did not have permission")
            return False

    # Virtual functions

    def c_register(self):
        return

    def c_refresh_attributes(self):
        return

    def c_setup(self):
        return

    def c_destroy(self):
        return

    def _input_update(self):
        self.input_changed_ = False
        if self.mgr.hostmode == 'client':
            if self.mgr.game.systems['Input'].input_target is self:
                state = self.getInputState()
                self._packer.pack('_input', [state])
        else:
            state = self.getInputState()
            self._packer.pack('_input', [state])

    def c_update(self, dt):
        return

    def c_server_update(self, dt):
        return


class MainComponent(Component):
    def __init__(self, mgr, net_id):
        Component.__init__(self, mgr, net_id)
        self.ob_ = mgr.owner

        # new_net_id, new_net_id
        # posx, posy, posz
        # rotx, roty, rotz
        self._packer.registerRPC('addComponent', self.addComponent,
            [Pack.USHORT, Pack.USHORT])

        self._packer.registerRPC('freeComponent', self.freeComponent,
            [Pack.USHORT])

        self._packer.registerRPC('setClientID', self.setClientID,
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

