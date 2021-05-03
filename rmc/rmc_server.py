# rmc imports
from rmc_common import *

from auth.server import tcp_server
from auth.crypt import passkey, Fernet

#
from util.default_hba import default_hba

from wireguard import WireguardServer_macOS

# 3rd party package imports
import psycopg2

# built-in imports
from pathlib import Path
from ipaddress import ip_address, ip_network
import sys

import asyncio
import datetime
from multiprocessing import Process, Queue
import platform

"""
Server app:
    - Server: main app
    - Server setup: setup guide window
    - Server auth: authorization form to kick off server authentication
    - Server pass: form to 'log in' to the server app itself
"""

# gui
class Server(UI_Common):
    """Server window"""

    context = 'server'
    subnet = '9.0.0.0/24'
    auth_port = 4444
    wg_port = 51820

    def __init__(self, app, parent=None):
        super().__init__(app, parent=parent)

        self.setWindowTitle("Resolve Mission Control Server")

        # Define buttons
        self.b_dbadd = QPushButton("+")
        self.b_dbcon = QPushButton("⇄")
        self.b_dbdel = QPushButton("-")
        self.b_setup = QPushButton("Setup")
        self.b_tunn = QPushButton("Activate Tunnel")
        self.b_auth = QPushButton("Activate Authentication")

        # for b in [self.b_dbadd, self.b_dbcon, self.b_dbdel]:
        for b in [self.b_dbcon]: # TODO: Expand to add and del
            self.p_LU.lay.addWidget(b)
            b.setObjectName("LU_buttons")
            b.setStyleSheet(f"""QPushButton#LU_buttons {{
                                        color: #848484;
                                        background: transparent;
                                        }}
                                        QPushButton#LU_buttons::hover{{
                                        	color: white;
                                        }}
                                        QPushButton#LU_buttons::pressed{{
                                        	color: #848484;
                                        }}""")


        for b in [self.b_setup, self.b_tunn, self.b_auth]:
            self.p_RU.lay.addWidget(b)

        self.message = QLabel("")
        self.message.setTextFormat(Qt.MarkdownText)
        self.p_RB.lay.addWidget(self.message, alignment=Qt.AlignBottom)

        self.b_tunn.setEnabled(False)
        self.b_tunn.setCheckable(True)

        self.b_auth.setEnabled(False)
        self.b_auth.setCheckable(True)

        # BUTTON CONNECT
        self.setup_window = ServerSetup(self)
        self.b_setup.clicked.connect(self.setup_window.show)
        self.b_dbcon.clicked.connect(self.database_connect)
        self.b_tunn.clicked.connect(self.toggle_tunnel)
        self.b_auth.clicked.connect(self.toggle_auth)

        # Sever configured?
        if self.config['auth'] != {}:
            self.init_userview()
            self.auth_key = self.config['auth']['authkey']
            self.auth_port = self.config['auth']['port']
            self.subnet = self.config['auth']['subnet']
            self.setup_window.step_enable(['Create Remote User'])

            if len(self.config['userlist']) > 1:
                self.setup_window.step_enable(['Remove Remote User'])

        # Tunnel configured? (Requires server to be configured)
        if 'wireguard' in self.config.config:
            self.b_auth.setEnabled(True)
            self.b_tunn.setEnabled(True)
            self.wg_port = self.config['wireguard']['port']
            self.setup_window.step_enable(['Port Forward',
                                           'Authenticate Remote User'])

            if platform.system().lower() == 'darwin':
                self.wireguard = WireguardServer_macOS(config=self.config)

                # Check if already running, toggle if so
                if self.wireguard.state:
                    self.toggle_tunnel(True)


    def config_server(self):
        """ Configure server for the first time
            - Create passkey (hash of password)
            - Create server userlist
        """

        # login
        success = False

        if self.config['auth'] == {}:
            # First time / new config

            prompt = ServerConfig(self)
            prompt_result = prompt.exec_()
            password, port, subnet = prompt.get_output()

            if port == "":
                port = self.auth_port

            if subnet == "":
                subnet = self.subnet

            try:
                self.subnet = ip_network(subnet)

            except ValueError as e:
                UI_Error(self, "Invalid Assignment Subnet", "Retry or leave default")
                self.config_server()
                return

            try:
                port = int(port)
            except ValueError as e:
                UI_Error(self, "Invalid Assignment Port", "Was port as an integer?")
                self.config_server()
                return

            if len(password) == 0:
                UI_Error(self, "Invalid Password", "Must be longer than 0 characters")
                self.config_server()
                return

            if prompt_result and len(password) > 0:

                self.config['auth']['authkey'] = passkey(password).decode()
                self.config['auth']['subnet'] = subnet
                self.config['auth']['port'] = port
                self.config.save()

                # this class variable is used in authentication
                # and in sending
                self.auth_key = self.config['auth']['authkey']
                self.auth_port = self.config['auth']['port']

                success = True

        # Create userlist
        if success:

            self.config['userlist'] = []

            self.new_user({
                                "name"  : "Server",
                                "Pk"    : "",
                                "ip"    : "",
                            })

            self.config.save()

            self.init_userview()

    def reset_server(self):

        # Are you sure?
        areyousure = UI_Dialog(self)
        areyousure.setWindowTitle("Are you sure?")

        layout = QVBoxLayout(areyousure)

        info = QLabel("""# Reset Server deletes the entire configuration:
- Server info like password hash and authentication port
- Wireguard info like port, private and Public keys
- User list names, ips, public keys, everything...

___Are you sure you want to reset?___
_This action cannot be undone_""")
        info.setTextFormat(Qt.MarkdownText)

        layout.addWidget(info)

        # OK and Cancel buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            Qt.Horizontal, areyousure)

        buttons.accepted.connect(areyousure.accept)
        buttons.rejected.connect(areyousure.reject)

        layout.addWidget(buttons)
        result = areyousure.exec_()

        if result:
            self.config.reset(True)

            msg = QMessageBox(self)
            msg.setTextFormat(Qt.MarkdownText)
            msg.setText("Server has been reset")
            msg.setInformativeText("Resolve Mission Control Server will close"
                            " now. Please re-open to start a new configuration")
            msg.setWindowTitle("Server Reset")
            msg.exec_()

            self.app.closeAllWindows()

    def init_userview(self):
        """ Initialize the userlist view
            - Reload userlist
            - Repopulate userview
            - Change setup page to reflect state
            - Kick off userlist tcp update timer (Client Only)
            - Kick off view update timer
            - Kick off ip ping timer
        """
        # Server configured! Make Create Tunnel possible.
        self.setup_window.step_disable(['Configure Server'])
        self.setup_window.step_enable(['Create Tunnel'])

        self.setup_window.step_enable(['Create Remote User'])

        self.update_userview()
        self.user_timer = QTimer(self)
        self.user_timer.timeout.connect(self.update_userview)
        self.user_timer.start(1000)

    def update_userview(self):
        """ Update userlist view
            - Update list
            - Update auths
            - Update pings
        """
        self.users.update(self.config['userlist'])

    def new_user(self, user=None):
        """ Create a new remote user to authenticate and add to tunnel"""

        if user:
            self.config['userlist'] += [user]
            self.config.save()
            return

        auth_new = ServerAuth(self)
        auth_new.setWindowTitle("New User")
        auth_result = auth_new.exec_()
        auth_new = auth_new.get_output()

        if auth_result:

            try:
                ip_address(auth_new['ASSIGN_IP'])
            except ValueError as e:
                UI_Error(self, "Invalid Assignment IP", str(e))
                self.new_user()
                return

            if (ip_address(auth_new['ASSIGN_IP'])
                            not in ip_network(self.subnet)):
                UI_Error(self,"Invalid Assignment IP", f"IP must be on subnet {self.subnet}")
                self.new_user()
                return

            first_ip = next(ip_network(self.subnet).hosts())

            if (str(first_ip)==auth_new['ASSIGN_IP']):
                UI_Error(self,"Invalid Assignment IP", f"IP is reserved for server")
                self.new_user()
                return

            if (auth_new['ASSIGN_IP'] in [u['ip'] for u in self.config['userlist']]):
                UI_Error(self,"Invalid Assignment IP", f"IP is already assigned")
                self.new_user()
                return

            if len(auth_new['UNAME']) == 0:
                UI_Error(self,"Invalid Username", "Check input and try again")
                self.new_user()
                return

            # By this point, the input is a valid authentication request
            self.config['userlist'] += [{
                                "name" : auth_new['UNAME'],
                                "Pk"   : "",
                                "ip"   : auth_new['ASSIGN_IP'],
                            }]
            self.config.save()

            UI_Successful(self, f"Created {auth_new['UNAME']}",
                            f"IP Assigned: {auth_new['ASSIGN_IP']}")

            self.update_userview()

    def toggle_auth(self, state):
        """ Toggle authentication server """
        if state:
            self.open_authentication()
            self.b_auth.setText("Deactivate Authentication")
        else:
            self.close_authentication()
            self.b_auth.setText("Activate Authentication")

    def open_authentication(self):
        """ Run an authentication server """

        # Already running?
        if hasattr(self, 'tcp_proc'):
            return

        # ------------- CONFIG
        C_IP = '0.0.0.0' # where clients can come from (anywhere)
        S_PORT = self.auth_port

        self.tcp_queue = Queue()
        self.tcp_proc = Process(target = tcp_server,
                                args = (self.tcp_queue, C_IP, S_PORT,
                                        self.config['userlist'],
                                        self.config['auth']['authkey'],
                                        self.wg_port,))

        self.tcp_timer = QTimer(self)
        self.tcp_timer.timeout.connect(self.update_authentication)
        self.tcp_timer.start(500)
        self.tcp_proc.start()

        self.message.setText("Authentication server opened")

    def update_authentication(self):
        """ Check for updates on the authentication server """
        if not self.tcp_queue.empty():
            update = self.tcp_queue.get_nowait()

            if type(update) == str:
                self.message.setText(f"{update}")

                if 'error' in update:
                    self.toggle_auth(False)

            elif type(update) == list:
                # Hey! That's a new authenticated user!
                # update userlist with [PKEYU, UNAME, ASSIGN_IP]
                self.authenticated_user(update)

    def close_authentication(self):
        """ Close the authentication server """
        if hasattr(self, 'tcp_proc'):
            # Running? Stop.
            self.tcp_timer.stop()
            self.tcp_proc.terminate()
            self.tcp_proc.join()
            self.tcp_queue.close()

            self.message.setText("Authentication server closed")

            # Update HBA here in case if failed somewhere else
            self.update_hba()

    def authenticated_user(self, new_user):
        """ Add authorized, newly-created, remote user to tunnel config and userlist
            1) Update userlist
            2) Update tunnel config file and reboot tunnel therefore
            3) Update database hba conf
        """
        UNAME, PKEYU = new_user

        for n, user in enumerate(self.config['userlist']):

            if user['name'] == UNAME:
                # UNAME unchanged
                self.config['userlist'][n]['Pk'] = PKEYU
                self.config.save()
                break

        self.wireguard.update_config(self.config['userlist'])

        self.update_hba()

    def remove_user(self, username):
        """ Remove remote user, update wireguard, update hba """

        new_userlist = self.config['userlist']

        # find entry with name and remove it
        for user in self.config['userlist']:
            if user['name'] == username:
                new_userlist.remove(user)
                break

        self.config['userlist'] = new_userlist
        self.config.save()

        if hasattr(self, 'wireguard'):
            self.wireguard.update_config(new_userlist)

        self.update_hba()

        print("... Removed", username)
        self.message.setText(f"_Removed {username}_")

        # No need to remove from userview, it will automatically next refresh

    def create_database(self):
        """ Create a new PostgreSQL database based on Resolve template """
        # # TODO:

    def database_connect(self):
        added = super().database_connect()
        if added:
            self.update_hba()

    def update_hba(self):
        """ Update the access permissions for all databases in list """

        # Default hba_conf from util.default_hba
        hba = str(default_hba)
        hba_file = None

        for db, ui_db in self.dbses.ui_dbses.items():

            self.dbses.select(ui_db.db_details, fail_queitly = True)
            connection = ui_db.connection

            if connection:

                # Use "SHOW hba_file" to get the location of hba file
                # ... it is common across all database/connections
                crs = connection.cursor()
                try:
                    crs.execute("SHOW hba_file")

                except psycopg2.errors.InsufficientPrivilege:
                    UI_Error(self, "Database Error",
                        f"The database user {ui_db.db_details['name']} must "
                        f"be a superuser to update the "
                        f"host-based authentication permissions")
                    continue

                hba_file = crs.fetchall()[0][0]

                hba += f"""# Added by RMCS at {datetime.datetime.utcnow()}\n"""

                db_name = ui_db.db_details['name']
                db_user = ui_db.db_details['user']

                hba +="    ".join(['host', db_name, db_user, self.subnet, 'md5'])
                hba += '\n'

                # for user in self.config['userlist']:
                    # Allow access from these ips
                    # (the authenticated ones)

                    # if user['name'] == 'Server':
                    #     continue
                    #
                    # if user['Pk'] != "":
                    #     db_name = ui_db.db_details['name']
                    #     db_user = ui_db.db_details['user']
                    #     user_ip = f"{user['ip']}/32"
                    #
                    #     hba +="    ".join(['host', db_name, db_user, user_ip, 'md5'])
                    #     hba += '\n'

        if hba_file and connection:
            # Snag the last hba_file and connection from the for loop
            #  to actuall execute the file saving etc...

            # Backup
            backup_file = Path(hba_file).parent / Path("pg_hba_rmcsbackup.conf")

            with open(backup_file,'w') as bkup:

                with open(hba_file,'r') as file:
                    bkup.write(file.read())

            # Overwrite with new
            with open(hba_file,'w') as file:
                file.write(hba)

            # Reload config
            crs.execute("select pg_reload_conf()")
            out = crs.fetchall()[0][0]
            crs.close()

            print(f">>> pg_hba.conf updated with exit code: {out}")

            if out:
                self.message.setText("_Updated Host-Based Authentication_")

            # True if suceeded, False if failed
            return out

    def config_tunnel(self):
        """ Create a new Wireguard configuration
            1) Define port and subnet
            2) Create configuration based on **authenticated** users in userlist
            3) Activate tunnel
        """

        prompt = TunnelConfig(self)
        prompt_result = prompt.exec_()
        PORT = prompt.get_output()

        if not prompt_result:
            return

        if PORT == "":
            PORT = self.wg_port

        try:
            self.wg_port = int(PORT)

        except ValueError as e:
            UI_Error(self, "Invalid Assignment Port", "Was port as an integer?")
            self.config_tunnel()
            return

        if platform.system().lower() == 'darwin':

            try:
                self.wireguard = WireguardServer_macOS(force_reset = True,
                                                        port = self.wg_port,
                                                        subnet = self.subnet)

                self.wireguard.update_config(self.config['userlist'])

            except PermissionError:
                UI_Error(self, "Wireguard Configuration Failed",
                        "Must be run as root\n>>> sudo python rmc_server.py")
                return

        else:
            raise(NotImplementedError("Only macOS Wireguard Server supported"))

        # first ip in the subnet is always the server
        first_ip = next(ip_network(self.subnet).hosts())

        self.config['wireguard'] = {}
        self.config['wireguard']['port'] = self.wg_port
        self.config['wireguard']['pk'] = self.wireguard.pk
        self.config['wireguard']['Pk'] = self.wireguard.Pk
        self.config['userlist'][0]['Pk'] = self.wireguard.Pk
        self.config['userlist'][0]['ip'] = first_ip
        self.config.save()

        self.b_tunn.setEnabled(True)
        self.b_auth.setEnabled(True)

    def toggle_tunnel(self, state):
        """ Toggle the Wireguard directly with wg or wg-quick up/down
        """
        if not hasattr(self, 'wireguard'):
            print("... Tried to toggle non-existent Wireguard instance")
            return

        if state:
            # Open tunnel
            self.b_tunn.setText("Deactivate Tunnel")
            self.wireguard.up()
            self.message.setText("Wireguard tunnel open!")
        else:
            # Close tunnel
            self.b_tunn.setText("Activate Tunnel")
            self.wireguard.down()
            self.message.setText("Wireguard tunnel closed!")

    def closeEvent(self, event):
        """ Upon closing server:
            - Shutdown authentication server
            - Shutdown Wireguard tunnel
        """
        self.close_authentication()
        self.toggle_tunnel(False)
        super().closeEvent(event)

