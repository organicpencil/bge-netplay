import time
import random
import bge
import netplay
from userinput import InputSystem

import components  # Must be imported for components to register
components

# Limit 255x255
SIZE_X = 10
SIZE_Y = 10
MINES = 10


class Game:
    def __init__(self, owner, mode=netplay.MODE_OFFLINE):
        self.owner = owner

        ## TODO - load from disk
        self.config = {}
        self.config['master'] = {}
        self.config['master']['hostname'] = ''
        self.config['master']['port'] = 64738

        self.systems = {}

        self.timer = None  # We'll store the game timer here

        self.board = None  # We'll store the game board here

        ## Initialize core systems.  These will tic every frame
        if mode == netplay.MODE_SERVER or mode == netplay.MODE_OFFLINE:
            self.systems['Server'] = netplay.Server(self, mode=mode)
            self.systems['Component'] = netplay.ServerComponentSystem(self)

            serversystem = self.systems['Server']
            serversystem.onConnect = self.Server_onConnect
            serversystem.onDisconnect = self.Server_onDisconnect

            """
            # Spawn blocks and add timer
            self.generate()
            """
            components.SPAWN_BOARD(self.systems['Component'],
                    SIZE_X, SIZE_Y, MINES)
        else:
            self.systems['Client'] = netplay.Client(self, server_ip = owner['ip'])
            self.systems['Component'] = netplay.ClientComponentSystem(self)

        self.systems['Input'] = InputSystem(self)

        if mode == netplay.MODE_SERVER or mode == netplay.MODE_OFFLINE:
            c = self.systems['Component']
            #p = c.spawnComponent('Player')
            p = components.SPAWN_PLAYER(c, 'TheHost')
            self.systems['Input'].setTarget(p)

        ## Used to determine frame time delta.
        self.last_time = time.monotonic()

        self.init = True

    """
    def reset(self):
        # Yellow button pressed!!!
        print ("Resetting board")

        c = self.systems['Component']
        for comp in c.active_components_:
            if comp is not None:
                if type(comp) is components.Player:
                    comp._attributes['current_block_id'] = 0
                    comp._send_attributes()

                elif type(comp) is components.Block:
                    c.freeComponent(comp)
                    continue

                elif type(comp) is components.Timer:
                    c.freeComponent(comp)

                else:
                    # Unspecified component, likely the MainComponent
                    continue

        self.generate()
    """
    """
    def generate(self):
        self.grid = []
        grid = self.grid
        c = self.systems['Component']

        for x in range(0, SIZE_X):
            grid.append([])
            for y in range(0, SIZE_Y):
                block = components.SPAWN_BLOCK(c, x, y)

                grid[x].append(block)

        # Place mines
        used = []
        for i in range(0, MINES):
            rx = random.randint(0, SIZE_X-1)
            ry = random.randint(0, SIZE_Y-1)

            done = False
            while not done:
                done = True

                for u in used:
                    if u[0] == rx and u[1] == ry:
                        done = False

                        rx += 1
                        if rx == SIZE_X:
                            rx = 0
                            ry += 1
                            if ry == SIZE_Y:
                                ry = 0

            block = grid[rx][ry]
            block.isMine = True
            block._attributes['isMine'] = True
            used.append([rx, ry])

        # Calculate adjacent mines
        for x in range(0, SIZE_X):
            for y in range(0, SIZE_Y):
                block = grid[x][y]
                for xx in range(-1, 2):
                    for yy in range(-1, 2):
                        xi = x + xx
                        yi = y + yy

                        if SIZE_X > xi > -1:
                            if SIZE_Y > yi > -1:
                                other = grid[xi][yi]
                                if other.isMine:
                                    block.count += 1
                                    block._attributes['count'] += 1

        # Calculate blocks remaining to be uncovered for win
        self.blocks_remaining = (SIZE_X * SIZE_Y) - MINES

        # Add timer
        components.SPAWN_TIMER(self.systems['Component'])
    """


    def Server_onConnect(self, client_id):
        # Spawn a player component and give input permission
        c = self.systems['Component']
        p = components.SPAWN_PLAYER(c, 'AClient')
        p.givePermission(client_id)

    def Server_onDisconnect(self, client_id):
        # Find the player component that matches the client ID
        c = self.systems['Component']
        for comp in c.active_components_:
            if comp is not None:
                if comp.hasPermission(client_id):
                    # Destroy the player component
                    c.freeComponent(comp)
                    return

    def update(self):
        # Determine delta time
        now = time.monotonic()
        dt = now - self.last_time
        self.last_time = now

        # Update the systems
        for system in list(self.systems.values()):
            system.update(dt)


def resetButton(cont):
    if cont.sensors['click'].positive and cont.sensors['over'].positive:
        owner = cont.owner
        game = owner.get('Game', None)
        if game is not None:
            if game.systems['Component'].hostmode == 'server':
                game.reset()


def main(cont):
    owner = cont.owner

    game = owner.get('Game', None)
    if game is None:
        if 'init' in owner:
            return
        owner['init'] = True
        game = Game(owner, mode=owner['mode'])
        owner['Game'] = game

    game.update()


if __name__ == '__main__':
    main(bge.logic.getCurrentController())
