## PLACEHOLDER - LIKELY BROKEN

import bge
import mathutils
import time

from netplay import Component, Pack


## Call these on the server
def SPAWN_PLAYER(mgr, playername):
    comp = mgr.spawnComponent('Player')
    comp.setup([playername, 0])
    comp.send_state()
    return comp


def SPAWN_BLOCK(mgr, x, y):
    comp = mgr.spawnComponent('Block')
    comp.setup([x, y, 0, 0, 0, 0, 0, 0])
    comp.send_state()
    return comp
##


class Player(Component):
    def c_register_setup(self):
        self.packer.registerPack('setup', self.setup,
            [Pack.STRING, Pack.USHORT])

    def c_getStateData(self):
        p_id = self.packer.pack_index['setup']
        dataprocessor = self.packer.pack_list[p_id]
        data = [self.playername, self.current_block_id]

        return dataprocessor.getBytes(self.net_id, p_id, data)

    def send_state(self):
        # Sent to each client once, not the new clients though...
        # Much duplication with the above function
        self.packer.pack('setup', [self.playername, self.current_block_id])

    def setup(self, data):
        playername = data[0]
        self.current_block_id = data[1]  # Currently hovered block

        print (playername)

        self.registerInput('primary_pressed')
        self.registerInput('primary_released')
        self.registerInput('secondary_pressed')

        # True when mouse is held
        self.holding = False

        self.playername = playername

        self.packer.registerPack('current_block', self.setBlock,
            [Pack.USHORT])

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
        Component.c_update(self, dt)
        block = self.mgr.getComponent(self.current_block_id)

        getInput = self.getInput

        if getInput('primary_pressed'):
            self.setInput('primary_pressed', 0, False)
            self.holding = True
            block.addHold()

        if getInput('primary_released'):
            self.setInput('primary_released', 0, False)
            self.holding = False
            block.open()

        if getInput('secondary_pressed'):
            self.setInput('secondary_pressed', 0, False)
            block.flag()


class Block(Component):
    def c_register_setup(self):
        self.packer.registerPack('setup', self.setup,
            [Pack.UCHAR, Pack.UCHAR, Pack.UCHAR, Pack.UCHAR, Pack.UCHAR, Pack.UCHAR, Pack.UCHAR, Pack.UCHAR])

    def c_getStateData(self):
        p_id = self.packer.pack_index['setup']
        dataprocessor = self.packer.pack_list[p_id]

        if self.opened:
            count = self.count
            isMine = self.isMine
        else:
            count = 0
            isMine = 0
        data = [self.x, self.y, self.over, self.held, self.opened, self.flagged, count, isMine]

        return dataprocessor.getBytes(self.net_id, p_id, data)

    def send_state(self):
        # Sent on initial creation (c_getStateData is used for new clients)
        self.packer.pack('setup', [self.x, self.y, self.over, self.held, self.opened, self.flagged, self.count, self.isMine])

        """ Replicated variables would be cool
        # Changes to these variables automatically replicate to other clients
        # (data type, initial value)
        self.x = self.packer.replicate(Pack.UCHAR, 0)
        self.y = self.packer.replicate(Pack.UCHAR, 0)
        self.over = self.packer.replicate(Pack.UCHAR, 0)
        self.held = self.packer.replicate(Pack.UCHAR, 0)
        self.opened = self.packer.replicate(Pack.UCHAR, 0)
        self.flagged = self.packer.replicate(Pack.UCHAR, 0)
        """

    def setup(self, data):
        self.x = data[0]
        self.y = data[1]
        self.over = data[2]  # Number of players hovering over the block
        self.held = data[3]  # Number of players holding mouse on the block
        self.opened = data[4]
        self.flagged = data[5]
        self.count = data[6]  # Will always be 0 on clients unless opened
        self.isMine = data[7]  # Will always be 0 on clients unless opened

        #self.registerInput('addHover')
        #self.registerInput('removeHover')
        #self.registerInput('addHold')
        #self.registerInput('removeHold')
        #self.registerInput('open')
        #self.registerInput('flag')

        self.packer.registerPack('open', self.process_open_signal, [Pack.UCHAR, Pack.UCHAR])

        # Create the GameObject
        scene = bge.logic.getCurrentScene()
        ob = scene.addObject('Block', self.mgr.owner)
        ob.worldPosition = [self.x, self.y, 0.0]
        #if rot is not None:
        #    ob.worldOrientation = rot

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

    def addHold(self):
        if self.opened or self.flagged:
            return

        self.held += 1
        if self.held == 1:
            self.ob.replaceMesh('Block_pressed')

    def removeHold(self):
        if self.opened or self.flagged:
            return

        if self.held == 0:
            print ("Already 0 hold?")
            return

        self.held -= 1
        if self.held == 0:
            self.ob.replaceMesh('Block_hover')

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

            self.packer.pack('open', [self.count, self.isMine])

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
                            other.packer.pack('open', [other.count, other.isMine])

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
            """
            new = self.ob.scene.addObject('Uncovered', self.ob)
            self.ob.endObject()
            self.ob = new
            """
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