class ServerSetup(QWidget):
    """ Setup window to assist server creation """

    def __init__(self, server, parent=None):
        super().__init__(parent=parent)
        self.server = server
        self.setWindowTitle("Server Setup")

        self.lay = QGridLayout(self)

        # self.setFrameShape(QtWidgets.QFrame.Panel)
        self.setObjectName("ServerSetup")

        stylesheet  = """QWidget#ServerSetup {"""
        stylesheet += f"""background-color: #28282E;"""
        stylesheet += """}"""
        stylesheet += """QLabel { color: white; }"""

        self.setStyleSheet(stylesheet)
        self.b_setup = {}

        # Create login details for the server itself (internally, externally)
        b = self.add_step("Configure Server", 'ui/icons/database.png', 0,0)
        b.setEnabled(True)
        b.clicked.connect(self.server.config_server)
        self.add_arrow(0,1)

        # Prep Wireguard: method (manual or automatic), config, subet, ip, etc...
        b = self.add_step("Create Tunnel", 'ui/icons/database_secured.png', 0,2)
        b.clicked.connect(self.server.config_tunnel)
        self.add_arrow(0,3)

        # Guide to turning on port forwarding
        b = self.add_step("Port Forward", 'ui/icons/database.png', 0,4)
        b.clicked.connect(lambda: PortForward(self.server))

        # Create remote user into config/database
        b = self.add_step("Create Remote User", 'ui/icons/user.png', 1,0)
        b.clicked.connect(self.server.new_user)
        self.add_arrow(1,1)

        # Authenticate remote user, update wireguard, update hba
        b = self.add_step("Authenticate Remote User", 'ui/icons/user_secured.png', 1,2)
        b.clicked.connect(lambda: self.server.toggle_auth(True))

        # Create login details for the server itself (internally, externally)
        b = self.add_step("Reset Server", 'ui/icons/database.png', 2,0)
        b.setEnabled(True)
        b.clicked.connect(self.server.reset_server)

        # TODO: Dropbox auth
        # b = self.add_step("Connect Media Storage", 'ui/icons/database.png', 2,0)
        # self.add_arrow(2,1)

        # TODO: Media mappings think this through
        # b = self.add_step("Define Media Mapping", 'ui/icons/database.png', 2,2)

    def add_step(self, label_text, icon, i, j):
        """ Add setup step (button) """

        slay = QHBoxLayout()
        icon = QPixmap(icon)

        key = label_text.lower()

        self.b_setup[key] = QPushButton(label_text)
        self.b_setup[key].setEnabled(False)
        self.b_setup[key].setObjectName("setup_button")
        self.b_setup[key].setStyleSheet(
            """QPushButton#setup_button {
                color: #848484;
                background: transparent;
            }
            QPushButton#setup_button::hover{
            	color: white;
            }
            QPushButton#setup_button::pressed{
            	color: #848484;
            }""")

        icon = icon.scaledToWidth(50, Qt.SmoothTransformation)

        self.b_setup[key].setIcon(QIcon(icon))
        self.b_setup[key].setIconSize(icon.rect().size())

        slay.addWidget(self.b_setup[key])
        self.lay.addWidget(self.b_setup[key], i,j, alignment=Qt.AlignLeft)

        return self.b_setup[key]

    def add_arrow(self, i,j):
        """ Add setup flow arrow """

        arrow = QLabel("→")
        arrow.setObjectName("arrow")
        self.lay.addWidget(arrow, i,j)

    def step_abled(self, keys, abled):
        for keyb, button in self.b_setup.items():
            for key in keys:
                if key.lower() == keyb:
                    button.setEnabled(abled)

    def step_enable(self, keys):
        self.step_abled(keys, True)

    def step_disable(self, keys):
        self.step_abled(keys, False)

