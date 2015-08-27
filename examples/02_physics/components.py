import math
import mathutils
import time
import bge
from netplay import Component, MovingComponent, Pack


class Dynamic_Cube(MovingComponent):
    def __init__(self, mgr, net_id):
        MovingComponent.__init__(self, mgr, net_id)
        self.obj = 'dynamic_cube'
        self.was_idle = True

    def _register(self):
        MovingComponent._register(self)
        self.RPC_Client('idle', self.setIdle, Pack.UCHAR)

    def _server_update(self, dt):
        MovingComponent._server_update(self, dt)

        if self._idle != self.was_idle:
            self.was_idle = self._idle

            if self._idle:
                self.call_rpc('idle', [1])
                self.setIdle([1])
            else:
                self.call_rpc('idle', [0])
                self.setIdle([0])

    def setIdle(self, data):
        if data[0] == 1:
            self.ob.color = [0.0, 0.0, 1.0, 1.0]
        else:
            self.ob.color = [0.5, 0.5, 1.0, 1.0]


class Rigid_Cube(MovingComponent):
    def __init__(self, mgr, net_id):
        MovingComponent.__init__(self, mgr, net_id)
        self.obj = 'rigid_cube'
        self.was_idle = True

    def _register(self):
        MovingComponent._register(self)
        self.RPC_Client('idle', self.setIdle, Pack.UCHAR)

    def _server_update(self, dt):
        MovingComponent._server_update(self, dt)

        if self._idle != self.was_idle:
            self.was_idle = self._idle

            if self._idle:
                self.call_rpc('idle', [1])
                self.setIdle([1])
            else:
                self.call_rpc('idle', [0])
                self.setIdle([0])

    def setIdle(self, data):
        if data[0] == 1:
            self.ob.color = [1.0, 0.0, 0.0, 1.0]
        else:
            self.ob.color = [1.0, 0.5, 0.5, 1.0]


class Player(MovingComponent):
    def __init__(self, mgr, net_id):
        MovingComponent.__init__(self, mgr, net_id)
        self.obj = 'player'
        self.was_idle = True

    def setIdle(self, data):
        if data[0] == 1:
            self.ob.color = [0.0, 1.0, 0.0, 1.0]
        else:
            self.ob.color = [0.5, 1.0, 0.5, 1.0]

    def _register(self):
        MovingComponent._register(self)
        self.register_attribute('t_x', Pack.FLOAT, 0.0)
        self.register_attribute('t_y', Pack.FLOAT, 0.0)

        self.RPC_Server('position', self.setTargetPosition,
                [Pack.FLOAT, Pack.FLOAT])

        self.RPC_Client('idle', self.setIdle, Pack.UCHAR)

    def _setup(self):
        MovingComponent._setup(self)
        attr = self.getAttribute

        self.target_position = [attr('t_x'), attr('t_y'), 1.0]

    def _update_attributes(self):
        MovingComponent._update_attributes(self)
        pos = self.target_position
        self.setAttribute('t_x', pos[0])
        self.setAttribute('t_y', pos[1])

    def _server_update(self, dt):
        vec = self.ob.getVectTo(self.target_position)
        if vec[0] > 0.5:
            self.ob.setLinearVelocity(vec[1] * (vec[0] * 3.0), False)
        else:
            self.ob.setLinearVelocity((0.0, 0.0, 0.0), False)

        MovingComponent._server_update(self, dt)

        if self._idle != self.was_idle:
            self.was_idle = self._idle

            if self._idle:
                self.call_rpc('idle', [1])
                self.setIdle([1])
            else:
                self.call_rpc('idle', [0])
                self.setIdle([0])

    def setTargetPosition(self, data):
        self.target_position = [data[0], data[1], 1.0]