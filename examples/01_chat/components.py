import mathutils
import time
from netplay import Component, Pack


class ChatUser(Component):
    def _register(self):
        self.register_attribute('username', Pack.STRING, "")

        """
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
        """
        self.RPC_Server('change_username', self.change_username,
                [Pack.STRING])
        self.RPC_Client('recv_change_username', self.recv_change_username,
                [Pack.STRING])

        self.RPC_Server('public_chat', self.public_chat,
                [Pack.STRING])
        self.RPC_Client('recv_public_chat', self.recv_public_chat,
                [Pack.STRING])

        self.RPC_Server('private_chat', self.private_chat,
                [Pack.STRING, Pack.STRING])
        self.RPC_Client('recv_private_chat', self.recv_private_chat,
                [Pack.STRING, Pack.STRING])

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

    def change_username(self, data):
        # Used for a server-side RPC
        new = data[0]
        msg = None
        invalid = ['>', 'Server', 'server']
        for inv in invalid:
            if inv in new:
                print ("invalid name")
                msg = "invalid name"
                break

        if msg is None:
            nameList = self.mgr.game.nameList
            for name in nameList:
                if name == new:
                    msg = 'name in use'
                    break

        if msg is not None:
            # Get the encoded data
            bdata, reliable = self.getRPCData('recv_private_chat',
                    [msg, 'Server'])


            # Queue to sender and recipient
            serv = self.mgr.game.systems['Server']

            for send_id in self.client_permission_list_:
                sender = serv.client_list[send_id]
                sender.queue(bdata, reliable)

            # Normally don't display chat on server, but for testing purposes...
            if not len(self.client_permission_list_):
                self.recv_private_chat([msg, 'Server'])

            return

        # Notify all clients
        """
        bdata, reliable = self.getRPCData('recv_change_username', [new])

        s = self.mgr.game.systems['Server']
        for c in s.client_list:
            if c is not None:
                c.queue(bdata, reliable)
        """
        # Actually, since all clients are notified we can use the default
        # RPC call
        self.call_rpc('recv_change_username', [new])

        # Normally don't display chat on server, but for testing purposes...
        self.recv_change_username([new])

    def recv_change_username(self, data):
        old = self.getAttribute('username')
        new = data[0]

        self.setAttribute('username', new)

        nameList = self.mgr.game.nameList
        nameList.remove(old)
        nameList.append(new)

        text = "".join([old, " renamed to ", new, "\n"])
        self.mgr.game.systems['Input'].addChat(text)

    def public_chat(self, data):
        text = data[0]

        # Clean it

        # Forward to all clients
        self.call_rpc('recv_public_chat', [text])

        # This is a server RPC.  Ideally nobody plays on the server,
        # but we will display chat for testing purposes
        self.recv_public_chat(data)

    def recv_public_chat(self, data):
        username = self.getAttribute('username')
        text = "".join([username, ": ", data[0], "\n"])
        self.mgr.game.systems['Input'].addChat(text)

    def private_chat(self, data):
        other = None
        for c in self.mgr.active_components_:
            if c is not None:
                if c.getAttribute('username') == data[1]:
                    other = c
                    break

        if other is not None:
            text = data[0]

            # Clean it

            # Get the encoded data
            sendname = self.getAttribute('username')
            bdata, reliable = self.getRPCData('recv_private_chat',
                    [text, sendname])

            # Queue to sender and recipient
            serv = self.mgr.game.systems['Server']

            for send_id in self.client_permission_list_:
                sender = serv.client_list[send_id]
                sender.queue(bdata, reliable)

            for recp_id in other.client_permission_list_:
                recipient = serv.client_list[recp_id]
                recipient.queue(bdata, reliable)

            # Normally don't display chat on server, but for testing purposes...
            if (not len(self.client_permission_list_)) or (not len(other.client_permission_list_)):
                self.recv_private_chat([text, sendname])

    def recv_private_chat(self, data):
        username = self.getAttribute('username')
        text = "".join([data[1], " -> ", username, ": ", data[0], "\n"])
        self.mgr.game.systems['Input'].addChat(text)