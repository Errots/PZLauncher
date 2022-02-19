import os
import signal
import logging
import threading as thr
import PySimpleGUI as sg
from subprocess import Popen, PIPE
from sys import exit
from queue import Queue, Empty
from time import sleep, localtime, strftime


class Gui:
    def __init__(self):
        self.debug = False
        self.window = None
        self.keys = ["-Settings tab-", "64bits", "steam", "znet",
                     "-CFB-", "-SPB-", "-Min RAM-", "-Max RAM-", "-MFB-", "-MS-", "-Download mod-"]

    def disable_all(self, val):
        for key in self.keys:
            self.window[key].update(disabled=val)

    def start_popup(self, fs):
        layout = [
            [sg.Column([[sg.T('Do you want to install it?')],
                        [sg.Yes(s=10), sg.No(s=10), sg.Button(button_text="Already", tooltip="Just skip this part", k="-Already folder-")]], k="-PQ-"),
             sg.Column([[sg.T('Where?', pad=((5, 0)))], [sg.Input(default_text="Directory", enable_events=True, key='-Where Folder-', readonly=True),
                                                         sg.FolderBrowse(target='-Where Folder-')]], k="-PA-", visible=False)]]
        self.window = sg.Window('Server folder not found', layout, icon=fs.icon,
                                finalize=True)

    def start(self, zs, fs):
        def TextLabel(text, s, ky=None): return sg.Text(
            text, justification='left', size=(s, 1), pad=((5, 0)), k=ky)
        pdt = ((5, 0), (0, 8))
        sg.theme('Dark Grey 13')
        ######################################################################################################################################################################################
        mods_tab = [[TextLabel("Mods folder", 10)],
                    [sg.Input(default_text=fs.workshop_path, tooltip="Path to the mods folder (by default is the same as server folder)", key='-Mods Folder-', enable_events=True, pad=pdt), sg.FolderBrowse(
                        target='-Mods Folder-', tooltip="Use this to refresh mod list", initial_folder=fs.workshop_path, k="-MFB-", pad=pdt), sg.Button(button_text="Update ALL", tooltip="Updates all the mods in folder", k="-Update ALL mods-", enable_events=True, pad=pdt)],
                    [TextLabel("Mod search", 10)],
                    [sg.Input(tooltip="Enter number id of mod", key='-Mods Search-', enable_events=True, pad=pdt), sg.Button(button_text='Search', k="-MS-",
                                                                                                                             enable_events=True, pad=pdt), sg.Button(button_text="Download", tooltip="Download the specified mod", k="-Download mod-", enable_events=True, pad=pdt)],
                    [sg.Frame(layout=[*[[TextLabel(key, 10), TextLabel(value[0], 30), sg.Checkbox(text="Active", default=value[3], key=f"-Mod active-{key}", metadata=key, enable_events=True, pad=(5, 0)), sg.Button(button_text="Update", tooltip="Updates the mod in this row", k="-Update mod-", metadata=key)]
                                        for key, value in fs.workshop_mods.items()]], title="Mod list", k="-Mods frame-", expand_x=True),
                     sg.Frame(layout=[[TextLabel("", 10, "-FNum Text-"), TextLabel("", 30, "-FName Text-"), sg.Checkbox(text="Active", key=f"-FMod active-", enable_events=True, pad=(5, 0)), sg.Button(button_text="Update", tooltip="Updates the mod in this row", k="-FUpdate mod-")]],
                              title="Mod list", k="-FMods frame-", visible=False, expand_x=True)]]
        mods_col = [
            [sg.Column(mods_tab, scrollable=True, vertical_scroll_only=True, k="-Mods col-", expand_x=True, expand_y=True)]]

        ######################################################################################################################################################################################
        settings_tab = [*[[TextLabel(key, 20), sg.Input(default_text=value, key=f'-File Config-{key}', metadata=key, enable_events=True, pad=pdt)]
                          for key, value in fs.config_data.items()]]
        settings_col = [
            [sg.Column(settings_tab, scrollable=True, vertical_scroll_only=True, expand_x=True, k="-Settings Column-")]]

        ######################################################################################################################################################################################
        zomboid_tab = [[sg.Button(button_text="Start Server", tooltip="Start/Stop server after saving settings", k="Server"), sg.Checkbox("64 Bits", default=zs.bit_system, k="64bits", tooltip="Enables the use of jre64 instead of normal jre (means that can use more ram)", enable_events=True), sg.Checkbox("Steam", default=zs.steam, k="steam", tooltip="Activates steam services as for auto update for mods and steam servers", enable_events=True), sg.Checkbox("ZNetlog", default=zs.znet, k="znet", tooltip="Activates log for server and clients console", enable_events=True)],
                       [TextLabel('Config file', 15)], [sg.Input(default_text=fs.server_file_path, key='-Config File-', tooltip="Path to the config file on C:\\Users\\[user]\\Zomboid\\Server", enable_events=True, pad=pdt),
                                                        sg.FileBrowse(target='-Config File-', initial_folder=fs.settings_path, k="-CFB-", pad=pdt)],
                       [TextLabel('Dedicated server Folder', 20)], [sg.Input(default_text=zs.server_path, key='-Server Folder-', tooltip="Path to the server files", enable_events=True, pad=pdt),
                                                                    sg.FolderBrowse(target='-Server Folder-', initial_folder=zs.PZDS_Path, k="-SPB-", pad=pdt)],
                       [TextLabel('Min RAM', 13), TextLabel('Max RAM', 10)], [sg.Input(default_text=zs.m_ram, k='-Min RAM-', tooltip="Minimun RAM for server (Uses 2g for GB or 2048m for MB)", size=(15, 1), enable_events=True, pad=pdt), sg.Input(default_text=zs.mx_ram, key='-Max RAM-', tooltip="Maximum RAM for server (Uses 2g for GB or 2048m for MB)", size=(15, 1), enable_events=True, pad=pdt)]]
        #####################################################################################################################################################################################
        layout = [[sg.TabGroup([[sg.Tab('Project Zomboid', zomboid_tab, k="-ZTab-"), sg.Tab('Settings', settings_col, k="-Settings tab-"), sg.Tab('Mods', mods_col, k="-Mods tab-")]], expand_x=True, size=(600, 150), k="-Tabs-")],
                  [sg.HSep()],
                  [sg.Multiline(autoscroll=True, disabled=True, tooltip="Output for all console log", reroute_stdout=True, expand_x=True, expand_y=True)]]

        self.window = sg.Window('PZLauncher', layout, icon=fs.icon, resizable=True,
                                finalize=True, size=(600, 400))
        self.window['-Tabs-'].expand(expand_x=True, expand_y=True)
        LogI("**GUI STARTED**")


