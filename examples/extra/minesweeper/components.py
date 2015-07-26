import bge
import mathutils
import time
import random

from netplay import Component, Pack


## Call these on the server
##


class Player(Component):
    def _register(self):
        # Attributes are used for spawning the object on clients
        # These should ONLY be defined once and in c_register
        self.register_attribute('playername', Pack.STRING, 'unnamed')
        self.register_attribute('current_block_x', Pack.USHORT, 0)
        self.register_attribute('current_block_y', Pack.USHORT, 0)

        # RPCs are called during the game
        self.register_rpc('set_current_block', self.setBlock,
                [Pack.USHORT, Pack.USHORT])

        # Inputs are intended to efficiently sync keystates as a bitmask.
        # Up to 32 keys can be registered.
        self.register_input('primary_pressed')
        self.register_input('primary_released')
        self.register_input('secondary_pressed')
        # You can accomplish the same with RPCs if desired.
        # In fact inputs are just an abstraction to this built-in RPC:
        #self.registerRPC('_input', self._process_input, [Pack.UINT])

    def _update_attributes(self):
        # Runs on server when new clients need information
        # Only need to update attributes that could have changed
        self.setAttribute('current_block_x', self.current_block[0])
        self.setAttribute('current_block_y', self.current_block[1])

    def _setup(self):
        # Runs when the objected is spawned on the client

        # Access attributes as needed.
        self.playername = self._attributes['playername']
        self.current_block = [
                self.getAttribute('current_block_x'),
                self.getAttribute('current_block_y')
                ]

        # True when mouse is held
        self.holding = False

    def _destroy(self):
        # Unhover / hold blocks
        self.setBlock([0, 0])

    def setBlock(self, data):
        x = data[0]
        y = data[1]

        old_x = self.current_block[0]
        old_y = self.current_block[1]

        board = self.mgr.game.board

        oldblock = board.grid[old_x][old_y]
        if self.holding:
            oldblock.removeHold()
        oldblock.removeHover()

        newblock = board.grid[x][y]
        newblock.addHover()
        if self.holding:
            newblock.addHold()
        self.current_block[0] = x
        self.current_block[1] = y

    def _update(self, dt):
        x = self.current_block[0]
        y = self.current_block[1]
        board = self.mgr.game.board
        if len(board.grid) == 0:
            # Board not yet initialized
            return

        block = board.grid[x][y]

        getInput = self.getInput

        if getInput('primary_pressed'):
            self.resetInput('primary_pressed')
            self.holding = True
            block.addHold()

        if getInput('primary_released'):
            self.resetInput('primary_released')
            self.holding = False
            block.removeHold()
            board.open(block)

        if getInput('secondary_pressed'):
            self.resetInput('secondary_pressed')
            block.toggleFlag()


class Block:
    def __init__(self, comp, x, y):
        self.board = comp
        self.x = x
        self.y = y
        self.adjacent = 0
        self.isMine = False
        self.isOpen = False
        self.isFlagged = False

        self.hovering = 0
        self.holding = 0

        owner = comp.mgr.owner
        ob = owner.scene.addObject('Block', owner)
        ob.worldPosition = [x, y, 0.0]
        ob['BLOCK'] = self
        self.ob = ob

    def addHover(self):
        self.hovering += 1
        if self.hovering == 1 and not self.isFlagged and not self.isOpen:
            self.ob.replaceMesh('Block_hover')

    def removeHover(self):
        self.hovering -= 1
        if self.hovering == 0 and not self.isFlagged and not self.isOpen:
            self.ob.replaceMesh('Block')

    def addHold(self):
        self.holding += 1

        if self.holding == 1 and not self.isFlagged and not self.isOpen:
            self.ob.replaceMesh('Block_pressed')

    def removeHold(self):
        self.holding -= 1

        if self.holding == 0 and not self.isFlagged and not self.isOpen:
            if self.hovering:
                self.ob.replaceMesh('Block_hover')
            else:
                self.ob.replaceMesh('Block')

    def toggleFlag(self):
        if self.isFlagged:
            self.isFlagged = False

            if self.holding:
                self.ob.replaceMesh('Block_pressed')
            elif self.hovering:
                self.ob.replaceMesh('Block_hover')
            else:
                self.ob.replaceMesh('Block')

        else:
            self.isFlagged = True
            self.ob.replaceMesh('Block_locked')

    def reveal(self):
        new = self.ob.scene.addObject('Uncovered', self.ob)
        self.ob.endObject()
        self.ob = new

        text = new.children[0]
        if self.isMine:
            text['Text'] = "X"
            text.color = self.board.colors[0]
        elif self.adjacent:
            text['Text'] = "%d" % self.adjacent
            text.color = self.board.colors[self.adjacent]
        else:
            text['Text'] = ""

    def destroy(self):
        self.ob.endObject()


