import datetime
import time
from getpass import getpass

class UI:
    """
    A static utility class for handling console output with rich formatting, ANSI colors,
    and structured logging levels.
    """

    # --- ANSI Colors ---
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    GREY    = "\033[90m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"

    # --- Config ---
    SHOW_TIME = True

    # =========================================================
    #  PART 1: SETUP & HELPERS
    # =========================================================

    @staticmethod
    def clear_screen():
        print("\033[2J\033[H")

    @staticmethod
    def banner():
        print("\033[2J\033[H")
        print(f"{UI.CYAN}")
        print(r"""
   _____                  _              __  __                         _ 
  / ____|                | |            |  \/  |                       | |
 | |     ___  _   _ _ __ | |_ ___ _ __  | \  / | ___  ___ ___  __ _  __| |
 | |    / _ \| | | | '_ \| __/ _ \ '__| | |\/| |/ _ \/ __/ __|/ _` |/ _` |
 | |___| (_) | |_| | | | | ||  __/ |    | |  | | (_) \__ \__ \ (_| | (_| |
  \_____\___/ \__,_|_| |_|\__\___|_|    |_|  |_|\___/|___/___/\__,_|\__,_| v1.0
        """)
        print(f"{UI.RESET}{UI.BOLD}   E2EE Communication System{UI.RESET}")
        print(f"{UI.GREY}   ─────────────────────────{UI.RESET}\n")
        print(f"{UI.GREEN}[+] Initializing System Sequence...{UI.RESET}")

    @staticmethod
    def step(message, status="OK", color=None):
        if color is None:
            color = UI.GREEN
        print(f" ├── {message:<40} [{color}{status}{UI.RESET}]")
        time.sleep(0.05)

    @staticmethod
    def sys_ready():
        print(f"\n{UI.BOLD}>>> System Ready. Entering Command Mode...{UI.RESET}\n")

    @staticmethod
    def sub_step(key, value):
        print(f" │   └── {UI.GREY}{key}: {UI.RESET}{value}")

    @staticmethod
    def end_step(message, status="DONE"):
        print(f" └── {message:<40} [{UI.GREEN}{status}{UI.RESET}]")

    @staticmethod
    def setup_error(message):
        print(f" └── {UI.RED}ERROR: {message}{UI.RESET}")

    # =========================================================
    #  PART 2: MAIN LOGS
    # =========================================================

    @staticmethod
    def _timestamp():
        if not UI.SHOW_TIME:
            return ""
        now = datetime.datetime.now().strftime("%H:%M:%S")
        return f"{UI.GREY}[{now}]{UI.RESET} "

    @staticmethod
    def _log(tag, color, message):
        ts = UI._timestamp()
        print(f"{ts}{UI.BOLD}{color}[ {tag} ]{UI.RESET} {message}")

    @staticmethod
    def user(msg):     UI._log("USER",     UI.GREEN,   msg)
    @staticmethod
    def security(msg): UI._log("SECURITY", UI.BLUE,    msg)
    @staticmethod
    def success(msg):  UI._log("SUCCESS",  UI.GREEN,   msg)
    @staticmethod
    def error(msg):    UI._log("ERROR",    UI.RED,     msg)
    @staticmethod
    def warn(msg):     UI._log("WARN",     UI.MAGENTA, msg)
    @staticmethod
    def info(msg):     UI._log("INFO",     UI.GREY,    msg)
    @staticmethod
    def admin(msg):  UI._log("ADMIN",  UI.YELLOW,  msg)
    @staticmethod
    def sys(msg):      UI._log("SYSTEM",   UI.CYAN,    msg)

    # =========================================================
    #  PART 3: SUB LOGS
    # =========================================================

    @staticmethod
    def _sub(color, message):
        ts = UI._timestamp()
        print(f"{ts}   {color}└──{UI.RESET} {message}")

    @staticmethod
    def sub_user(msg):     UI._sub(UI.GREEN,   msg)
    @staticmethod
    def sub_security(msg): UI._sub(UI.BLUE,    msg)
    @staticmethod
    def sub_error(msg):    UI._sub(UI.RED,     msg)
    @staticmethod
    def sub_warn(msg):     UI._sub(UI.MAGENTA, msg)
    @staticmethod
    def sub_info(msg):     UI._sub(UI.GREY,    msg)
    @staticmethod
    def sub_admin(msg):  UI._sub(UI.YELLOW,  msg)
    @staticmethod
    def sub_sys(msg):      UI._sub(UI.CYAN,    msg)

    # =========================================================
    #  PART 4: MENU RENDERING
    # =========================================================

    @staticmethod
    def menu_header(name: str):
        """Prints a styled menu header with correctly aligned box borders."""
        # Inner width = the content area between the two │ characters.
        # We pad it to at least 30 chars so short names don't produce tiny boxes.
        inner = max(len(name) + 4, 30)
        bar   = "─" * inner
        # name.center(inner) produces exactly `inner` characters, so the right │ always lands in column (inner + 4).
        print(f"\n{UI.BOLD}{UI.CYAN}  ┌{bar}┐{UI.RESET}")
        print(f"{UI.BOLD}{UI.CYAN}  │{name.center(inner)}│{UI.RESET}")
        print(f"{UI.BOLD}{UI.CYAN}  └{bar}┘{UI.RESET}")

    @staticmethod
    def menu_option(index: int, text: str):
        """Prints a numbered menu entry."""
        num = f"{UI.BOLD}{UI.YELLOW}[ {index} ]{UI.RESET}"
        print(f"   {num} {text}")

    @staticmethod
    def menu_option_special(key: str, text: str, color=None):
        """Prints a special (non-numbered) menu entry such as Back or Quit."""
        if color is None:
            color = UI.GREY
        tag = f"{UI.BOLD}{color}[ {key} ]{UI.RESET}"
        print(f"   {tag} {UI.GREY}{text}{UI.RESET}")

    @staticmethod
    def menu_divider():
        """Prints a thin horizontal divider between option groups."""
        print(f"   {UI.GREY}{'─' * 28}{UI.RESET}")

    @staticmethod
    def menu_prompt() -> str:
        """Prints the input prompt and returns the stripped, lowercased input."""
        return input(f"\n  {UI.BOLD}{UI.CYAN}›{UI.RESET} ").strip().lower()

    @staticmethod
    def menu_invalid():
        UI.warn("Invalid option — please try again.")

    @staticmethod
    def menu_error(exc: Exception):
        UI.error(f"Menu error → {exc}")

    @staticmethod
    def menu_exit():
        print(f"\n{UI.BOLD}{UI.GREEN}[+] Exiting application...{UI.RESET}\n")

    def menu_prompt_message(msg) -> str:
        return input(f"\n  {UI.BOLD}{UI.CYAN}{msg} : {UI.RESET} ").strip()#.lower()
    
    def get_pass(msg) -> str:
        return getpass(f"\n {UI.BOLD}{UI.CYAN}{msg} : {UI.RESET} ").strip()