class ZomboidServer:
    def __init__(self):
        self.znet = False
        self.steam = False
        self.debug = False
        self.is_game = False
        self.running = False
        self.bit_system = False
        self.stdout_queue = None
        self.server_thread = None
        self.server_process = None
        self.server_path = ""
        self.mx_ram = "2g"
        self.m_ram = "2g"
        self.file_save = "servertest"
        self.class_path32 = "java/istack-commons-runtime.jar;java/jassimp.jar;java/javacord-2.0.17-shaded.jar;java/javax.activation-api.jar;java/jaxb-api.jar;java/jaxb-runtime.jar;java/lwjgl.jar;java/lwjgl-natives-windows-x86.jar;java/lwjgl-glfw.jar;java/lwjgl-glfw-natives-windows-x86.jar;java/lwjgl-jemalloc.jar;java/lwjgl-jemalloc-natives-windows-x86.jar;java/lwjgl-opengl.jar;java/lwjgl-opengl-natives-windows-x86.jar;java/lwjgl_util.jar;java/sqlite-jdbc-3.27.2.1.jar;java/trove-3.0.3.jar;java/uncommons-maths-1.2.3.jar;"
        self.executable32 = "jre\\bin\\java.exe"
        self.start_server32 = " -Djava.awt.headless=true -Dzomboid.steam={1} -Dzomboid.znetlog={4} -XX:+UseG1GC -XX:-CreateCoredumpOnCrash -XX:-OmitStackTraceInFastThrow -Xms{2} -Xmx{3} -Djava.library.path=natives/;natives/win32/;./ -cp {0}{5} zombie.network.GameServer -servername {6} "
        self.class_path64 = "java/istack-commons-runtime.jar;java/jassimp.jar;java/javacord-2.0.17-shaded.jar;java/javax.activation-api.jar;java/jaxb-api.jar;java/jaxb-runtime.jar;java/lwjgl.jar;java/lwjgl-natives-windows.jar;java/lwjgl-glfw.jar;java/lwjgl-glfw-natives-windows.jar;java/lwjgl-jemalloc.jar;java/lwjgl-jemalloc-natives-windows.jar;java/lwjgl-opengl.jar;java/lwjgl-opengl-natives-windows.jar;java/lwjgl_util.jar;java/sqlite-jdbc-3.27.2.1.jar;java/trove-3.0.3.jar;java/uncommons-maths-1.2.3.jar;"
        self.executable64 = "jre64\\bin\\java.exe"
        self.start_server64 = " -Djava.awt.headless=true -Dzomboid.steam={1} -Dzomboid.znetlog={4} -XX:+UseZGC -XX:-CreateCoredumpOnCrash -XX:-OmitStackTraceInFastThrow -Xms{2} -Xmx{3} -Djava.library.path=natives/;natives/win64/;. -cp {0}{5} zombie.network.GameServer -statistic 0 -servername {6} "
        self.PZDS_Path = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Project Zomboid Dedicated Server"
        self.PZ_Path = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\ProjectZomboid"

    def stdout_thread(self, out, queue):
        for line in iter(out.readline, b''):
            queue.put(line)
        out.close()

    def start_server(self):
        if self.server_process != None:
            LogI("Server already running!")
            return
        if self.debug:
            LogD(self.start_server64.format(
                self.class_path64, "1" if self.steam else "0", self.m_ram, self.mx_ram, "1" if self.znet else "0", "./" if self.is_game else "java/", self.file_save))
        if self.bit_system:
            self.server_process = Popen(self.start_server64.format(
                self.class_path64,
                "1" if self.steam else "0",
                self.m_ram, self.mx_ram,
                "1" if self.znet else "0",
                "./" if self.is_game else "java/",
                self.file_save), cwd=self.server_path,
                executable=os.path.join(self.server_path, self.executable64), stdout=PIPE, stdin=PIPE)
            LogI("**Started 64bits server**")
        else:
            self.server_process = Popen(self.start_server32.format(
                self.class_path32,
                "1" if self.steam else "0",
                self.m_ram, self.mx_ram,
                "1" if self.znet else "0",
                "./" if self.is_game else "java/",
                self.file_save), cwd=self.server_path,
                executable=os.path.join(self.server_path, self.executable32), stdout=PIPE, stdin=PIPE)
            LogI("**Started 32bits server**")
        self.stdout_queue = Queue()
        self.server_thread = thr.Thread(
            target=self.stdout_thread, args=(self.server_process.stdout, self.stdout_queue), daemon=True)
        self.server_thread.start()
        self.running = True

    def stop_server(self):
        if self.server_process == None:
            LogI("No server running!")
            return
        if self.server_process != None:
            if self.debug:
                LogD("Try to terminate process")
                LogD(f"Program Id:#{self.server_process.pid}")
            try:
                os.kill(self.server_process.pid, signal.SIGTERM)
            except PermissionError as e:
                LogX(f"The process didn't have permission to die: {e}")
                raise PermissionError
            except Exception as e:
                LogX(e)
                exit()
            self.server_process = None
            if self.debug:
                LogD("Process Successfully terminated")
            self.running = False
            LogI("**Stopped server**")

    def comms_server(self):
        if self.server_process != None:
            try:
                line = self.stdout_queue.get_nowait()
            except Empty:
                return
            else:
                LogI(line.decode("utf-8").replace("\r\n", ""))


