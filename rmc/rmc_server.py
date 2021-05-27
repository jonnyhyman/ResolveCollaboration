# rmc imports
from rmc_common import *

from auth.server import tcp_server
from auth.crypt import passkey, Fernet

#
from util import postgres, default_hba, sudoscience

from wireguard import WireguardServer_macOS, WireguardServer_Windows

# 3rd party package imports
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import psycopg2

# built-in imports
from pathlib import Path
from ipaddress import ip_address, ip_network
import sys

import asyncio
import datetime

from multiprocessing import Process, Queue
from subprocess import Popen, PIPE
import subprocess

import platform
user_platform = platform.system().lower()

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
    wg_only = True

    def __init__(self, app, parent=None):
        super().__init__(app, parent=parent)

        self.setWindowTitle("Resolve Mission Control Server")

        # Define buttons
        self.b_dbadd = QPushButton("+")
        self.b_dbcon = QPushButton("⇄")
        self.b_dbcyc = QPushButton("⟳")
        self.b_dbdel = QPushButton("×")
        self.b_tunn = QPushButton("Activate Tunnel")
        self.b_auth = QPushButton("Activate Authentication")

        # The ordering here reflects the lifecycle of a database
        # (create, connect, restart, delete)
        self.b_dbadd.setToolTip("Create Resolve Database")
        self.b_dbcon.setToolTip("Connect to Resolve Database")
        self.b_dbcyc.setToolTip("Restart PostgreSQL Server")
        self.b_dbdel.setToolTip("Delete Resolve Database (FOREVER)")


        for b in [self.b_dbadd, self.b_dbcon, self.b_dbcyc, self.b_dbdel]:
            self.p_LU.lay.addWidget(b)
            b.setObjectName("LU_buttons")
            b.setStyleSheet(f"""QPushButton#LU_buttons {{
                                        font-size: 15px;
                                        color: #848484;
                                        background: transparent;
                                        }}
                                        QPushButton#LU_buttons::hover{{
                                        	color: white;
                                        }}
                                        QPushButton#LU_buttons::pressed{{
                                        	color: #848484;
                                        }}""")

        for b in [self.b_tunn, self.b_auth]:
            self.p_RU.lay.addWidget(b)

        self.b_tunn.setEnabled(False)
        self.b_tunn.setCheckable(True)

        self.b_auth.setEnabled(False)
        self.b_auth.setCheckable(True)

        # BUTTON CONNECT
        self.setup_window = ServerSetup(self)
        self.p_RB.lay.addWidget(self.setup_window, alignment=Qt.AlignCenter)

        self.message = QLabel("")
        self.message.setTextFormat(Qt.MarkdownText)
        self.p_RB.lay.addWidget(self.message, alignment=Qt.AlignBottom)

        self.b_dbadd.clicked.connect(self.database_create)
        self.b_dbcon.clicked.connect(self.database_connect)
        self.b_dbcyc.clicked.connect(self.database_restart)
        self.b_dbdel.clicked.connect(self.database_delete)
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

            # Backwards compatibility, v0.1.2 onwards
            if 'only' not in self.config['wireguard'].keys():
                self.config['wireguard']['only'] = self.wg_only
                self.config.save()

            self.b_auth.setEnabled(True)
            self.b_tunn.setEnabled(True)
            self.wg_port = self.config['wireguard']['port']
            self.wg_only = self.config['wireguard']['only']
            self.setup_window.step_enable(['Port Forward',
                                           'Authenticate Remote User'])

            if user_platform == 'darwin':
                self.wireguard = WireguardServer_macOS(config=self.config)

            elif user_platform == 'windows':
                self.wireguard = WireguardServer_Windows(config=self.config)

                # Check if already running, set ui state
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

            if not prompt_result:
                return

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

            self.subnet = str(self.subnet)

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

            # Reset the entire userlist
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
                            " now. Re-open to start a new configuration")
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

        # Restart authentication server (send new userlist)
        # if running:
        if hasattr(self,'tcp_proc'):
            self.toggle_auth(False)
            self.toggle_auth(True)

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
                                args = (C_IP, S_PORT, self.tcp_queue,
                                            [self.config['userlist'],
                                             self.config['auth']['authkey'],
                                             self.wg_port,
                                             self.wg_only,
                                             self.subnet],
                                        )
                                )

        self.tcp_timer = QTimer(self)
        self.tcp_timer.timeout.connect(self.update_authentication)
        self.tcp_timer.start(500)
        self.tcp_proc.start()

        self.message.setText("Authentication server opening...")

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
                # update userlist with [UNAME, PKEYU]
                print("... Going to authenticated_user")
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

            del self.tcp_proc

            # Update HBA here in case it failed somewhere else
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
                print(f">>> Added {UNAME} to userlist")
                self.config.save()
                break

        self.wireguard.update_config(self.config['userlist'])
        self.update_hba()
        self.update_userview()

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

        self.update_userview()

        # Restart authentication server (send new userlist)
        self.toggle_auth(False)
        self.toggle_auth(True)

    def database_create(self):
        """ Create a new PostgreSQL database """

        # low risk secrets:
        connection = psycopg2.connect(
                                          host    =  '127.0.0.1',
                                          user    =  'postgres',
                                          database=  'postgres',
                                          password=  "DaVinci",
                                          port    = "5432",
                                          connect_timeout=3,
                                        )
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = connection.cursor()

        cursor.execute("SELECT rolname FROM pg_roles")
        roles = [item for sublist in cursor.fetchall() for item in sublist]

        # PROMPT: New user/pass or existing user? and new database name?
        config = DatabaseConfig(roles, self)
        output = config.exec_()

        if not output:
            return

        username, password, databasename = config.get_output()

        if username == "" or databasename == "" or password == "":
            UI_Error(self, "Input Error", "Username and database name cannot be blank")

            cursor.close()
            connection.close()

            self.database_create()
            return

        if username not in roles:
            psql = f"""
            CREATE ROLE {username}
            CREATEDB
            LOGIN
            SUPERUSER
            PASSWORD '{password}';"""

            try:
                cursor.execute(psql)
                connection.commit()
            except Exception as e:
                UI_Error(self, 'PostgreSQL Error', e)
                return

        try:
            cursor.execute(f"CREATE DATABASE {databasename} WITH OWNER='{username}'")
            connection.commit()
        except psycopg2.errors.DuplicateDatabase as e:
            UI_Error(self, 'Already Exists', e)
            cursor.close()
            connection.close()
            return

        UI_Successful(self, "Database Created!",
            "Upon first connect to the database, Resolve will fill it with"
            " the standard tables and entries")

        db = {
                    'host' : "127.0.0.1",
                    'name' : databasename,
                    'user' : username,
                    'pass' : password
        }

        self.dbses.add_database(db, select=False)

    def database_connect(self):

        added = super().database_connect()

        if added:
            self.update_hba()

    def database_restart(self):
        """ Restart PostgreSQL """

        icon = QPixmap(link('ui/icons/postgres.png'))
        icon = icon.scaledToWidth(100, Qt.SmoothTransformation)

        reply = UI_Question(self).ask("Restart PostgreSQL",
                                "Restart the PostgreSQL Server?", icon)

        if reply != QtWidgets.QMessageBox.Yes:
            return

        if user_platform == 'darwin':
            out = postgres.postgres_restart_macos()

        elif user_platform == 'windows':
            out = postgres.postgres_restart_windows()

        print(f">>> PostgreSQL restarted with value : {out}")

        if out:
            self.message.setText("_PostgreSQL Server Restarted_")
        else:
            self.message.setText("__Failed to restart PostgreSQL Server__")

    def database_delete(self):
        """ Delete a postgres database permanently """

        icon = QPixmap(link('ui/icons/postgres.png'))
        icon = icon.scaledToWidth(100, Qt.SmoothTransformation)

        ui_db = self.dbses.selected()

        if not ui_db:
            return

        db_name = ui_db.db_details['name']

        quit_msg = f"Are you sure you want to delete database {db_name}?"
        reply = UI_Question(self).ask('Delete Database?', quit_msg, icon)

        if reply != QtWidgets.QMessageBox.Yes:
            return

        quit_msg = f"Seriously, this will delete everything in {db_name}. Continue?"

        reply = UI_Question(self).ask('Delete Database?', quit_msg, icon)

        if reply != QtWidgets.QMessageBox.Yes:
            return

        getpass = ServerPassword(self)
        output = getpass.exec_()

        if not getpass:
            return

        if self.config['auth']['authkey'] != passkey(getpass.get_output()).decode():
            UI_Error(self, "Incorrect password", "Please try again")
            return

        # Now backend
        if db_name in ['postgres', 'resolve']:
            # Don't allow those to be deleted
            UI_Error(self, "Cannot remove", "Databases `postgres` and `resolve`"
                                            "cannot be deleted")
            return

        # Remove UI first
        self.database_remove(ui_db)

        # Then backend
        # low risk secrets:
        connection = psycopg2.connect(
                                          host    =  '127.0.0.1',
                                          user    =  'postgres',
                                          database=  'postgres',
                                          password=  "DaVinci",
                                          port    = "5432",
                                          connect_timeout=3,
                                        )
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = connection.cursor()

        # terminate user connections
        cursor.execute(f"""SELECT pg_terminate_backend (pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '{db_name}';""")

        cursor.execute(f"DROP DATABASE {db_name}")
        connection.commit()

        cursor.close()
        connection.close()

        UI_Successful(self, f"Database {db_name} Deleted!",
                            "I sure hope that was intentional!")

    def update_hba(self, debug=True):
        """ Update the access permissions for all databases in list """

        hba_lines = []
        hba_file = None
        connection = None

        for db, ui_db in self.dbses.ui_dbses.items():

            self.dbses.select(ui_db.db_details, fail_queitly = True)
            connection = ui_db.connection

            if ui_db.db_details['host'] != "127.0.0.1":
                # ONLY change pg_hba.conf on LOCAL machine (server)
                #  any remote call would be erroneous
                continue

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

                db_name = ui_db.db_details['name']
                db_user = ui_db.db_details['user']

                db_name = f'"{db_name}"' # allows for spaces
                db_user = f'"{db_user}"' # allows for spaces

                hba_lines.append("    ".join(
                        ['host', db_name, db_user, self.subnet, 'md5']
                    )
                )

        if hba_file and connection:

            if debug: print("... Building hba update")

            # Snag the last `hba_file` and `connection` from the for loop
            #  to actually execute the file saving etc...

            if user_platform == 'darwin':
                command = ""

                hba_file_backup = Path(hba_file).parent / "pg_hba_rmcsbackup.conf"
                command += f"""sudo cp -b "{hba_file}" "{hba_file_backup}"; """

                # Append our new lines into configuration
                for hba_line in hba_lines:

                    command += (f"""if ! sudo grep -Fx '{hba_line}' '{hba_file}'; """
                                f"""then echo '{hba_line}' | sudo tee -a '{hba_file}'; fi;""")

                if debug: readable = ';   \n'.join(command.split(';'))
                if debug: print(f"... About to run >>> \n{readable}\n---")

                try:
                    out,err = sudoscience.elevated_Popen(command, errors=True,
                        prompt=("Resolve Mission Control wants to read PostgreSQL "
                                "access permissions and alter them if needed")
                    )
                except PermissionError:
                    return

                # Reload config
                crs.execute("select pg_reload_conf()")
                out = crs.fetchall()[0][0]
                crs.close()

                print(f">>> pg_hba.conf updated with exit code: {out}")

                if out:
                    self.message.setText("_Updated Host-Based Authentication_")
                else:
                    self.message.setText("__Host-Based Authentication failed to update__")

                # True if suceeded, False if failed
                return err.strip() == ""

            elif user_platform == 'windows':

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
                else:
                    self.message.setText("__Host-Based Authentication failed to update__")


                # True if suceeded, False if failed
                return out
            else:
                raise(Exception(f"Platform {user_platform} is not supported"))


    def config_tunnel(self):
        """ Create a new Wireguard configuration
            1) Define port and subnet
            2) Create configuration based on **authenticated** users in userlist
            3) Activate tunnel
        """

        prompt = TunnelConfig(self)
        prompt_result = prompt.exec_()
        PORT, ONLY = prompt.get_output()

        if not prompt_result:
            return

        if PORT == "":
            PORT = self.wg_port

        # Port verify
        try:
            self.wg_port = int(PORT)

        except ValueError as e:
            UI_Error(self, "Invalid Assignment Port", "Was port an integer?")
            self.config_tunnel()
            return

        self.wg_only = ONLY

        if user_platform == 'darwin':

            try:
                self.wireguard = WireguardServer_macOS(force_reset = True,
                                                        port = self.wg_port,
                                                        subnet = self.subnet)

            except PermissionError as e:
                UI_Error(self, "Wireguard Configuration Failed",
                    f"Must be run as root\n>>> sudo python rmc_server.py\n\n{e}")
                return

        elif user_platform == 'windows':

            try:
                self.wireguard = WireguardServer_Windows(force_reset = True,
                                                        port = self.wg_port,
                                                        subnet = self.subnet)

            except PermissionError as e:
                UI_Error(self, "Wireguard Configuration Failed",
                    f"Must be run as admin\n\n{e}")
                return
        else:
            raise(NotImplementedError("Only macOS/Windows Wireguard Server supported"))

        # first ip in the subnet is always the server
        first_ip = next(ip_network(self.subnet).hosts())

        self.config['wireguard'] = {}
        self.config['wireguard']['port'] = self.wg_port
        self.config['wireguard']['only'] = self.wg_only
        self.config['wireguard']['pk'] = self.wireguard.pk
        self.config['wireguard']['Pk'] = self.wireguard.Pk
        self.config['userlist'][0]['Pk'] = self.wireguard.Pk
        self.config['userlist'][0]['ip'] = first_ip
        self.config.save()

        self.wireguard.update_config(self.config['userlist'])

        self.b_tunn.setEnabled(True)
        self.b_auth.setEnabled(True)

        self.setup_window.step_enable(['Port Forward',
                                       'Authenticate Remote User'])

        self.update_userview()

    def toggle_tunnel(self, state):
        """ Toggle the Wireguard directly with wg or wg-quick up/down
        """

        if not hasattr(self, 'wireguard'):
            print("... Tried to toggle non-existent Wireguard instance")
            return

        if state:
            # Open tunnel
            status = self.wireguard.up()
            self.message.setText(f"Wireguard tunnel{status} open!")

            if not 'failed' in status:
                self.b_tunn.setText("Deactivate Tunnel")

        else:
            # Close tunnel
            status = self.wireguard.down()
            self.message.setText(f"Wireguard tunnel{status} closed!")

            if not 'failed' in status:
                self.b_tunn.setText("Activate Tunnel")

        if not 'failed' in status:
            self.b_tunn.setChecked(state)
        else:
            self.b_tunn.setChecked(not state)

    def closeEvent(self, event):
        """ Upon closing server:
            - Shutdown authentication server
            - Shutdown Wireguard tunnel
        """
        self.close_authentication()

        # use weak status (button.isChecked) so we don't need to request sudo
        if hasattr(self,'wireguard') and self.b_tunn.isChecked():

            icon = QPixmap(link('ui/icons/wireguard.png'))
            icon = icon.scaledToWidth(100, Qt.SmoothTransformation)

            reply = UI_Question(self).ask('Close Tunnel?',
                             "Do you want to shutdown Wireguard?",
                             icon)



            if reply == QtWidgets.QMessageBox.Yes:
                self.toggle_tunnel(False)

        super().closeEvent(event)

