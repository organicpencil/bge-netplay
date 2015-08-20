import time
import netplay
from chat_ui import Chat

import components  # Must be imported for components to register


class Game:
    def __init__(self, owner, mode=netplay.MODE_SERVER):
        self.owner = owner

        ## TODO - load from disk
        self.config = {}
        self.config['master'] = {}
        self.config['master']['hostname'] = ''
        self.config['master']['port'] = 64738

        self.systems = {}

        ## Initialize core systems.  These will tic every logic frame.
        if mode == netplay.MODE_SERVER or mode == netplay.MODE_OFFLINE:
            self.systems['Server'] = netplay.Server(self, mode=mode)
            self.systems['Component'] = netplay.ServerComponentSystem(self)

            server = self.systems['Server']
            server.onConnect = self.Server_onConnect
            server.onDisconnect = self.Server_onDisconnect

        else:
            self.systems['Client'] = netplay.Client(self, server_ip=owner['ip'])
            self.systems['Component'] = netplay.ClientComponentSystem(self)

        self.systems['Input'] = Chat(self)

        self.last_time = time.monotonic()

        # Hack to allow non-dedicated servers.  Doesn't really belong here.
        if mode == netplay.MODE_SERVER or mode == netplay.MODE_OFFLINE:
            c = self.systems['Component']
            p = components.SPAWN_CHAT(c)
            self.systems['Input'].setTarget(p)

    def Server_onConnect(self, client_id):
        # Spawn a player component and give input permission
        c = self.systems['Component']
        p = components.SPAWN_CHAT(c)
        p.givePermission(client_id)

    def Server_onDisconnect(self, client_id):
        # Find the player component that matches the ID
        c = self.systems['Component']
        for comp in c.active_components_:
            if comp is not None:
                if comp.hasPermission(client_id):
                    # Destroy the player component
                    c.freeComponent(comp)
                    return

    def update(self):
        now = time.monotonic()
        dt = min(now - self.last_time, 0.2)
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
