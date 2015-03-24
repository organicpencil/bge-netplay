import mathutils
import time
from netplay import Component, Pack


def SPAWN_CHAT(mgr):
    comp = mgr.spawnComponent('Chat')
    comp._attributes['username'] = 'unnamed'
    comp._send_attributes()
    return comp


class Chat(Component):
    def c_register(self):
        # Attributes are used for spawning the object on other clients
        self.registerAttribute('username', Pack.STRING)

        self.registerRPC('change_username', self.change_username,
                [Pack.STRING], reliable=True)

        # Replicate false so only the server will process it
        self.registerRPC('raw_public_chat', self.raw_public_chat,
                [Pack.STRING], reliable=True, replicate=False)

        # Replicate false to ensure clients can't sent un-audited chat
        self.registerRPC('public_chat', self.public_chat,
                [Pack.STRING], reliable=False, replicate=False)

    def c_setup(self):
        # Runs when the object is spawned
        #self.username = self.getAttribute('username')
        return

    def c_refresh_attributes(self):
        # You know, this is rather counter-productive.
        # Would it not be better to access the attributes dict directly?
        #self.setAttribute('username', self.playername)
        return

    def c_destroy(self):
        #self.ob.endObject()
        None

    def change_username(self, data):
        print ("FIXME - need server side audit of name change")
        newname = data[0]
        oldname = self.getAttribute('username')
        self.setAttribute('username', newname)

        message = "%s renamed to %s" % (oldname, newname)
        self.mgr.game.systems['Input'].addChat("SYSTEM", message)

    def raw_public_chat(self, data):
        # Not replicated to other clients, so only the server processes
        text = data[0]
        ## Perform audits
        # Ensure data is within size limit
        text = text[:50]

        # Ship to clients
        self._packer.pack('public_chat', [text])

        if self.mgr.hostmode == 'server':
            self.mgr.game.systems['Input'].addChat(self.getAttribute('username'), text)

    def public_chat(self, data):
        if self.mgr.hostmode == 'server':
            print ("WARNING - client attempting to send chat without audit...")
            return

        self.mgr.game.systems['Input'].addChat(self.getAttribute('username'), data[0])