class ServerSetup(QWidget):
    """ Setup window to assist server creation """

    def __init__(self, server, parent=None):
        super().__init__(parent=parent)
        self.server = server
        self.setWindowTitle("Server Setup")

        self.lay = QGridLayout(self)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)

        # self.setFrameShape(QtWidgets.QFrame.Panel)
        self.setObjectName("ServerSetup")

        stylesheet  = """QWidget#ServerSetup {"""
        stylesheet += f"""background-color: #28282E;"""
        stylesheet += """}"""
        stylesheet += """QLabel { color: white; }"""

        self.setStyleSheet(stylesheet)
        self.b_setup = {}

        # Create login details for the server itself (internally, externally)
        b = self.add_step("Configure Server", link('ui/icons/database.png'), 0,0)
        b.setEnabled(True)
        b.clicked.connect(self.server.config_server)
        self.add_arrow(0,1)

        # Prep Wireguard: method (manual or automatic), config, subet, ip, etc...
        b = self.add_step("Create Tunnel", link('ui/icons/database_secured.png'), 0,2)
        b.clicked.connect(self.server.config_tunnel)
        self.add_arrow(0,3)

        # Guide to turning on port forwarding
        b = self.add_step("Port Forward", link('ui/icons/database.png'), 0,4)
        b.clicked.connect(lambda: PortForward(self.server))

        # Create remote user into config/database
        b = self.add_step("Create Remote User", link('ui/icons/user.png'), 1,0)
        b.clicked.connect(self.server.new_user)
        self.add_arrow(1,1)

        # Authenticate remote user, update wireguard, update hba
        b = self.add_step("Authenticate Remote User", link('ui/icons/user_secured.png'), 1,2)
        b.clicked.connect(lambda: self.server.toggle_auth(True))

        # Create login details for the server itself (internally, externally)
        b = self.add_step("Reset Server", link('ui/icons/database.png'), 2,0)
        b.setEnabled(True)
        b.clicked.connect(self.server.reset_server)

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


