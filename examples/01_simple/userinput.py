import bge

class InputSystem:
    def __init__(self, game):
        self.game = game
        self.owner = game.owner
        
        # References the component that receives input
        self.input_target = None
        
    def setTarget(self, component):
        # Must be a valid component or None
        self.input_target = component
        
    def update(self, dt):
        component = self.input_target
        if component is None:
            return
            
        events = bge.logic.keyboard.events
        
        #JUST_ACTIVATED = bge.logic.KX_INPUT_JUST_ACTIVATED
        #JUST_RELEASED = bge.logic.KX_INPUT_JUST_RELEASED
        ACTIVE = bge.logic.KX_INPUT_ACTIVE
        
        if events[bge.events.WKEY] == ACTIVE:
            component.setInput('up_held', 1)
        else:
            component.setInput('up_held', 0)
            
        if events[bge.events.SKEY] == ACTIVE:
            component.setInput('down_held', 1)
        else:
            component.setInput('down_held', 0)
            
        if events[bge.events.AKEY] == ACTIVE:
            component.setInput('left_held', 1)
        else:
            component.setInput('left_held', 0)
            
        if events[bge.events.DKEY] == ACTIVE:
            component.setInput('right_held', 1)
        else:
            component.setInput('right_held', 0)