class FileSearch:
    def __init__(self):
        self.debug = False
        self.config_data = {}
        self.launcher_data = {}
        self.workshop_mods = {}
        self.server_file_path = ""
        self.default_file = "servertest.ini"
        self.self_path = os.path.abspath(os.getcwd())
        self.icon = os.path.join(self.self_path, "icon.ico")
        self.settings_path = os.path.expanduser("~\\Zomboid\\Server")
        self.workshop_path = os.path.abspath(
            "C:\\Program Files (x86)\\Steam")

    def exist_launch_config(self) -> bool():
        launcher_file_path = os.path.join(self.self_path, "config.ini")
        ss = os.path.isfile(launcher_file_path)
        LogI("**Config file {0} exist**".format("do" if ss else "doesn't"))
        return ss

    def read_launcher_config(self, zs):
        variables_keys = ["64bits", "steam", "znet", "debug"]
        try:
            launcher_path = os.path.join(self.self_path, "config.ini")
            launcher_dict = {}
            with open(launcher_path) as f:
                for lines in f:
                    variables = lines.split('=', 1)
                    var_val = variables[1].replace("\n", "")
                    launcher_dict[variables[0]] = var_val
            for key in variables_keys:
                if "True" in launcher_dict[key]:
                    launcher_dict[key] = True
                elif "False" in launcher_dict[key]:
                    launcher_dict[key] = False
            self.debug = launcher_dict["debug"]
            self.workshop_path = os.path.abspath(
                launcher_dict["workshop_path"])
            self.server_file_path = os.path.join(
                self.settings_path, f"{launcher_dict['file_save']}.ini")
            zs.server_path = os.path.abspath(launcher_dict["server_path"])
            zs.file_save = launcher_dict["file_save"]
            zs.bit_system = launcher_dict["64bits"]
            zs.steam = launcher_dict["steam"]
            zs.znet = launcher_dict["znet"]
            zs.mx_ram = launcher_dict["mx_ram"]
            zs.m_ram = launcher_dict["m_ram"]
            self.launcher_data = launcher_dict
            if self.debug:
                LogD(self.launcher_data)
        except InterruptedError as e:
            LogX(e)
            raise InterruptedError
        except FileNotFoundError as e:
            LogX(e)
            exit()
        LogI("*Read all launcher configs*")

    def write_launcher_config(self, zs):
        try:
            self.launcher_data["workshop_path"] = self.workshop_path
            self.launcher_data["debug"] = self.debug
            self.launcher_data["server_path"] = zs.server_path
            self.launcher_data["file_save"] = zs.file_save
            self.launcher_data["64bits"] = zs.bit_system
            self.launcher_data["steam"] = zs.steam
            self.launcher_data["znet"] = zs.znet
            self.launcher_data["mx_ram"] = zs.mx_ram
            self.launcher_data["m_ram"] = zs.m_ram
            launcher_path = os.path.join(self.self_path, "config.ini")
            with open(launcher_path, "w") as f:
                for key, value in self.launcher_data.items():
                    f.write(f"{key}={value}\n")
                    if self.debug:
                        LogD(f"{key}={value}\n")
        except InterruptedError:
            LogX("Something went wrong with the launcher data")
            raise InterruptedError
        except FileNotFoundError as e:
            LogX(e)
            exit()
        LogI("*Wrote all launcher configs*")

    def copy_default_file(self):
        if not os.path.exists(self.settings_path):
            os.makedirs(self.settings_path)
        file = os.path.join(self.self_path, self.default_file)
        if not os.path.isfile(file):
            LogE("**Default ini file not found**")
            exit()
        where = os.path.join(self.settings_path, self.default_file)
        os.system(f'cp {file} {where}')
        if self.debug:
            LogD("**Default ini file copied**")

    def exist_server_folder(self, zomboid) -> bool():
        ss = os.path.isdir(zomboid.PZDS_Path)

        if not ss:
            ss = os.path.isdir(zomboid.PZ_Path)
            if ss:
                zomboid.is_game = True
                zomboid.server_path = zomboid.PZ_Path
        else:
            zomboid.server_path = zomboid.PZDS_Path
            self.workshop_path = zomboid.PZDS_Path
        if self.debug:
            LogD(zomboid.server_path)
        LogI("{0}\n**Server folder {1} exist**".format(zomboid.server_path,
                                                       "do" if ss == True else "doesn't"))
        return ss

    def exist_settings_files(self, file_name) -> bool():
        if not os.path.exists(self.settings_path):
            return False
        self.server_file_path = os.path.join(self.settings_path, file_name)
        ss = os.path.isfile(self.server_file_path)
        if self.debug:
            LogD(self.server_file_path)
        LogI("{0}\n**File {1} exist**".format(self.server_file_path,
                                              "do" if ss == True else "doesn't"))
        return ss

    def exist_mods_folder(self) -> bool():
        ss = os.path.isdir(self.workshop_path)
        if self.debug:
            LogD(self.server_file_path)
        LogI("{0}\n**Mods folder {1} exist**".format(self.server_file_path,
                                                     "do" if ss == True else "doesn't"))
        return ss

    def read_server_config(self):
        try:
            LogD(self.server_file_path)
            with open(self.server_file_path) as f:
                config_dict = {}
                for lines in f:
                    variables = lines.split('=', 1)
                    config_dict[variables[0]] = variables[1].replace("\n", "")
                self.config_data = config_dict
                if self.debug:
                    LogD(self.config_data)
        except InterruptedError as e:
            LogX(e)
            raise InterruptedError
        except FileNotFoundError as e:
            LogX(e)
            exit()
        LogI("*Read all server configs*")

    def write_server_config(self):
        mods_string = ""
        workshop_num = ""
        maps = "Muldraugh, KY;"
        try:
            active_mods = [*[[key, value] for key,
                             value in self.workshop_mods.items() if value[3] == True]]
            if self.debug:
                LogD(active_mods)
            for value in active_mods:
                workshop_num = f'{workshop_num}{value[0]};'
                mods_string = f'{mods_string}{value[1][1]};'
                maps = f'{maps}{value[1][1]};' if value[1][2] == True else maps
            self.config_data["Mods"] = mods_string
            self.config_data["WorkshopItems"] = workshop_num
            self.config_data["Map"] = maps

            with open(self.server_file_path, "w") as f:
                for key, value in self.config_data.items():
                    f.write(f"{key}={value}\n")
                    if self.debug:
                        LogD(f"{key}={value}\n")
        except InterruptedError as e:
            LogX(e)
            raise InterruptedError
        except FileNotFoundError as e:
            LogX(e)
            exit()
        LogI("*Wrote all server configs*")

    def get_workshop_mods(self):
        mods = {}
        try:
            mods_path = os.path.join(
                self.workshop_path, "steamapps\\workshop\\content\\108600")
            if not os.path.exists(mods_path):
                os.makedirs(mods_path)
            for name in os.listdir(mods_path):
                if self.debug:
                    LogD(f"{mods_path}\\{name}\n")
                mod_path = os.path.join(mods_path, name, "mods")
                folder = os.listdir(mod_path)
                file = os.path.join(mod_path, folder[0], "mod.info")
                if not os.path.isfile(file):
                    continue

                with open(file, encoding="utf-8-sig") as f:
                    config_dict = {}
                    for lines in f:
                        if not len(lines) > 1:
                            continue
                        variables = lines.split('=', 1)
                        if len(variables) > 0:
                            config_dict[variables[0]] = variables[1]
                            if self.debug:
                                LogD(f"{variables[0]}={variables[1]}\n")

                    mods[name] = [config_dict["name"].replace(
                        "\n", ""),
                        config_dict["id"].replace("\n", ""),
                        True if "tiledef" in config_dict else False,
                        False,
                        config_dict["require"] if "require" in config_dict else None]
            self.workshop_mods = mods
            if self.debug:
                LogD(f"{self.workshop_mods}\n")
            LogI("*Readed all mods*")
            return True
        except FileNotFoundError:
            LogW("!!FileNotFoundError!!")
            return False

    def validate_server_mods(self):
        mods_active = self.config_data["WorkshopItems"].split(';')
        for mod in mods_active:
            if mod in self.workshop_mods:
                self.workshop_mods[mod][3] = True
        if self.debug:
            tt = [value for (key, value) in self.workshop_mods.items()
                  if value[3] == True]
            LogD(f"{tt}\n")
        LogI("*Acknowledged all mods*")

    def find_mod_by_id(self, id: str()) -> str():
        for key, value in self.workshop_mods.items():
            if value[1] == id:
                return key
        return None


