import bge
import collections
from netplay import packer, component
import compz
import logging


def define_tables():
    tabledef = packer.TableDef('ChatSetup')
    tabledef.define('uint16', 'id')
    # One limitation with tables is that you can only have 1 json definition
    # But that's OK because it can be a container
    tabledef.define('json', 'messages')
    tabledef.component = ChatWindow

    tabledef = packer.TableDef('MessageToServer')
    tabledef.define('uint16', 'id')
    tabledef.define('json', 'message')

    tabledef = packer.TableDef('MessageToClient')
    tabledef.define('uint16', 'id')
    tabledef.define('json', 'fullmessage')


class ChatWindow(component.NetComponent):
    obj = None

    def start(self):
        None

    def start_server(self):
        self.users = []
        self.messages = collections.deque()

    def MessageToServer(self, table):
        fullmsg = "{}: {}".format(table.source, table.get('message'))
        self.messages.appendleft(fullmsg)
        if len(self.messages) > 12:
            self.messages.pop()

        logging.info("Chat: " + fullmsg)

        table = packer.Table('MessageToClient')
        table.set('id', self.net_id)
        table.set('fullmessage', fullmsg)
        buff = packer.to_bytes(table)

        net = bge.logic.netplay
        for c in net.clients:
            if c is not None:
                # Queues for sending
                c.send_reliable(buff)

    def MessageToClient(self, table):
        fullmsg = table.get('fullmessage')
        self.push_message(fullmsg)

    def send_click(self, sender):
        table = packer.Table('MessageToServer')
        table.set('id', self.net_id)
        table.set('message', self.entry.text)
        print (self.entry.text)
        buff = packer.to_bytes(table)
        self.entry.text = ""

        bge.logic.netplay.send_reliable(buff)

    def ChatSetup(self, table):
        self.c = c = compz.Compz()

        stylepath = bge.logic.expandPath('//../common/style/')
        panelStyle = compz.Style(name="panel", stylesPath=stylepath)
        buttonStyle = compz.Style(name="button", stylesPath=stylepath)
        entryStyle = compz.Style(name="entry", stylesPath=stylepath)

        # Needs to be a grid panel, I think
        # That or 2 separate panels
        panel = compz.Panel(panelStyle)
        p = bge.render.getWindowHeight() - 64
        panel.position = [32, p]
        panel.width = 100
        panel.height = 32
        c.addComp(panel)

        send = compz.Button("Send", buttonStyle)
        send.events.set(compz.EV_MOUSE_CLICK, self.send_click)
        #server.icon = compz.Icon(stylepath + 'network-server.png')
        panel.addComp(send)

        panel = compz.Panel(panelStyle)
        panel.position = [128, p]
        panel.width = bge.render.getWindowWidth() - 160
        panel.height = 32
        c.addComp(panel)

        self.entry = entry = compz.Entry(style=entryStyle)
        panel.addComp(entry)

        panel = compz.Panel(panelStyle)
        panel.position = [32, 32]
        panel.width = bge.render.getWindowWidth() - 64
        panel.height = p - 48
        c.addComp(panel)

        self.labels = []

        for i in range(0, 12):
            lbl = panel.addComp(compz.Label("Empty"))
            self.labels.append(lbl)

        # Show existing messages
        messages = table.get('messages')
        for fullmsg in messages:
            self.push_message(fullmsg)

        #client = compz.Button("Client", buttonStyle)
        #client.events.set(compz.EV_MOUSE_CLICK, self.start_client)
        #client.icon = compz.Icon(stylepath + 'computer.png')

        #end = compz.Button("Exit", buttonStyle)
        #end.events.set(compz.EV_MOUSE_CLICK, self.end_game)
        #end.icon = compz.Icon(stylepath + 'application-exit.png')

        #panel.addComp(client)
        #panel.addComp(end)

    def push_message(self, fullmsg):
        labels = self.labels
        total = len(labels)
        for i in range(0, total):
            if i < total - 1:
                labels[i].text = labels[i + 1].text
            else:
                labels[i].text = fullmsg

    def update_client(self):
        self.c.update()

    def serialize(self):
        data = list(self.messages)

        table = packer.Table('ChatSetup')
        table.set('id', self.net_id)
        table.set('messages', data)

        return packer.to_bytes(table)


def on_connect(peerID):
    bge.logic.chat.permissions.append(peerID)


def on_disconnect(peerID):
    bge.logic.chat.permissions.append(peerID)


def register_chat(cont):
    owner = cont.owner
    if 'init' in owner:
        return

    owner['init'] = True
    define_tables()

    if bge.logic.netplay.server:
        bge.logic.chat = ChatWindow(None)
        bge.logic.netplay.on_connect = on_connect
        bge.logic.netplay.on_disconnect = on_disconnect