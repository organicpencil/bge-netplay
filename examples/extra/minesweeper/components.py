## PLACEHOLDER - LIKELY BROKEN

import bge
import mathutils
import time

from netplay import Component, Pack


## Call these on the server
def SPAWN_PLAYER(mgr, playername):
    comp = mgr.spawnComponent('Player')
    comp._attributes['playername'] = playername
    comp._attributes['current_block_id'] = 0
    comp._send_attributes()
    return comp


def SPAWN_BLOCK(mgr, x, y):
    comp = mgr.spawnComponent('Block')
    a = comp._attributes
    a['x'] = x
    a['y'] = y
    a['over'] = 0
    a['held'] = 0
    a['opened'] = 0
    a['flagged'] = 0
    a['count'] = 0
    a['isMine'] = 0
    comp._send_attributes()
    return comp
##


class Player(Component):
    def c_register(self):
        # Attributes are used for spawning the object on clients
        # These should ONLY be defined once and in c_register
        self.registerAttribute('playername', Pack.STRING)
        self.registerAttribute('current_block_id', Pack.USHORT)

        # RPCs are called during the game
        self.registerRPC('set_current_block', self.setBlock, [Pack.USHORT])

        # Inputs are intended to efficiently sync keystates as a bitmask.
        # Up to 32 keys can be registered.
        self.registerInput('primary_pressed')
        self.registerInput('primary_released')
        self.registerInput('secondary_pressed')
        # You can accomplish the same with RPCs if desired.
        # In fact inputs are just an abstraction to this built-in RPC:
        #self.registerRPC('_input', self._process_input, [Pack.UINT])
        
    def c_refresh_attributes(self):
        # Runs on server when new clients need information
        # Only need to update attributes that could have changed
        self.setAttribute('current_block_id', self.current_block_id)

    def c_setup(self):
        # Runs when the objected is spawned on the client

        # Access attributes as needed.
        self.playername = self._attributes['playername']
        self.current_block_id = self._attributes['current_block_id']

        # True when mouse is held
        self.holding = False

    def setBlock(self, data):
        if self.current_block_id != 0:
            oldblock = self.mgr.getComponent(self.current_block_id)
            if self.holding:
                oldblock.removeHold()

            oldblock.removeHover()

            self.current_block_id = 0

        net_id = data[0]
        block = self.mgr.getComponent(net_id)
        block.addHover()
        if self.holding:
            block.addHold()

        self.current_block_id = net_id

    def c_update(self, dt):
        if self.current_block_id == 0:
            return

        block = self.mgr.getComponent(self.current_block_id)

        getInput = self.getInput

        if getInput('primary_pressed'):
            self.resetInput('primary_pressed')
            self.holding = True
            block.addHold()

        if getInput('primary_released'):
            self.resetInput('primary_released')
            self.holding = False
            block.open()

        if getInput('secondary_pressed'):
            self.resetInput('secondary_pressed')
            block.flag()


class Block(Component):
    def c_register(self):
        self.registerAttribute('x', Pack.UCHAR)
        self.registerAttribute('y', Pack.UCHAR)
        self.registerAttribute('over', Pack.UCHAR)
        self.registerAttribute('held', Pack.UCHAR)
        self.registerAttribute('opened', Pack.UCHAR)
        self.registerAttribute('flagged', Pack.UCHAR)
        self.registerAttribute('count', Pack.UCHAR)
        self.registerAttribute('isMine', Pack.UCHAR)

        self.registerRPC('open', self.process_open_signal,
            [Pack.UCHAR, Pack.UCHAR])
            
    def c_refresh_attributes(self):
        self.setAttribute('over', self.over)
        self.setAttribute('held', self.held)
        self.setAttribute('opened', self.opened)
        self.setAttribute('flagged', self.flagged)
        if self.opened:
            self.setAttribute('count', self.count)
            self.setAttribute('isMine', self.isMine)

    def c_setup(self):
        attributes = self._attributes

        self.x = attributes['x']
        self.y = attributes['y']
        self.over = attributes['over']
        self.held = attributes['held']
        self.opened = attributes['opened']
        self.flagged = attributes['flagged']
        self.count = attributes['count']
        self.isMine = attributes['isMine']

        # Create the game object
        scene = bge.logic.getCurrentScene()
        ob = scene.addObject('Block', self.mgr.owner)
        ob.worldPosition = [self.x, self.y, 0.0]

        self.ob = ob
        ob['component'] = self

        self.refresh()
        
    def addHover(self):
        if self.opened or self.flagged:
            return

        self.over += 1
        if self.over == 1 and self.held == 0:
            self.ob.replaceMesh('Block_hover')

    def removeHover(self):
        if self.opened or self.flagged:
            return

        if self.over == 0:
            print ("Already 0 hover?")
            return

        self.over -= 1
        if self.over == 0:
            self.ob.replaceMesh('Block')

        self._attributes['over'] = self.over

    def addHold(self):
        if self.opened or self.flagged:
            return

        self.held += 1
        if self.held == 1:
            self.ob.replaceMesh('Block_pressed')

        self._attributes['held'] = self.held

    def removeHold(self):
        if self.opened or self.flagged:
            return

        if self.held == 0:
            print ("Already 0 hold?")
            return

        self.held -= 1
        if self.held == 0:
            self.ob.replaceMesh('Block_hover')

        self._attributes['held'] = self.held

    def open(self):
        if self.opened or self.flagged:
            return

        if not self.held:
            return

        self.opened = 1

        if self.mgr.hostmode == 'server':
            new = self.ob.scene.addObject('Uncovered', self.ob)
            self.ob.endObject()
            self.ob = new

            text = new.children[0]
            if self.isMine:
                text['Text'] = "X"
                text.color = self.mgr.game.colors[0]
            elif self.count == 0:
                text['Text'] = ""
                text.color = self.mgr.game.colors[0]
            else:
                text['Text'] = str(self.count)
                text.color = self.mgr.game.colors[self.count]

            self._packer.pack('open', [self.count, self.isMine])

            # And recursively open adjacent blocks if count = 0
            if self.count == 0:
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        if dx == 0 and dy == 0:
                            continue

                        x = self.x + dx
                        y = self.y + dy

                        if (0 <= x < 10) and (0 <= y < 10):
                            other = self.mgr.game.grid[x][y]
                            other.held = 1
                            other.open()

                            # Others need to be signalled as well
                            other._packer.pack('open', [other.count, other.isMine])

    def process_open_signal(self, data):
        self.count = data[0]
        self.isMine = data[1]
        self.opened = 1

        new = self.ob.scene.addObject('Uncovered', self.ob)
        self.ob.endObject()
        self.ob = new

        text = new.children[0]
        if self.isMine:
            text['Text'] = "X"
            text.color = self.mgr.game.colors[0]
        elif self.count == 0:
            text['Text'] = ""
            text.color = self.mgr.game.colors[0]
        else:
            text['Text'] = str(self.count)
            text.color = self.mgr.game.colors[self.count]

    def flag(self):
        if self.opened:
            return

        if self.flagged:
            self.flagged = 0
            self.addHover()

        else:
            #self.removeHover()
            self.over = 0
            #if self.held:
            self.held = 0

            self.flagged = 1
            self.ob.replaceMesh('Block_locked')

    def refresh(self):
        if self.opened:
            self.process_open_signal([self.count, self.isMine])
            return

        if self.flagged:
            self.over = 0
            self.held = 0
            self.ob.replaceMesh('Block_locked')
            return

        if self.held:
            self.ob.replaceMesh('Block_pressed')
            return

        if self.over:
            self.ob.replaceMesh('Block_hover')
            return