class SteamCMD:
    def __init__(self):
        self.debug = False
        self.running = False
        self.stdout_queue = None
        self.server_thread = None
        self.steam_process = None
        self.command = ".\\Include\\steamcmd +force_install_dir {1} +login anonymous {0} +quit"

    def stdout_thread(self, out, queue):
        for line in iter(out.readline, b''):
            queue.put(line)
        out.close()

    def install_pzds(self, path):
        app_string = "+app_update 380870 validate"
        if self.debug:
            LogD(f"{path}\n")
        LogI("** Start install **")
        self.steam_process = Popen(
            self.command.format(app_string, path))
        self.steam_process.wait()
        self.steam_process = None
        LogI("** Install finished **")

    def update_workshop_mods(self, path, numbers: list):
        mod_string = "+workshop_download_item 108600 {0} validate "
        mods_val = ""
        for number in numbers:
            mods_val = mods_val + mod_string.format(number)
        if self.debug:
            LogD(f"{self.command.format(mods_val, path)}\n")
        self.steam_process = Popen(
            self.command.format(mods_val, path), stdout=PIPE)
        self.stdout_queue = Queue()
        self.server_thread = thr.Thread(
            target=self.stdout_thread, args=(self.steam_process.stdout, self.stdout_queue), daemon=True)
        self.server_thread.start()
        self.running = True
        LogI("**Start mods Update/Install**")

    def update_workshop_mod(self, path, number):
        mod_string = f"+workshop_download_item 108600 {number} validate"
        if self.debug:
            LogD(f"{self.command.format(mod_string, path)}\n")
        self.steam_process = Popen(
            self.command.format(mod_string, path), stdout=PIPE)
        self.stdout_queue = Queue()
        self.server_thread = thr.Thread(
            target=self.stdout_thread, args=(self.steam_process.stdout, self.stdout_queue), daemon=True)
        self.server_thread.start()
        self.running = True
        LogI("**Start mod Update/Install**")

    def comms_steamcmd(self, wn):
        if self.steam_process != None:
            try:
                line = self.stdout_queue.get_nowait()
            except Empty:
                check = self.steam_process.poll()
                if check is not None:
                    self.running = False
                    self.steam_process = None
                    LogI("**Mod Update/Install finish**")
                    wn.disable_all(False)
                    if self.debug:
                        LogD(check)
            else:
                if "0x202" in line.decode("utf-8"):
                    LogW(
                        "Insufficient space for zomboid dedicated server files (Needs 4GB)")
                    exit()
                LogI(line.decode("utf-8").replace("\r\n", ""))