class Board(Component):
    def _register(self):
        self.register_attribute('size_x', Pack.USHORT, 0)
        self.register_attribute('size_y', Pack.USHORT, 0)
        self.register_attribute('mine_count', Pack.USHORT, 0)
        self.register_attribute('mine_locations', Pack.STRING, "")
        self.register_attribute('open_locations', Pack.STRING, "")
        self.register_attribute('flag_locations', Pack.STRING, "")

    def _server_setup(self):
        self.generateMineLocations()

    def _setup(self):
        self.mgr.game.board = self

        self.colors = [
            [0.0, 0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0, 1.0],
            [0.0, 1.0, 0.0, 1.0],
            [1.0, 0.0, 0.0, 1.0],
            [0.0, 0.0, 0.5, 1.0],
            [0.5, 0.0, 0.0, 1.0],
            [0.5, 0.5, 1.0, 1.0],
            [0.0, 0.0, 0.0, 1.0],
            [0.0, 0.0, 0.0, 1.0],
        ]

        attr = self.getAttribute

        self.size_x = attr('size_x')
        self.size_y = attr('size_y')
        self.blocks_remaining = (self.size_x * self.size_y) - attr('mine_count')

        self.setMineLocations(attr('mine_locations'))
        self.setOpenLocations(attr('open_locations'))
        self.setFlagLocations(attr('flag_locations'))

    def _update_attributes(self):
        open_locations = ""
        flag_locations = ""
        for x in range(0, self.size_x):
            for y in range(0, self.size_y):
                if self.grid[x][y].isOpen:
                    open_locations += "%d-%d," % (x, y)

                if self.grid[x][y].isFlagged:
                    flag_locations += "%d-%d," % (x, y)

        self.setAttribute('open_locations', open_locations)
        self.setAttribute('flag_locations', flag_locations)

    def initGrid(self):
        # Initialize an empty grid
        try:
            self.grid
            # Grid already exists, must be server
            print ("This is a terrible solution")
            return
        except:
            pass

        self.grid = []
        grid = self.grid
        for x in range(0, self.size_x):
            grid.append([])
            for y in range(0, self.size_y):
                grid[x].append(Block(self, x, y))

    def setMineLocations(self, locations):
        self.initGrid()

        loc_list = locations.split(',')
        for L in loc_list:
            if L == '':  # Last entry is blank
                break

            x, y = L.split('-')
            self.grid[int(x)][int(y)].isMine = True

        self.calculateAdjacent()

    def setOpenLocations(self, locations):
        loc_list = locations.split(',')
        for L in loc_list:
            if L == '':  # Last entry is blank
                break

            x, y = L.split('-')
            #self.grid[int(x)][int(y)].isOpen = True
            block = self.grid[int(x)][int(y)]
            self.open(block)

    def setFlagLocations(self, locations):
        loc_list = locations.split(',')
        for L in loc_list:
            if L == '':  # Last entry is blank
                break

            x, y = L.split('-')
            #self.grid[int(x)][int(y)].isFlagged = True
            block = self.grid[int(x)][int(y)]
            block.toggleFlag()

    def generateMineLocations(self):
        self.size_x = size_x = self.getAttribute('size_x')
        self.size_y = size_y = self.getAttribute('size_y')
        mine_count = self.getAttribute('mine_count')

        self.initGrid()

        # Server only, run this instead of setting initial attributes
        self.setAttribute('mine_locations', "")
        self.setAttribute('open_locations', "")
        self.setAttribute('flag_locations', "")

        mine_locations = ""

        grid = self.grid
        used = []
        for i in range(0, mine_count):
            rx = random.randint(0, size_x - 1)
            ry = random.randint(0, size_y - 1)

            done = False
            while not done:
                done = True

                for u in used:
                    if u[0] == rx and u[1] == ry:
                        done = False

                        rx += 1
                        if rx == size_x:
                            rx = 0
                            ry += 1
                            if ry == size_y:
                                ry = 0

            used.append([rx, ry])
            block = grid[rx][ry]
            block.isMine = True
            mine_locations += "%d-%d," % (rx, ry)

        self.setAttribute('mine_locations', mine_locations)
        #self.calculateAdjacent()

    def calculateAdjacent(self):
        # Calculate adjacent mines
        grid = self.grid
        for x in range(0, self.size_x):
            for y in range(0, self.size_y):
                block = grid[x][y]
                for xx in range(-1, 2):
                    for yy in range(-1, 2):
                        xi = x + xx
                        yi = y + yy

                        if self.size_x > xi > -1:
                            if self.size_y > yi > -1:
                                other = grid[xi][yi]
                                if other.isMine:
                                    block.adjacent += 1

    def open(self, block):
        if block.isOpen or block.isFlagged:
            return

        block.reveal()
        block.isOpen = True

        if block.isMine:
            timer = self.mgr.game.timer
            timer.onStop([timer.time, 1])
            # Sync time with clients
            if self.mgr.hostmode == 'server':
                timer._packer.pack('stop', [timer.time, timer.stopped])

            return

        else:
            self.blocks_remaining -= 1
            if self.blocks_remaining == 0:
                timer = self.mgr.game.timer
                timer.onStop([timer.time, 2])
                # Sync time with clients
                if self.mgr.hostmode == 'server':
                    timer._packer.pack('stop', [timer.time, timer.stopped])

                return

        # Recursively open adjacent blocks while adjacent is 0
        if block.adjacent == 0:
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if dx == 0 and dy == 0:
                        continue

                    x = block.x + dx
                    y = block.y + dy

                    if (0 <= x < self.size_x) and (0 <= y < self.size_y):
                        other = self.grid[x][y]
                        if not other.isOpen and not other.isFlagged:
                            self.open(other)
                            #other.reveal()

    def _destroy(self):
        for col in self.grid:
            for block in col:
                block.destroy()

        self.grid = []


class Timer(Component):
    def _register(self):
        self.register_attribute('time', Pack.FLOAT, 0.0)
        self.register_attribute('stopped', Pack.CHAR, 0)

        self.register_rpc('stop', self.onStop, [Pack.FLOAT, Pack.CHAR])

    def _update_attributes(self):
        self.setAttribute('time', self.time)
        self.setAttribute('stopped', self.stopped)

    def _setup(self):
        owner = self.mgr.owner
        ob = owner.scene.addObject('Timer', owner)
        ob.worldPosition = [-7.0, 11.0, 0.0]
        self.ob = ob
        self.mgr.game.timer = self

        self.onStop([self.getAttribute('time'), self.getAttribute('stopped')])

    def _destroy(self):
        self.ob.endObject()

    def _update(self, dt):
        if not self.stopped:
            self.time += dt
            self.ob['Text'] = "%.0f" % self.time

    def onStop(self, data):
        # Sync with server stop time
        self.time = data[0]
        self.stopped = data[1]
        self.ob['Text'] = "%.0f" % self.time

        if self.stopped == 1:
            # Loss
            self.ob['Text'] += " - Defeated"

        if self.stopped == 2:
            # Win
            self.ob['Text'] += " - Victory"