def PortForward(server):

    text = f"""_Forward these ports to the server_

    - TCP Port: {server.auth_port}
    - UDP Port: {server.wg_port}
    """

    msg = QMessageBox(server)
    msg.setTextFormat(Qt.MarkdownText)
    msg.setText(text)
    msg.setInformativeText("And check firewalls while you're at it!")
    msg.setWindowTitle("Port Forwarding")
    msg.exec_()

# ----------------------- AUTHENTICATION PROMPTS AND FLOWS

class ServerAuth(UI_Dialog):
    """ Form to define a new authenticatable user """

    def __init__(self, parent = None):
        super(ServerAuth, self).__init__(parent)

        layout = QVBoxLayout(self)

        self.UNAME = QtWidgets.QLineEdit()
        self.UNAME.setPlaceholderText("New Username")

        self.ASSIGN_IP = QtWidgets.QLineEdit()
        self.ASSIGN_IP.setPlaceholderText("New Assigned IP")

        layout.addWidget(self.UNAME)
        layout.addWidget(self.ASSIGN_IP)

        # OK and Cancel buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            Qt.Horizontal, self)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def get_output(self):

        self.auth_new = {
            "UNAME" : self.UNAME.text(), "ASSIGN_IP" : self.ASSIGN_IP.text(),
        }

        return (self.auth_new)

