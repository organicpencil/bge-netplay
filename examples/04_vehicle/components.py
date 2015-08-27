import math
import mathutils
import time
import bge
from netplay import Component, MovingComponent, Pack


class Input_Dummy(Component):
    def __init__(self, component):
        Component.__init__(self, component.mgr, component.net_id)
        self.component = component

    def _register(self):
        self.register_input('forward')
        self.register_input('reverse')
        self.register_input('left')
        self.register_input('right')
        self.register_input('brake')

    def update(self):
        if self.input_changed_:
            self.input_changed_ = False
            state = self.getInputState()
            self.component._packer.pack('_send_input', [state])


class Car(MovingComponent):
    def _register(self):
        MovingComponent._register(self)
        self.register_input('forward')
        self.register_input('reverse')
        self.register_input('left')
        self.register_input('right')
        self.register_input('brake')

        #self.register_attribute('steer', Pack.CHAR, 0)

        #self.RPC_Client('sync_steering', self.sync_steering, [Pack.CHAR])

    def _setup(self):
        self.obj = 'car'
        MovingComponent._setup(self)

        self.ob.restoreDynamics()

        self.tireObj = 'wheel'
        # Tire positions relative to carObj origin
        self.tirePos = [[-2.5, 2.5, -1.0],  # front left
                        [2.5, 2.5, -1.0],  # front right
                        [-2.5, -2.5, -1.0],  # rear left
                        [2.5, -2.5, -1.0]]  # rear right

        self.tireRadius = [1.0,  # front left
                           1.0,  # front right
                           1.0,  # rear left
                           1.0]  # rear right

        # Tire suspension height
        self.tireSuspension = [0.3,  # front left
                               0.3,  # front right
                               0.3,  # rear left
                               0.3]  # rear right

        # Tire suspension angle
        self.tireAngle = [[0.0, 0.0, -1.0],  # front left
                          [0.0, 0.0, -1.0],  # front right
                          [0.0, 0.0, -1.0],  # rear left
                          [0.0, 0.0, -1.0]]  # rear right

        # Tire axis attached to axle
        self.tireAxis = [[-1.0, 0.0, 0.0],  # front left
                         [-1.0, 0.0, 0.0],  # front right
                         [-1.0, 0.0, 0.0],  # rear left
                         [-1.0, 0.0, 0.0]]  # rear right

        # Which tires have steering
        self.tireSteering = [True,  # front left
                             True,  # front right
                             False,  # rear left
                             False]  # rear right

        # Grip factor (friction)
        self.tireGrip = [30.0,  # front left
                         30.0,  # front right
                         30.0,  # rear left
                         30.0]  # rear right

        # Tires that apply power (fwd/rwd/awd/etc)
        self.powerTires = [True,  # front left
                           True,  # front right
                           False,  # rear left
                           False]  # rear right

        # Suspension compression
        self.compression = [6.0,  # front left
                            6.0,  # front right
                            6.0,  # rear left
                            6.0]  # rear right

        # Suspension damping
        self.damping = [1.0,  # front left
                        1.0,  # front right
                        1.0,  # rear left
                        1.0]  # rear right

        # Suspension stiffness
        self.stiffness = [18.0,  # front left
                          18.0,  # front right
                          18.0,  # rear left
                          18.0]  # rear right

        # Roll influence
        self.roll = [0.00,  # front left
                     0.00,  # front right
                     0.00,  # rear left
                     0.00]  # rear right

        self.constraint_setup()
        #self.sync_steering([self.getAttribute('steer')])

    def constraint_setup(self):
        ### Vehicle constraint setup
        ob = self.ob
        scene = ob.scene

        phys_ID = ob.getPhysicsId()

        constraint = bge.constraints.createConstraint(phys_ID, 0, 11)
        constraint_ID = constraint.getConstraintId()

        constraint = bge.constraints.getVehicleConstraint(constraint_ID)
        self.constraint = constraint

        ### Tire setup
        self.tires = []
        #tirelist = ['_FL', '_FR', '_RL', '_RR']
        for i in range(0, 4):
            tire_ob = scene.addObject(self.tireObj, ob)
            self.tires.append(tire_ob)

            pos = self.tirePos[i]
            suspA = self.tireAngle[i]
            axis = self.tireAxis[i]
            suspH = self.tireSuspension[i]
            radius = self.tireRadius[i]
            steering = self.tireSteering[i]

            constraint.addWheel(tire_ob, pos,
                    suspA, axis, suspH, radius, steering)

        ### Suspension setup
        for i in range(0, 4):
            constraint.setTyreFriction(self.tireGrip[i], i)
            constraint.setSuspensionCompression(self.compression[i], i)
            constraint.setSuspensionDamping(self.damping[i], i)
            constraint.setSuspensionStiffness(self.stiffness[i], i)
            constraint.setRollInfluence(self.roll[i], i)

    """
    def sync_steering(self, data):
        steer = (data[0] / 100.0) * 0.3
        constraint = self.constraint
        for i in range(0, 4):
            if self.tireSteering[i]:
                constraint.setSteeringValue(steer, i)
    """

    """
    def _client_update(self, dt):
        MovingComponent._client_update(self, dt)
        getInput = self.getInput

        steer = 0.0
        brake = 0.0
        if getInput('left'):
            steer += 1.0

        if getInput('right'):
            steer -= 1.0

        if getInput('brake'):
            brake = 1.0

        constraint = self.constraint
        for i in range(0, 4):
            if self.tireSteering[i]:
                constraint.setSteeringValue(steer * 0.3, i)

            constraint.applyBraking(brake * 100.0, i)
    """

    def _update(self, dt):
        getInput = self.getInput

        power = 0.0
        steer = 0.0
        brake = 0.0

        if getInput('forward'):
            power += 1.0

        if getInput('reverse'):
            power -= 1.0

        if getInput('left'):
            steer += 1.0

        if getInput('right'):
            steer -= 1.0

        if getInput('brake'):
            brake = 1.0

        constraint = self.constraint
        for i in range(0, 4):
            if self.powerTires[i]:
                constraint.applyEngineForce(power * -100.0, i)

            if self.tireSteering[i]:
                constraint.setSteeringValue(steer * 0.3, i)

            constraint.applyBraking(brake * 100.0, i)

    def _destroy(self):
        self.ob.endObject()


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