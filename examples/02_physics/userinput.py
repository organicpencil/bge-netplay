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
        bge.render.showMouse(1)

    def update(self, dt):
        component = self.input_target
        if component is None:
            return

        over = self.owner.sensors['over']
        if over.positive:
            pos = over.hitPosition
            pos[2] = 1.0
            self.input_target.call_rpc('position', [pos[0], pos[1]])