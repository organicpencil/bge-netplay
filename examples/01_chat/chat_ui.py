import bge
import bgui
from bgui import bge_utils
import collections


class Chat(bge_utils.System):

    def __init__(self, owner):
        bge_utils.System.__init__(self, theme='theme')
        self.owner = owner
        self.component = None

        self.frame = bgui.Widget(self, aspect=1.0, size=[0.9, 0.9],
            pos=[0.05, 0.05])

        self.textQueue = collections.deque(['\n'] * 28)

        self.textbox = bgui.TextBlock(self.frame,
            size=[1.0, 0.8], pos=[0.0, 0.2])

        self.inputbox = bgui.TextInput(self.frame, pt_size=36,
            size=[1.0, 0.075], pos=[0.0, 0.12])

        self.sendbtn = bgui.FrameButton(self.frame, text="Send",
            size=[0.4, 0.1], pos=[0.0, 0.0])
        self.sendbtn.on_click = self.send

        self.renamebtn = bgui.FrameButton(self.frame, text="Rename",
            size=[0.4, 0.1], pos=[0.5, 0.0])
        self.renamebtn.on_click = self.rename

        # Now setup the scene callback so we can draw
        bge.logic.getCurrentScene().post_draw = [self.render]

    def setTarget(self, comp):
        self.component = comp

    def addChat(self, username, text):
        self.textQueue.append("".join([username, ": ", text, "\n"]))
        self.textQueue.popleft()
        self.textbox.text = "".join(self.textQueue)

    def send(self, widget):
        if self.component is None:
            # No component defined, do nothing
            return

        text = self.inputbox.text
        if len(text):
            # Reset the input box
            self.inputbox.text = ""

            if self.component.mgr.hostmode == 'server':
                self.component.raw_public_chat([text])
            else:
                # Send it to the server for processing
                self.component._packer.pack('raw_public_chat', [text])

    def rename(self, widget):
        if self.component is None:
            return

        text = self.inputbox.text
        if len(text):
            self.inputbox.text = ""

            self.component.change_username([text])
            self.component._packer.pack('change_username', [text])

    def update(self, dt):
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
