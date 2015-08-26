import bge
import components


class InputSystem:
    def __init__(self, game):
        self.game = game
        self.owner = game.owner

        # References the component that receives input
        self.component = None
        self.cam = None

    def setTarget(self, component):
        # Must be a valid component or None
        self.component = component
        self.input_dummy = components.Input_Dummy(component)
        bge.render.showMouse(1)

        target = self.owner.scene.objects['cam_target']
        target.removeParent()
        target.worldPosition = component.ob.worldPosition
        target.setParent(component.ob)
        #cam.actuators['Camera'].object = component.ob

    def update(self, dt):
        component = self.component
        if component is None:
            return

        events = bge.logic.keyboard.events

        ACTIVE = bge.logic.KX_INPUT_ACTIVE

        input_dummy = self.input_dummy
        if events[bge.events.WKEY] == ACTIVE:
            input_dummy.setInput('forward', 1)
        else:
            input_dummy.setInput('forward', 0)

        if events[bge.events.SKEY] == ACTIVE:
            input_dummy.setInput('reverse', 1)
        else:
            input_dummy.setInput('reverse', 0)

        if events[bge.events.AKEY] == ACTIVE:
            input_dummy.setInput('left', 1)
        else:
            input_dummy.setInput('left', 0)

        if events[bge.events.DKEY] == ACTIVE:
            input_dummy.setInput('right', 1)
        else:
            input_dummy.setInput('right', 0)

        if events[bge.events.SPACEKEY] == ACTIVE:
            input_dummy.setInput('brake', 1)
        else:
            input_dummy.setInput('brake', 0)

        input_dummy.update()