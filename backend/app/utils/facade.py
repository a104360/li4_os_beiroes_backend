from .ui import * 
import traceback


def full_stack():
    full_tb = traceback.format_exc()

    UI.error(f"Critical Error:\n{full_tb}")


class MenuExit(Exception):
    """Signal to exit all menus."""
    pass
 
 
class MenuEntry:
    def __init__(self, text: str, function, *args, **kwargs):
        self.text = text
        self.function = function
        self.args = args
        self.kwargs = kwargs
 
    def run(self):
        return self.function(*self.args, **self.kwargs)
 
 
class Menu:
    def __init__(self, name: str, *entries: MenuEntry, allow_back=True):
        self.name = name
        self.entries = list(entries)
        self.allow_back = allow_back
 
    def display(self):
        UI.menu_header(self.name)
        for i, entry in enumerate(self.entries, start=1):
            UI.menu_option(i, entry.text)
        UI.menu_divider()
        if self.allow_back:
            UI.menu_option_special("0", "Back", color=UI.BLUE)
        UI.menu_option_special("q", "Quit", color=UI.RED)
 
    def run(self):
        while True:
            self.display()
            key = UI.menu_prompt()
 
            if key == "q":
                raise MenuExit()
 
            if self.allow_back and key == "0":
                return
 
            try:
                index = int(key) - 1
                if 0 <= index < len(self.entries):
                    result = self.entries[index].run()
                    if isinstance(result, Menu):
                        result.run()
                else:
                    UI.menu_invalid()
 
            except ValueError as e:
                tb = traceback.extract_tb(e.__traceback__)[-1]
                filename = tb.filename.split("/")[-1]
                error_msg = f"{type(e).__name__}: {e} ({filename}:{tb.lineno})"
                UI.warn(error_msg)

            except MenuExit:
                raise
            except Exception as e:

                tb = traceback.extract_tb(e.__traceback__)[-1]
                filename = tb.filename.split("/")[-1]
                error_msg = f"{type(e).__name__}: {e} ({filename}:{tb.lineno})"
                UI.error(error_msg)
 
 
class Facade:
    def __init__(self):
        self.menus: dict[str, Menu] = {}
 
    def add_menu(self, name: str, menu: Menu):
        self.menus[name] = menu
 
    def run(self, start_menu: str):
        UI.banner()
        try:
            if start_menu in self.menus:
                self.menus[start_menu].run()
        except MenuExit:
            UI.menu_exit()
 