class ServerPassword(UI_Dialog):
    """ Form for the server password and other details """

    def __init__(self, parent = None):
        super(ServerPassword, self).__init__(parent)

        layout = QVBoxLayout(self)

        self.S_PWD = QtWidgets.QLineEdit()
        self.S_PWD.setPlaceholderText("Server Password")
        self.S_PWD.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addWidget(self.S_PWD)

        # OK and Cancel buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def get_output(self):
        return self.S_PWD.text()

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

        self.WG_ALL = QtWidgets.QPushButton("All traffic")
        self.WG_ALL.setCheckable(True)
        self.WG_ALL.setChecked(False)

        self.WG_ONLY = QtWidgets.QPushButton("Resolve traffic only")
        self.WG_ONLY.setCheckable(True)
        self.WG_ONLY.setChecked(True)

        self.WG_ALL.clicked.connect(lambda x: self.WG_ONLY.setChecked(not x))
        self.WG_ONLY.clicked.connect(lambda x: self.WG_ALL.setChecked(not x))

        pathbox = QHBoxLayout()
        pathbox.addWidget(self.WG_ALL)
        pathbox.addWidget(self.WG_ONLY)
        pathbox.setContentsMargins(0,0,0,0)
        pathbox.setSpacing(0)

        info = QLabel("Route _all_ user traffic through Wireguard, or _only_ __Resolve__ traffic?")
        info.setTextFormat(Qt.MarkdownText)

        layout.addWidget(info)
        layout.addLayout(pathbox)

        # OK and Cancel buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def get_output(self):

        if self.WG_ALL.isChecked():
            WG_ONLY = False

        if self.WG_ONLY.isChecked():
            WG_ONLY = True

        return self.WG_PORT.text(), WG_ONLY


