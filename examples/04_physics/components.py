import math
import mathutils
import time
import bge
from netplay import Component, DynamicComponent, RigidComponent, Pack


class Dynamic_Cube(DynamicComponent):
    def __init__(self, mgr, net_id):
        DynamicComponent.__init__(self, mgr, net_id)
        self.obj = 'dynamic_cube'
        self.was_idle = True

    def _register(self):
        DynamicComponent._register(self)
        self.register_rpc('idle', self.setIdle, Pack.UCHAR)

    def _server_update(self, dt):
        DynamicComponent._server_update(self, dt)

        if self._idle != self.was_idle:
            self.was_idle = self._idle

            if self._idle:
                self.call_rpc('idle', [1])
            else:
                self.call_rpc('idle', [0])

    def setIdle(self, data):
        if data[0] == 1:
            self.ob.color = [0.0, 0.0, 1.0, 1.0]
        else:
            self.ob.color = [0.5, 0.5, 1.0, 1.0]


class Rigid_Cube(RigidComponent):
    def __init__(self, mgr, net_id):
        RigidComponent.__init__(self, mgr, net_id)
        self.obj = 'rigid_cube'
        self.was_idle = True

    def _register(self):
        RigidComponent._register(self)
        self.register_rpc('idle', self.setIdle, Pack.UCHAR)

    def _server_update(self, dt):
        RigidComponent._server_update(self, dt)

        if self._idle != self.was_idle:
            self.was_idle = self._idle

            if self._idle:
                self.call_rpc('idle', [1])
            else:
                self.call_rpc('idle', [0])

    def setIdle(self, data):
        if data[0] == 1:
            self.ob.color = [1.0, 0.0, 0.0, 1.0]
        else:
            self.ob.color = [1.0, 0.5, 0.5, 1.0]


class Player(DynamicComponent):
    def __init__(self, mgr, net_id):
        DynamicComponent.__init__(self, mgr, net_id)
        self.obj = 'player'
        self.was_idle = True

    def setIdle(self, data):
        if data[0] == 1:
            self.ob.color = [0.0, 1.0, 0.0, 1.0]
        else:
            self.ob.color = [0.5, 1.0, 0.5, 1.0]

    def _register(self):
        DynamicComponent._register(self)
        self.register_attribute('t_x', Pack.FLOAT, 0.0)
        self.register_attribute('t_y', Pack.FLOAT, 0.0)

        self.register_rpc('position', self.setTargetPosition,
                [Pack.FLOAT, Pack.FLOAT])

        self.register_rpc('idle', self.setIdle, Pack.UCHAR)

    def _setup(self):
        DynamicComponent._setup(self)
        attr = self.getAttribute

        self.target_position = [attr('t_x'), attr('t_y'), 1.0]

    def _update_attributes(self):
        DynamicComponent._update_attributes(self)
        pos = self.target_position
        self.setAttribute('t_x', pos[0])
        self.setAttribute('t_y', pos[1])

    def _server_update(self, dt):
        vec = self.ob.getVectTo(self.target_position)
        if vec[0] > 0.5:
            self.ob.setLinearVelocity(vec[1] * (vec[0] * 3.0), False)
        else:
            self.ob.setLinearVelocity((0.0, 0.0, 0.0), False)

        DynamicComponent._server_update(self, dt)

        if self._idle != self.was_idle:
            self.was_idle = self._idle

            if self._idle:
                self.call_rpc('idle', [1])
            else:
                self.call_rpc('idle', [0])

    def setTargetPosition(self, data):
        self.target_position = [data[0], data[1], 1.0]