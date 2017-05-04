import bge
import sys

sys.path.append(bge.logic.expandPath('//../../'))

from netplay import host


class Button:
    def __init__(self, owner):
        self.owner = owner
        owner['button'] = self

    def on_click(self):
        pass


class Menu:
    def __init__(self):
        objects = bge.logic.getCurrentScene().objects

        button = Button(objects['server'])
        button.on_click = self.start_server

        button = Button(objects['client'])
        button.on_click = self.start_client

    def update(self):
        cam = bge.logic.getCurrentScene().active_camera
        mpos = bge.logic.mouse.position
        mvec = cam.getScreenVect(*mpos)
        mvec.negate()
        mvec += cam.worldPosition
        ob, pos, normal = cam.rayCast(mvec, cam, 200.0, 'btn', 1, 1)
        if ob is not None:
            if bge.logic.mouse.events[bge.events.LEFTMOUSE] == bge.logic.KX_INPUT_ACTIVE:
                ob['button'].on_click()

    def start_server(self):
        print ("SERVER")
        bge.logic.netplay = host.ServerHost()
        bge.logic.getCurrentScene().replace('Scene')

    def start_client(self):
        bge.logic.netplay = host.ClientHost()
        bge.logic.getCurrentScene().replace('Scene')


def main(cont):
    owner = cont.owner
    m = owner.get('menu', None)
    if m is None:
        owner['menu'] = Menu()
    else:
        m.update()