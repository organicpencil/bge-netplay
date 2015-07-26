## PLACEHOLDER - LIKELY BROKEN

import bge
import collections
import copy
import time

# Default controls are defined here
DEFAULTS = {
    'primary': bge.events.LEFTMOUSE,
    'secondary': bge.events.RIGHTMOUSE,
    }


class InputSystem:
    def __init__(self, game):
        self.game = game
        self.owner = game.owner

        # Copy the default controls.
        # Later we can modify inputDict to load custom controls
        self.inputDict = copy.deepcopy(DEFAULTS)

        # Handy switch for disabling user input
        self.locked = False

        # References the component that receives input
        self.input_target = None

        # We'll be needing the cursor for our game
        bge.render.showMouse(1)

    def setTarget(self, component):
        # Set the current input target or None, can be called at any time
        self.input_target = component

    def disable(self):
        # Abstraction for disabling input
        self.locked = True

    def enable(self):
        # Abstraction for enabling input
        self.locked = False

    def update(self, dt):
        component = self.input_target
        if component is None:
            return

        if self.locked:
            return

        timer = self.game.timer
        if timer.stopped:
            return

        iDict = self.inputDict
        events = bge.logic.mouse.events

        # We only need KX_INPUT_ACTIVE for our needs
        JUST_ACTIVATED = bge.logic.KX_INPUT_JUST_ACTIVATED
        JUST_RELEASED = bge.logic.KX_INPUT_JUST_RELEASED
        #ACTIVE = bge.logic.KX_INPUT_ACTIVE
        over = self.game.owner.sensors['over']
        if over.positive:
            other = over.hitObject
            if other['block'] != -1:
                block = other['BLOCK']

                coords = [block.x, block.y]
                if component.current_block != coords:
                    component.setBlock(coords)
                    component._packer.pack('set_current_block', coords)
            else:
                return
        else:
            return

        if events[iDict['primary']] == JUST_ACTIVATED:
            component.setInput('primary_pressed', 1)
        elif events[iDict['primary']] == JUST_RELEASED:
            component.setInput('primary_released', 1)

        if events[iDict['secondary']] == JUST_ACTIVATED:
            component.setInput('secondary_pressed', 1)
