import bge


class InputSystem:
    def __init__(self, game):
        self.game = game
        self.owner = game.owner

        # References the component that receives input
        self.input_target = None

        # Mouselook stuff
        self.mouseInit = True
        self.sens = 0.001
        self.invert = 1.0
        self.cap0 = -1.4
        self.cap1 = 1.4
        self.freeMouse = False

    def setTarget(self, comp):
        if self.input_target is not None:
            self.input_target.component.destroyLocal()
            self.input_target = None
        # Must be a valid component or None

        component = comp.createLocal()
        self.input_target = component
        bge.logic.getCurrentScene().active_camera = component.ob_camera
        bge.render.showMouse(0)

    def toggleMouse(self):
        self.freeMouse = not self.freeMouse

        if self.freeMouse:
            bge.render.showMouse(1)
        else:
            bge.render.showMouse(0)

    def update(self, dt):
        component = self.input_target
        if component is None:
            return

        events = bge.logic.keyboard.events

        JUST_ACTIVATED = bge.logic.KX_INPUT_JUST_ACTIVATED
        #JUST_RELEASED = bge.logic.KX_INPUT_JUST_RELEASED
        ACTIVE = bge.logic.KX_INPUT_ACTIVE

        if events[bge.events.WKEY] == ACTIVE:
            component.setInput('forward', 1)
        else:
            component.setInput('forward', 0)

        if events[bge.events.SKEY] == ACTIVE:
            component.setInput('back', 1)
        else:
            component.setInput('back', 0)

        if events[bge.events.AKEY] == ACTIVE:
            component.setInput('left', 1)
        else:
            component.setInput('left', 0)

        if events[bge.events.DKEY] == ACTIVE:
            component.setInput('right', 1)
        else:
            component.setInput('right', 0)

        if events[bge.events.TABKEY] == JUST_ACTIVATED:
            self.toggleMouse()

        events = bge.logic.mouse.events
        if events[bge.events.LEFTMOUSE] == ACTIVE:
            component.setInput('primary', 1)
        else:
            component.setInput('primary', 0)

        if not self.freeMouse:
            self.mouseLook()

        self.input_target.update(dt)

    def mouseLook(self):
        target = self.input_target
        ob = target.ob
        cam = target.ob_camera_armature

        if cam is None:
            print ("Can't do mouselook without a camera...")
            return

        width = bge.render.getWindowWidth()
        height = bge.render.getWindowHeight()

        centerX = int(width / 2)
        centerY = int(width / 2)

        if self.mouseInit:
            self.mouseInit = False
            bge.render.setMousePosition(centerX, centerY)
            return

        """
        # Weird hack to eliminate jumping when toggling mouse control
        # No idea why this happens, or if it even still happens.
        # Code is left over from a project long ago using
        if self.mouseInit > 0:
            self.mouseInit -= 1
            self.cap_0 = -1.5
            self.cap_1 = 1.5

            bge.render.setMousePosition(int(width / 2), int(height / 2))
            return 0
        """

        mpos = list(bge.logic.mouse.position)

        mpos[0] = mpos[0] * width
        mpos[1] = mpos[1] * height

        if int(mpos[0]) == centerX and int(mpos[1]) == centerY:
            return

        w = centerX - mpos[0]
        h = centerY - mpos[1]

        if target.aiming:
            sens = self.sens / 2.0
        else:
            sens = self.sens

        x = w * sens
        y = h * sens * self.invert

        ### Left/Right rotation
        # applyRotation screws up momentum, don't use it on dynamic objects
        rot = ob.worldOrientation.to_euler()
        rot[2] += x
        ob.worldOrientation = rot

        ### Up/Down cap
        rad = cam.worldOrientation.to_euler()

        if y < 0.0 and rad[0] < self.cap0:
            y = 0.0
        if y > 0.0 and rad[0] > self.cap1:
            y = 0.0

        ### Up/Down rotation
        cam.applyRotation([y, 0.0, 0.0], True)

        # Reset mouse position
        bge.render.setMousePosition(centerX, centerY)

        rot = cam.worldOrientation.to_euler()
        # Send delta rotation
        self.input_target.component.call_rpc('send_rotation', [rot[0], rot[2]])