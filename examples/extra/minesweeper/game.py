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

        ## TODO - load from disk
        self.config = {}
        self.config['master'] = {}
        self.config['master']['hostname'] = ''
        self.config['master']['port'] = 64738

        self.systems = {}

        ## Initialize core systems.  These will tic every frame
        if mode == netplay.MODE_SERVER or mode == netplay.MODE_OFFLINE:
            self.systems['Server'] = netplay.Server(self, mode=mode)
            self.systems['Component'] = netplay.ServerComponentSystem(self)

            serversystem = self.systems['Server']
            serversystem.onConnect = self.Server_onConnect
            serversystem.onDisconnect = self.Server_onDisconnect

            # Spawn blocks
            self.grid = []

            self.generate()

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
        self.last_time = time.time()

        self.init = True

    def generate(self):
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
        now = time.time()
        dt = now - self.last_time
        self.last_time = now

        # Update the systems
        for system in list(self.systems.values()):
            system.update(dt)


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
