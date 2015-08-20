import mathutils
import time
from netplay import Component, Pack


class ChatUser(Component):
    def _register(self):
        self.register_attribute('username', Pack.STRING, "")

        self.register_rpc('input_change_username', self.input_changeUsername,
                [Pack.STRING], replicate=False)
        self.register_rpc('send_change_username', self.changeUsername,
                [Pack.STRING], server_only=True)

        self.register_rpc('input_public_chat', self.input_chatPublic,
                [Pack.STRING], replicate=False)
        self.register_rpc('send_public_chat', self.chatPublic,
                [Pack.STRING], server_only=True)

        self.register_rpc('input_private_chat', self.input_chatPrivate,
                [Pack.STRING, Pack.STRING], replicate=False, private=True)
        self.register_rpc('send_private_chat', self.chatPrivate,
                [Pack.STRING, Pack.STRING], private=True, server_only=True)

    def _setup(self):
        username = self.getAttribute('username')
        nameList = self.mgr.game.nameList

        # Runs on both server and client... should be in sync
        # Server has authority either way
        if username in nameList:
            new = ""
            num = 1
            while True:
                new = "%s#%d" % (username, num)
                if new in nameList:
                    num += 1
                else:
                    username = new
                    break

            self.setAttribute('username', new)
            username = new

        nameList.append(username)

    def _destroy(self):
        self.mgr.game.nameList.remove(self.getAttribute('username'))

    def input_changeUsername(self, data):
        if self.mgr.hostmode == "server":
            #data[0] = "Cleaned username"
            new = data[0]
            invalid = ['>', 'Server', 'server']
            for inv in invalid:
                if inv in new:
                    self.call_rpc('send_private_chat',
                            ['invalid name', 'Server'])
                    return

            nameList = self.mgr.game.nameList
            for name in nameList:
                if name == new:
                    self.call_rpc('send_private_chat',
                            ['name in use', 'Server'])
                    return

            self.call_rpc('send_change_username', data)

    def changeUsername(self, data):
        old = self.getAttribute('username')
        new = data[0]

        self.setAttribute('username', new)

        nameList = self.mgr.game.nameList
        nameList.remove(old)
        nameList.append(new)

        text = "".join([old, " renamed to ", new, "\n"])
        self.mgr.game.systems['Input'].addChat(text)

    def input_chatPublic(self, data):
        # So when chat originates from the server this way it sends
        # unnecessary data, but no harm is done.  Ideally people wont
        # be playing from the server.  Server messages should interact
        # directly with the send RPC
        if self.mgr.hostmode == "server":
            #data[0] = "Cleaned data"
            self.call_rpc('send_public_chat', data)

    def chatPublic(self, data):
        username = self.getAttribute('username')
        text = "".join([username, ": ", data[0], "\n"])
        self.mgr.game.systems['Input'].addChat(text)

    def input_chatPrivate(self, data):
        if self.mgr.hostmode == "server":
            other = None
            for c in self.mgr.active_components_:
                if c is not None:
                    if c.getAttribute('username') == data[1]:
                        other = c
                        break

            if other is not None:
                #data[0] = "Cleaned private message"
                sender = self.getAttribute('username')
                other.call_rpc('send_private_chat', [data[0], sender])

    def chatPrivate(self, data):
        username = self.getAttribute('username')
        text = "".join([data[1], " -> ", username, ": ", data[0], "\n"])
        self.mgr.game.systems['Input'].addChat(text)