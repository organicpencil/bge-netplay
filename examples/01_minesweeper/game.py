import time
import bge
import netplay
from userinput import InputSystem

import components  # Must be imported for components to register
components

# Limit 255x255
GRID_SIZE_X = 10
GRID_SIZE_Y = 10
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

        ## Initialize core systems.  These will tic every frame
        if mode == netplay.MODE_SERVER or mode == netplay.MODE_OFFLINE:
            self.systems['Server'] = netplay.Server(self, mode=mode)
            self.systems['Component'] = netplay.ServerComponentSystem(self)

            serversystem = self.systems['Server']
            serversystem.onConnect = self.Server_onConnect
            serversystem.onDisconnect = self.Server_onDisconnect

            grid = []
            # Spawn blocks
            c = self.systems['Component']

            for x in range(0, GRID_SIZE_X):
                grid.append([])
                for y in range(0, GRID_SIZE_Y):
                    if mode == netplay.MODE_SERVER or mode == netplay.MODE_OFFLINE:
                        #comp = c.spawnComponent('Block')
                        comp = components.SPAWN_BLOCK(c, x, y)

                        grid[x].append(comp)

            self.grid = grid
        else:
            self.systems['Client'] = netplay.Client(self)
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

    def Server_onConnect(self, client_id):
        # Spawn a player component and give input permission
        c = self.systems['Component']
        p = components.SPAWN_PLAYER(c, 'AClient')
        p.givePermission(client_id)

    def Server_onDisconnect(self, client_id):
        print ("FIXME - unhover/hold blocks and delete the player component")

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