class ServerConfig(UI_Dialog):
    """ Form for the server password and other details """

    def __init__(self, parent = None):
        super(ServerConfig, self).__init__(parent)

        layout = QVBoxLayout(self)

        self.S_PWD = QtWidgets.QLineEdit()
        self.S_PWD.setPlaceholderText("Server Password")
        self.S_PWD.setEchoMode(QtWidgets.QLineEdit.Password)

        info = QLabel("Create password for Resolve Mission Control Server")
        layout.addWidget(info)
        layout.addWidget(self.S_PWD)

        self.S_PORT = QtWidgets.QLineEdit()
        self.S_PORT.setPlaceholderText("Server TCP Port (Default: 4444)")

        info = QLabel("Define TCP Port for Authentication Server")
        layout.addWidget(info)
        layout.addWidget(self.S_PORT)

        self.SUBNET = QtWidgets.QLineEdit()
        self.SUBNET.setPlaceholderText("9.0.0.0/24")

        info = QLabel("What should the Wireguard subnet be?")
        layout.addWidget(info)
        layout.addWidget(self.SUBNET)

        # OK and Cancel buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def get_output(self):
        return self.S_PWD.text(), self.S_PORT.text(), self.SUBNET.text()

class TunnelConfig(UI_Dialog):
    """ Form for the Wireguard details """

    def __init__(self, parent = None):
        super(TunnelConfig, self).__init__(parent)

        layout = QVBoxLayout(self)

        self.WG_PORT = QtWidgets.QLineEdit()
        self.WG_PORT.setPlaceholderText("Tunnel UDP Port (Default: 51820)")

        info = QLabel("Which UDP port do you want the Wireguard tunnel on?")
        layout.addWidget(info)
        layout.addWidget(self.WG_PORT)

        # OK and Cancel buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def get_output(self):
        return self.WG_PORT.text()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Server(app)
    w.show()

    if len(sys.argv) > 1 and sys.argv[1] == 'setup':
        w.setup_window.show()

    sys.exit(app.exec_())