def LogX(msg):
    logging.exception(msg)
    print(msg)


def LogE(msg):
    logging.error(msg)
    print(msg)


def LogW(msg):
    logging.warning(msg)
    print(msg)


def LogD(msg):
    logging.debug(msg)
    print(msg)


def LogI(msg):
    logging.info(msg)
    print(msg)


def main():
    # Setting logging like this because it works
    _filename = f'Logs\\{strftime("%d-%b-%y_%H-%M-%S", localtime())}_debug.log'
    logging.basicConfig()
    _log_handler = logging.FileHandler(
        filename=_filename,
        mode='w', encoding='utf-8')
    _log_format = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%d-%b-%y %H:%M:%S')
    _log_handler.setFormatter(_log_format)
    _logger = logging.getLogger()
    _logger.addHandler(_log_handler)
    _logger.setLevel(logging.INFO)
    _logger.setLevel(logging.DEBUG)
    ################################################

    LogI("°° STARTING °°")
    steam = SteamCMD()
    zs = ZomboidServer()
    fs = FileSearch()
    launch_config_exist = fs.exist_launch_config()
    if launch_config_exist:
        fs.read_launcher_config(zs)
    wn = Gui()

    if not launch_config_exist and not fs.exist_server_folder(zs):
        zs.debug = steam.debug = fs.debug = wn.debug = False
        wn.start_popup(fs)
        while True:
            event, values = wn.window.read(timeout=50)

            ##############################################################
            # Popup events
            ##############################################################
            if event == sg.WIN_CLOSED or event == 'No':
                exit(0)

            if event != "__TIMEOUT__" and fs.debug:
                LogI(event)

            if event == '-Already folder-':
                break

            if event == 'Yes':
                wn.window["-PQ-"].update(visible=False)
                wn.window["-PA-"].update(visible=True)

            if event == "-Where Folder-":
                folder_path = os.path.abspath(values[event].rstrip())
                LogI(folder_path)
                if not os.path.isdir(folder_path):
                    continue
                fs.workshop_path = folder_path
                zs.server_path = folder_path
                steam.install_pzds(folder_path)
                break
    else:
        zs.debug = steam.debug = wn.debug = fs.debug

    if not fs.exist_settings_files("servertest.ini"):
        fs.copy_default_file()
    fs.read_server_config()
    if fs.exist_mods_folder():
        fs.get_workshop_mods()
        fs.validate_server_mods()
    if wn.window is not None:
        wn.window.close()
    wn.start(zs, fs)
    while True:
        event, values = wn.window.read(timeout=50)

        ##############################################################
        # Main windows events
        ##############################################################
        if event == sg.WIN_CLOSED:
            fs.write_launcher_config(zs)
            zs.stop_server()
            break
        if event != "__TIMEOUT__" and fs.debug:
            LogI(event)

        continue

        ##############################################################
        # Project zomboid tab events
        ##############################################################
        if event == 'Server' and not steam.running:
            if zs.running:
                zs.stop_server()
                wn.window["Server"].update("Start Server")
                wn.disable_all(False)
                continue
            fs.write_launcher_config(zs)
            fs.write_server_config()
            zs.start_server()
            wn.window["Server"].update("Stop Server")
            wn.disable_all(True)

        # Comms if theres an active subprocess
        if zs.server_process != None:
            zs.comms_server()
        if steam.steam_process != None:
            steam.comms_steamcmd(wn)

        # Don't continue if running
        if zs.running and not steam.running:
            continue

        if event == "-Config File-":
            datav = values[event].rstrip()
            if not "Zomboid/Server/" in datav:
                wn.window[event].update(value=fs.server_file_path)
                LogI("## File isn't on default Zomboid/Server ##")
                continue
            fs.server_file_path = os.path.abspath(datav)
            wn.window[event].update(value=fs.server_file_path)
            splits = datav.split('/')
            zs.file_save = splits[len(splits)-1].replace(".ini", "")
            fs.read_server_config()
            for key, value in fs.config_data.items():
                wn.window[f"-File Config-{key}"].update(value)
            active_mods = [*[[key, value] for key,
                             value in fs.workshop_mods.items() if value[3] == True]]
            for value in active_mods:
                wn.window[f"-Mod active-{value[0]}"].update(False)
                fs.workshop_mods[value[0]][3] = False
            fs.validate_server_mods()
            active_mods = [*[[key, value] for key,
                             value in fs.workshop_mods.items() if value[3] == True]]
            for value in active_mods:
                wn.window[f"-Mod active-{value[0]}"].update(True)

        if event == "-Server Folder-":
            folder_path = os.path.abspath(values[event].rstrip())
            if not os.path.isdir(folder_path):
                wn.window[event].update(value=zs.server_path)
                LogI("## Folder doesn't exist ##")
                continue
            zs.server_path = folder_path
        if event == '64bits':
            zs.bit_system = not zs.bit_system
        if event == 'steam':
            zs.steam = not zs.steam
        if event == 'znet':
            zs.znet = not zs.znet
        if event == '-Min RAM-':
            zs.m_ram = values["-Min RAM-"].rstrip()
        if event == '-Max RAM-':
            zs.mx_ram = values["-Max RAM-"].rstrip()

        ##############################################################
        # File config tab events
        ##############################################################
        if event.startswith("-File Config-"):
            datav = wn.window[event].metadata
            fs.config_data[datav] = values[event].rstrip()

        ##############################################################
        # Mods config tab events
        ##############################################################

        if event == '-Mods Folder-':
            fs.workshop_path = os.path.abspath(values[event].rstrip())
            if fs.get_workshop_mods():
                fs.validate_server_mods()
                LogI("** RELOADING WINDOW PLEASE WAIT **")
                wn.window.refresh()
                sleep(5)
                wn.window.close()
                sleep(2)
                wn.start(zs, fs)

        if event == '-Mods Search-':
            LogI(f"Search: {values[event].rstrip()}")
            if values[event].rstrip() == "":
                wn.window["-FMods frame-"].update(visible=False)
                wn.window["-Mods frame-"].update(visible=True)

        if event == '-Download mod-':
            mods_id = values["-Mods Search-"].rstrip().split(';')
            if len(mods_id) > 1:
                steam.update_workshop_mods(f"\"{fs.workshop_path}\"", mods_id)
                wn.disable_all(True)
                continue

            if mods_id[0] != "":
                steam.update_workshop_mod(
                    f"\"{fs.workshop_path}\"", mods_id[0])
                wn.disable_all(True)

        if event == '-MS-':
            mod_id = values["-Mods Search-"].rstrip()
            found_mods = [*[[key, value] for key,
                            value in fs.workshop_mods.items() if key == mod_id]]
            if len(found_mods) < 1:
                LogI(f"** No mods found with id: {mod_id} **")
                continue
            found = found_mods[0]
            wn.window["-FMods frame-"].update(visible=True)
            wn.window["-Mods frame-"].update(visible=False)
            wn.window["-FNum Text-"].update(value=found[0])
            wn.window["-FName Text-"].update(value=found[1][0])
            wn.window["-FMod active-"].update(value=found[1][3])

        if event == '-FMod active-':
            mod_id = values["-Mods Search-"].rstrip()
            wn.window[f"-Mod active-{mod_id}"].update(
                not fs.workshop_mods[mod_id][3])
            fs.workshop_mods[mod_id][3] = not fs.workshop_mods[mod_id][3]

        if event == '-FUpdate mod-':
            mod_id = values["-Mods Search-"].rstrip()
            steam.update_workshop_mod(f"\"{fs.workshop_path}\"", mod_id)
            wn.disable_all(True)

        if event.startswith("-Update ALL mods-") and not zs.running:
            numbers = fs.workshop_mods.keys()
            steam.update_workshop_mods(f"\"{fs.workshop_path}\"", numbers)
            wn.disable_all(True)

        if event.startswith("-Mod active-"):
            datav = wn.window[event].metadata
            required_by_mods = [*[[key, value] for key,
                                  value in fs.workshop_mods.items() if value[4] == fs.workshop_mods[datav][1]]]

            if len(required_by_mods) > 0 and fs.workshop_mods[datav][3]:
                for mod in required_by_mods:
                    wn.window[f"-Mod active-{mod[0]}"].update(False)
                    fs.workshop_mods[mod[0]][3] = False
                fs.workshop_mods[datav][3] = False
                continue

            if fs.workshop_mods[datav][4] != None:
                mod_id = fs.find_mod_by_id(fs.workshop_mods[datav][4])
                if mod_id == None:
                    fs.workshop_mods[datav][3] = False
                    LogW("## REQUIRED MOD DOESN'T EXIST ##")
                    continue
                wn.window[f"-Mod active-{mod_id}"].update(True)
                fs.workshop_mods[mod_id][3] = True
            fs.workshop_mods[datav][3] = not fs.workshop_mods[datav][3]

        if event.startswith("-Update mod-") and not zs.running:
            datav = wn.window[event].metadata
            steam.update_workshop_mod(f"\"{fs.workshop_path}\"", datav)
            wn.disable_all(True)

    LogI("END")
    wn.window.close()


if __name__ == '__main__':
    LogI('Starting program...')
    main()
