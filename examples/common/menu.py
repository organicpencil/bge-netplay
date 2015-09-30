import bge
import bgui
from bgui import bge_utils


VERSION_MIN = (2, 76, 0)
VERSION_STRING = "2.76"


def CheckVersion():
    try:
        bge.app.version
    except:
        return False

    if VERSION_MIN > bge.app.version:
        return False

    return True


class Menu(bge_utils.System):

    def __init__(self, owner):
        bge_utils.System.__init__(self, theme='theme')
        self.owner = owner

        if not CheckVersion():
            bgui.Label(self, text="Unsupported version of Blender.  Download %s or newer." % VERSION_STRING,
                    pt_size=36,
                    options=bgui.BGUI_CENTERX | bgui.BGUI_CENTERY)
            return

        self.frame = bgui.Widget(self, aspect=1.0, size=[0.9, 0.9],
            pos=[0.05, 0.05])

        server = bgui.FrameButton(self.frame, text="Start Server", size=[0.4, 0.1],
            pos=[0.0, 0.9])
        server.on_click = self.start_server


        bgui.Label(self.frame, text="IP:", pos=[0.0, 0.42], sub_theme='Large')
        self.ip_input = bgui.TextInput(self.frame, text="127.0.0.1", size=[0.4, 0.1],
            pos=[0.2, 0.4])

        client = bgui.FrameButton(self.frame, text="Start Client", size=[0.4, 0.1],
            pos=[0.0, 0.28])
        client.on_click = self.start_client

        # Now setup the scene callback so we can draw
        bge.logic.getCurrentScene().post_draw = [self.render]

    def start_server(self, widget):
        self.owner['mode'] = 0
        self.owner.state = 2
        self.owner.scene.post_draw = []

    def start_client(self, widget):
        self.owner['mode'] = 2
        self.owner['ip'] = self.ip_input.text
        self.owner.state = 2
        self.owner.scene.post_draw = []

    def main(self):
        """A high-level method to be run every frame"""
        # Handle the mouse
        mouse = bge.logic.mouse

        pos = list(mouse.position)
        w = bge.render.getWindowWidth()
        h = bge.render.getWindowHeight()
        pos[0] *= w
        pos[1] = h - (h * pos[1])

        mouse_state = bgui.BGUI_MOUSE_NONE
        mouse_events = mouse.events

        JUST_ACTIVATED = bge.logic.KX_INPUT_JUST_ACTIVATED
        JUST_RELEASED = bge.logic.KX_INPUT_JUST_RELEASED
        ACTIVE = bge.logic.KX_INPUT_ACTIVE

        if mouse_events[bge.events.LEFTMOUSE] == JUST_ACTIVATED:
            mouse_state = bgui.BGUI_MOUSE_CLICK
        elif mouse_events[bge.events.LEFTMOUSE] == JUST_RELEASED:
            mouse_state = bgui.BGUI_MOUSE_RELEASE
        elif mouse_events[bge.events.LEFTMOUSE] == ACTIVE:
            mouse_state = bgui.BGUI_MOUSE_ACTIVE

        self.update_mouse(pos, mouse_state)

        # Handle the keyboard
        keyboard = bge.logic.keyboard

        key_events = keyboard.events
        is_shifted = key_events[bge.events.LEFTSHIFTKEY] == ACTIVE or \
                    key_events[bge.events.RIGHTSHIFTKEY] == ACTIVE

        for key, state in list(keyboard.events.items()):
            if state == bge.logic.KX_INPUT_JUST_ACTIVATED:
                self.update_keyboard(self.keymap[key], is_shifted)

def main(cont):
    owner = cont.owner
    menu = owner.get('menu', None)
    if menu is None:
        owner['menu'] = Menu(owner)
        bge.render.showMouse(1)
    else:
        menu.main()
