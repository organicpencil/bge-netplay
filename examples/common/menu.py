import bge
import compz
from netplay import host


class Menu:
    def __init__(self, cont):
        self.cont = cont

        skin = bge.logic.expandPath('//../common/skin.png')
        font = bge.logic.expandPath('//../common/Anonymous Pro.ttf')
        style = compz.Style(skin, font)
        icons = bge.logic.expandPath('//../common/icons/')

        self.c = c = compz.Compz(style)

        panel = compz.Panel()
        panel.position = [50, 50]
        panel.width = 100
        panel.height = 94
        c.addComp(panel)

        server = compz.Button("Server")
        server.events.set(compz.EV_MOUSE_CLICK, self.start_server)
        server.icon = compz.Icon(icons + 'network-server.png')

        client = compz.Button("Client")
        client.events.set(compz.EV_MOUSE_CLICK, self.start_client)
        client.icon = compz.Icon(icons + 'computer.png')

        end = compz.Button("Exit")
        end.events.set(compz.EV_MOUSE_CLICK, self.end_game)
        end.icon = compz.Icon(icons + 'application-exit.png')

        panel.addComp(server)
        panel.addComp(client)
        panel.addComp(end)

    def start_server(self, sender):
        bge.logic.netplay = host.ServerHost()
        bge.logic.getCurrentScene().replace('Scene')

    def start_client(self, sender):
        bge.logic.netplay = host.ClientHost()
        bge.logic.getCurrentScene().replace('Scene')

    def end_game(self, sender):
        bge.logic.endGame()

    def update(self):
        self.c.update()


def main(cont):
    owner = cont.owner
    m = owner.get('menu', None)
    if m is None:
        owner['menu'] = Menu(cont)
    else:
        m.update()

"""
from bge import logic as g
import compz
cont = g.getCurrentController()
o = cont.owner

if "init" not in o:
    o["C"] = compz.Compz()

    btnStyle = compz.Style(name="button", stylesPath=g.expandPath("//default/"))
    panelStyle = compz.Style(name="panel", stylesPath=g.expandPath("//default/"))
    entryStyle = compz.Style(name="entry", stylesPath=g.expandPath("//default/"))

    pan = compz.Panel(panelStyle)
    pan.position = [20, 20]
    pan.width = 120
    pan.height = 200
    o["C"].addComp(pan)

    text = compz.Entry(style=entryStyle)

    passwd = compz.Entry(style=entryStyle)
    passwd.text = "MyPassword"
    passwd.masked = True

    def click(sender):
        print("Clicked on button " + sender.text)
        text.text = sender.text

    play = compz.Button("Play", btnStyle)
    play.events.set(compz.EV_MOUSE_CLICK, click)
    play.icon = compz.Icon(g.expandPath("//control_play.png"))

    options = compz.Button("Options", btnStyle)
    options.events.set(compz.EV_MOUSE_CLICK, click)
    options.icon = compz.Icon(g.expandPath("//options.png"))

    exit = compz.Button("Exit", btnStyle)
    exit.events.set(compz.EV_MOUSE_CLICK, click)
    exit.icon = compz.Icon(g.expandPath("//door_out.png"))

    pan.addComp(play)
    pan.addComp(options)
    pan.addComp(exit)
    pan.addComp(text)
    pan.addComp(passwd)
    pan.addComp(compz.Label("Hello World!"))

    gpan = compz.Panel(panelStyle)
    gpan.position = [10, 10]
    gpan.width = 130
    gpan.height = 200
    gpan.layout = compz.GridLayout()
    o["C"].addComp(gpan)

    gpan.centerOnScreen()

    lbl = gpan.addComp(compz.Label("Click:"))
    lbl.textAlignment = compz.TEXT_ALIGN_RIGHT

    btn = gpan.addComp(compz.Button("Here", btnStyle))
    btn.column = 1
    btn.margin = [2, 6]

    lbl = gpan.addComp(compz.Label("And also:"))
    lbl.row = 1
    lbl.textAlignment = compz.TEXT_ALIGN_RIGHT

    btn = gpan.addComp(compz.Button("Here", btnStyle))
    btn.row = 1
    btn.column = 1
    btn.margin = [2, 6]

    o["init"] = 1
else:
    o["C"].update()
"""