class DatabaseConfig(UI_Dialog):
    """ Form for creating a database """

    def __init__(self, roles, parent = None):
        super(DatabaseConfig, self).__init__(parent)

        layout = QVBoxLayout(self)

        info = QLabel(f"Enter the name of an existing user or, "
                        "to create a new login role, enter a unique name")
        layout.addWidget(info)

        self.NAME = QtWidgets.QLineEdit()
        self.NAME.setPlaceholderText(f"Database Username: {', '.join(roles)} or a new username")
        layout.addWidget(self.NAME)

        info = QLabel("\nCreate password for a new role. (Leave blank for existing role)")
        layout.addWidget(info)

        self.PASS = QtWidgets.QLineEdit()
        self.PASS.setPlaceholderText("Database Password")
        self.PASS.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addWidget(self.PASS)

        info = QLabel("\nWhat should the database be called?")
        layout.addWidget(info)

        self.DB_NAME = QtWidgets.QLineEdit()
        self.DB_NAME.setPlaceholderText("Database Name")
        layout.addWidget(self.DB_NAME)

        # OK and Cancel buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def get_output(self):
        return self.NAME.text(), self.PASS.text(), self.DB_NAME.text()

if __name__ == '__main__':

    app = QApplication(sys.argv)
    app.setApplicationName("Resolve Mission Control Server")

    icon = QIcon(link('ui/icons/icon_rmcs.ico'))
    app.setWindowIcon(icon)

    w = Server(app)
    w.show()
    w.setWindowIcon(icon)

    sys.exit(app.exec_())
