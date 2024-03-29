import traceback

from pyglet.window import key

from console import Console
from plugin import Plugin, Mode, EventHandler


DEADGRAVE = 210453397504
TOPMOST_LAYER = 1000


class EditorConsole(Console):
    def __init__(self, editor):
        self.locals = {}
        super(EditorConsole, self).__init__()
        self.editor = editor
        self.mode_vars = {}
        self.vars = {}
        self.mode_cmds = {}
        self.cmds = {}
        self.add_command('help', self.do_help)
        self.add_command('layers', self.do_layers)

    def init_interpreter(self, ns_locals=None, ns_globals=None):
        super(EditorConsole, self).init_interpreter(ns_locals=self.locals)

    def add_mode_variable(self, mode, varname, getter):
        self.mode_vars.setdefault(mode, {})[varname] = getter
        self.update_locals(self.mode_vars[mode])

    def add_variable(self, varname, getter):
        self.vars[varname] = getter
        self.update_locals(self.vars)

    def add_mode_command(self, mode, cmd, callable):
        self.mode_cmds.setdefault(mode, {})[varname] = getter
        self.update_locals(self.mode_cmds[mode])

    def add_command(self, cmd, callable):
        self.cmds[cmd] = callable
        self.update_locals(self.cmds)

    def do_layers(self):
        for n, l in self.editor.layers.children_names.items():
            label = getattr(l, "label", None)
            if label is None:
                label = "<unlabelled>"
            self.write("%s: %s\n" % (n, label))

    def do_help(self):
        def write_section(name, source):
            self.write(name + "\n")
            for k, v in source.items():
                if v.__doc__ is not None:
                    self.write("%s: %s\n" % (k, v.__doc__))
                else:
                    self.write(k + "\n")
            self.write("\n")
        write_section("Variables", self.vars)
        if self.editor.current_mode is not None:
            mode = self.editor.current_mode.name
            if mode in self.mode_vars:
                write_section("Mode Variables", self.mode_vars[mode])
            write_section("Commands", self.cmds)
            if mode in self.mode_cmds:
                write_section("Mode Commands", self.mode_cmds[mode])

    def update_locals(self, source):
        for k, v in source.items():
            if hasattr(v, 'im_func'):
                # is an instance method
                r = v.im_func
            elif hasattr(v, 'func_code'):
                # is a function
                if v.func_code.co_argcount > 0:
                    r = v
                else:
                    r = v()
            else:
                r = v
            self.locals[k] = r

    def reset_locals(self):
        self.locals = {}
        # generic commands
        self.update_locals(self.cmds)
        # generic variables
        self.update_locals(self.vars)
        if self.editor.current_mode is not None:
            mode = self.editor.current_mode.name
            # mode specific commands
            if mode in self.mode_cmds:
                self.update_locals(self.mode_cmds[mode])
            # mode specific variables
            if mode in self.mode_vars:
                self.update_locals(self.mode_vars[mode])
        self.update_completer(self.locals)

    def update_completer(self, ns_locals=None, ns_globals=None):
        self.interpreter.update_namespace(ns_locals, ns_globals)

    #################
    # Text Events
    #################
    def on_command(self, command):
        self.reset_locals()

        try:
            parts = command.split(" ")
            if parts:
                name = parts[0].strip()
                args = parts[1:]
                if name in self.cmds:
                    self.write('\n')
                    self.cmds[name](*args)
                    self.interpreter.history.append(command)
                    self.write_prompt()
                    return
                else:
                    if self.editor.current_mode is not None:
                        mode = self.editor.current_mode.name
                        if mode in self.mode_cmds and name in self.mode_cmds[mode]:
                            self.write('\n')
                            self.mode_cmds[mode][name](*args)
                            self.interpreter.history.append(command)
                            self.write_prompt()
                            return
                return super(EditorConsole, self).on_command(command)
        except Exception, e:
            print e

        return super(EditorConsole, self).on_command(command)

    def on_completion(self, command):
        self.reset_locals()
        super(EditorConsole, self).on_completion(command)


class ConsoleEventHandler(EventHandler):

    def __init__(self, editor, console):
        self.editor = editor
        self.console = console
        self.console_visible = None
        self.mouse_position = (0, 0)

    def toggle_console(self):
        if not self.console_visible:
            self.editor.add(self.console, z=TOPMOST_LAYER)
        else:
            self.editor.remove(self.console)
        self.console_visible = not self.console_visible

    def on_key_press(self, k, m):
        print k

        if k == key.F12:
            self.toggle_console()
            return True
        elif k == key.I and (m & key.MOD_ACCEL):
            # override cocos default interpreter
            self.toggle_console()
            return True

    def on_mouse_drag(self, px, py, dx, dy, b, m):
        self.mouse_position = px, py

    def on_mouse_motion(self, px, py, dx, dy):
        self.mouse_position = px, py


class ConsolePlugin(Plugin):
    name = 'console'
    def __init__(self, editor):
        self.editor = editor
        console = EditorConsole(editor)
        self.editor.console = console
        self.handler = ConsoleEventHandler(editor, console)
        self.editor.register_handler(self.handler)

        def get_editor():
            'the editor instance'
            return editor

        console.add_variable('editor', get_editor)
        bookmarks = {}
        def goto(name):
            'goto bookmark NAME'
            try:
                self.editor.look_at(*bookmarks[name])
            except KeyError:
                pass
        editor.console.add_command('goto', goto)
        def mark(name):
            'mark this location as NAME'
            bookmarks[name] = self.editor.layers.pointer_to_world(
                *self.handler.mouse_position)
        editor.console.add_command('mark', mark)
