import bge
from . import host


def start_server(cont):
    bge.logic.netplay = host.ServerHost()
    owner = cont.owner
    scene = bge.logic.getCurrentScene()
    scene.replace(owner['gamescene'])


def start_client(cont):
    bge.logic.netplay = host.ClientHost()
    owner = cont.owner
    scene = bge.logic.getCurrentScene()
    scene.replace(owner['gamescene'])


def update(self):
    bge.logic.netplay.update()