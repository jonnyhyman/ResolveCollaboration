# package imports
# from PyQt5.QtCore import Qt
# from PyQt5 import QtWidgets, QtCore, QtGui
# from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QPushButton,
#                              QLabel, QSizePolicy, QSlider, QSpacerItem,
#                              QVBoxLayout, QWidget, QDialog, QMessageBox)
# from PyQt5.QtWidgets import QFileDialog, QDialog
# from PyQt5.QtWidgets import QApplication, QTableView
# from PyQt5.QtCore import QAbstractTableModel, Qt

from PyQt5 import QtWidgets, QtCore, QtGui
Qt = QtCore.Qt


QApplication = QtWidgets.QApplication
QHBoxLayout = QtWidgets.QHBoxLayout
QPushButton = QtWidgets.QPushButton
QLabel = QtWidgets.QLabel
QSizePolicy = QtWidgets.QSizePolicy
QSlider = QtWidgets.QSlider
QSpacerItem = QtWidgets.QSpacerItem
QVBoxLayout = QtWidgets.QVBoxLayout
QWidget = QtWidgets.QWidget
QDialog = QtWidgets.QDialog
QMessageBox = QtWidgets.QMessageBox

QFileDialog = QtWidgets.QFileDialog
QDialog = QtWidgets.QDialog
QApplication = QtWidgets.QApplication
QTableView = QtWidgets.QTableView

from PyQt5.QtCore import QAbstractTableModel

# from cryptography.hazmat.backends import default_backend
import cryptography.hazmat.backends
default_backend = cryptography.hazmat.backends.default_backend

# from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import cryptography.hazmat.primitives.kdf.pbkdf2
PBKDF2HMAC = cryptography.hazmat.primitives.kdf.pbkdf2.PBKDF2HMAC

#from cryptography.fernet import Fernet, InvalidToken
import cryptography.fernet
Fernet = cryptography.fernet.Fernet
InvalidToken = cryptography.fernet.InvalidToken

# from cryptography.hazmat.primitives import hashes
import cryptography.hazmat.primitives
hashes = cryptography.hazmat.primitives.hashes

import pandas as pd
import psycopg2

from wgnlpy import PrivateKey

# built-in imports
from pathlib import Path
import ipaddress
import sys

import asyncio
import base64
import datetime

# local imports
# from styles import *

# helper functions
def passkey(password):
    password = password.encode()  # Convert to type bytes
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=password,
        iterations=100000,
        backend=default_backend()
    )
    # if anything, this is what gets saved in a database
    return base64.urlsafe_b64encode(kdf.derive(password))

def FileDialog(directory='', forOpen=True, fmt='', isFolder=False):
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    options |= QFileDialog.DontUseCustomDirectoryIcons
    dialog = QFileDialog()
    dialog.setOptions(options)

    dialog.setFilter(dialog.filter() | QtCore.QDir.Hidden)

    # ARE WE TALKING ABOUT FILES OR FOLDERS
    if isFolder:
        dialog.setFileMode(QFileDialog.DirectoryOnly)
    else:
        dialog.setFileMode(QFileDialog.AnyFile)
    # OPENING OR SAVING
    dialog.setAcceptMode(QFileDialog.AcceptOpen) if forOpen else dialog.setAcceptMode(QFileDialog.AcceptSave)

    # SET FORMAT, IF SPECIFIED
    if fmt != '' and isFolder is False:
        dialog.setDefaultSuffix(fmt)
        dialog.setNameFilters([f'{fmt} (*.{fmt})'])

    # SET THE STARTING DIRECTORY
    if directory != '':
        dialog.setDirectory(str(directory))
    else:
        dialog.setDirectory(str(Path('').absolute()))


    if dialog.exec_() == QDialog.Accepted:
        path = dialog.selectedFiles()[0]  # returns a list
        return path
    else:
        return ''

def UpdateHBA():
    # Use "SHOW hba_file" to get location of hba file
    # Modify
    # Restart server: `etc/init.d/postgresql restart` or `systemctl restart postgresql-xx.service` or something else
    pass

# gui
class Window(QWidget):

    subnet = '9.0.0.0/24'
    auth_port = 4444 # TODO: Test on 51820 instead
    wg_port = 51820

    def __init__(self, app, parent=None):
        super().__init__(parent=parent)

        self.app = app
        self.setWindowTitle("Resolve Mission Control")

        self.lay = QVBoxLayout(self)

        self.context_lay = QHBoxLayout()
        self.lay.addLayout(self.context_lay)

        self.context_switch = QPushButton("Client")
        self.context_switch.setCheckable(True)
        self.context_switch.clicked.connect(self.toggle_context)

        self.context_action = QPushButton("Make New Connection")
        self.context_action.clicked.connect(self.authenticate)

        self.context_reconn = QPushButton("Reconnect")
        self.context_reconn.clicked.connect(self.reconnect)

        # layouts
        self.context_lay.addWidget( self.context_switch )
        self.context_lay.addWidget( self.context_action )
        self.context_lay.addWidget( self.context_reconn )

        self.init_resolveview()

    def toggle_context(self, state):

        if state:
            self.context_switch.setText("Server")
            self.context_action.setText("New Team Member")
            self.context_reconn.setText("Authenticate")
            self.init_server()

            # Update timer
            self.resolvedb_connect = True

            auth_db = DatabaseAuth(self)
            auth_result = auth_db.exec_()

            if auth_result:
                self.db_name, self.db_user, self.db_pass = auth_db.get_output()

                self.update_resolveview()
                self.update_timer = QtCore.QTimer()
                self.update_timer.timeout.connect(self.update_resolveview)
                self.update_timer.start(15*1000)

        else:
            self.context_switch.setText("Client")
            self.context_action.setText("Make New Connection")
            self.context_reconn.setText("Connect to Resolve")

        self.context_switch.setChecked(state)

    def resolvedb_users(self):

        cols = {"Name":"Name",
                "LastSeen":"Last Seen",
                "ClientAddr":"Local IP",
                # "UserDefinedClientName",
                "ClientMachineType":"OS",
                "SysId":"ID"}

        dat = pd.DataFrame(columns=cols.values())

        if not self.resolvedb_connect:
            return dat

        try:
            with psycopg2.connect(user=self.db_user,
                                  password=self.db_pass,
                                  host="9.0.0.1", # TODO: Make dynamic not string
                                  port="5432",
                                  connect_timeout=3,
                                  database=self.db_name) as connection:

                sql = ','.join(['"'+ci+'"' for ci in cols])
                sql = f'''SELECT {sql} FROM public."Sm2SysIdEntry" '''
                dat = pd.read_sql_query(sql, connection)
                dat = dat.rename(columns=cols)

                self.resolve_status.setText("Connected to Resolve database")

                # modify some entries
                dat = dat.replace({"OS": {4:'macos', 0:'Windows'} })

                cursor = connection.cursor()
                cursor.execute('''SELECT now()''')
                nowtime = (cursor.fetchall()[0][0]).timestamp()

                for idx, row in dat.iterrows():

                    dt = row['Last Seen']-nowtime
                    dt = datetime.timedelta(seconds=dt)

                    days, seconds = dt.days, dt.seconds
                    hours = days * 24 + seconds // 3600
                    minutes = (seconds % 3600) // 60
                    seconds = seconds % 60

                    dt =(   f"{str(days) + ' days ' if abs(days) > 1 else ''}"
                            f"{str(hours) + ' hrs ' if abs(hours) > 1 else ''}"
                            f"{str(minutes) + ' min ' if abs(minutes) > 1 else ''}"
                            f"{str(seconds) + ' sec' if abs(seconds) > 1 else ''}")

                    dat.loc[idx, 'Last Seen'] = dt

        except psycopg2.OperationalError as e:
            self.resolve_status.setText(f"Error connecting to database: {e}")
            self.resolvedb_connect = False

        return dat

    def resolvedb_projects(self, people):

        cols = {"ProjectName":"Name",
                "IsLiveCollaborationEnabled":"Collaboration Enabled",
                "SysIds":"Live Users",
                "SM_Project_id": "ID"}

        dat = pd.DataFrame(columns=cols.values())

        if not self.resolvedb_connect:
            return dat

        try:
            with psycopg2.connect(user=self.db_name,
                                  password=self.db_pass,
                                  host="9.0.0.1", # TODO: Make dynamic not string
                                  port="5432",
                                  connect_timeout=3,
                                  database=self.db_name) as connection:

                sql = ','.join(['"'+ci+'"' for ci in cols])
                sql = f'''SELECT {sql} FROM public."SM_Project" '''
                dat = pd.read_sql_query(sql, connection)
                dat = dat.rename(columns=cols)

                self.resolve_status.setText("Connected to Resolve database")

                # modify some entries
                for idx, row in dat.iterrows():

                    if row['Live Users'] is not None:
                        users = list(row['Live Users'].split(','))

                        users = ', '.join([list(people['Name'][people['ID'] == user])[0]
                                                        for user in users
                                                if (people['ID'] == user).any()])

                        dat.loc[idx, 'Live Users'] = users

        except psycopg2.OperationalError as e:
            self.resolve_status.setText("Resolve database timed out")
            self.resolvedb_connect = False

        return dat

    def init_resolveview(self):

        self.resolvedb_connect = False

        # People
        self.label = QLabel("### People")
        self.label.setTextFormat(Qt.MarkdownText)
        self.lay.addWidget(self.label)

        people = self.resolvedb_users()
        model = pandasModel(people)
        self.people_view = QTableView()
        self.people_view.setModel(model)
        self.lay.addWidget(self.people_view)

        # Projects
        self.label = QLabel("### Projects")
        self.label.setTextFormat(Qt.MarkdownText)
        self.lay.addWidget(self.label)

        model = pandasModel(self.resolvedb_projects(people))
        self.projects_view = QTableView()
        self.projects_view.setModel(model)
        self.lay.addWidget(self.projects_view)

        self.people_view.horizontalHeader().setSectionResizeMode(
                                                QtWidgets.QHeaderView.Stretch)
        self.projects_view.horizontalHeader().setSectionResizeMode(
                                                QtWidgets.QHeaderView.Stretch)

        self.resolve_status = QLabel("Not connected to Resolve")
        self.lay.addWidget(self.resolve_status)

    def update_resolveview(self):
        people = self.resolvedb_users()
        model = pandasModel(people)
        self.people_view.setModel(model)

        model = pandasModel(self.resolvedb_projects(people))
        self.projects_view.setModel(model)

    def init_server(self):

        # log in
        passkey_file = Path("./server_passkey")
        success = False

        if passkey_file.exists():
            prompt = PromptServerPassword(self)
            prompt_result = prompt.exec_()
            pass_check, Pk = prompt.get_output()

            if prompt_result and len(pass_check) > 0:

                pass_check = passkey(pass_check)

                with open(passkey_file, 'r') as file:
                    pass_truth = file.read()

                if pass_check.decode() != pass_truth:
                    self.error("Invalid Server Password", "Try again?")
                else:
                    success = True
                    self.auth_key = pass_check.decode()

        else:
            prompt = PromptServerPassword(self)
            prompt_result = prompt.exec_()
            pass_check, Pk = prompt.get_output()

            if prompt_result and len(pass_check) > 0:
                key = passkey(pass_check)

                with open(passkey_file, 'w') as saveto:
                    saveto.write(key.decode())

                success = True
                self.auth_key = key.decode()

        if not success:
            # Switch back to client mode if log in to server failed
            self.toggle_context(False)
            self.context_switch.setChecked(False)

        else:
            # open database on successful login
            database = Path("./server_database.csv")

            if database.exists():
                self.df = pd.read_csv(database)

                if len(Pk) != 0:
                    self.df.loc[self.df['User']=='admin','Public Key'] = Pk

                self.df.to_csv(Path("./server_database.csv"), index=False)

            else:
                first_ip = next(ipaddress.ip_network(self.subnet).hosts())

                if len(Pk) == 0:
                    # ------------- GENERATE NEW KEYS AND CONF FILE
                    pk = PrivateKey.generate()
                    Pk = pk.public_key()

                    #Server Config
                    conf = (f"""[Interface]\n"""
                            f"""PrivateKey = {pk}\n"""
                            f"""ListenPort = {self.wg_port}\n"""
                            f"""Address = {first_ip}\n""")

                    saveto = FileDialog(forOpen=False, fmt='conf')
                    with open(saveto, 'w') as save_conf:
                        save_conf.write(conf)

                self.df = pd.DataFrame(columns=["User",
                                                "IP Assigned",
                                                "Public Key",
                                                "Last Seen IP"])

                self.df = self.df.append({
                                "User"         : "admin",
                                "IP Assigned"  : first_ip,
                                "Public Key"   : Pk,
                                "Last Seen IP" : ""},
                                        ignore_index=True)

                self.df.to_csv(Path("./server_database.csv"), index=False)

    def error(self, error_message, infotext=""):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setText(error_message)
        msg.setInformativeText(infotext)
        msg.setWindowTitle(error_message)
        msg.exec_()

    def successful(self, error_message, infotext=""):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setText(error_message)
        msg.setInformativeText(infotext)
        msg.setWindowTitle(error_message)
        msg.exec_()

    def authenticate(self):

        context = self.context_switch.text()

        if context == 'Client':
            self.auth_client()

        elif context == 'Server':
            self.auth_server()

    def reconnect(self):

        context = self.context_switch.text()

        if context == 'Client':

            if self.resolvedb_connect == False:
                self.resolvedb_connect = True

                self.resolve_status.setText(f"")

                auth_db = DatabaseAuth(self)
                auth_result = auth_db.exec_()

                if auth_result:
                    self.db_name, self.db_user, self.db_pass = auth_db.get_output()

                    # Update timer
                    self.update_resolveview()
                    self.update_timer = QtCore.QTimer()
                    self.update_timer.timeout.connect(self.update_resolveview)
                    self.update_timer.start(30*1000)

        elif context == 'Server':
            auth_tcp = ServerAuthTCP(self)
            auth_tcp.exec_()

            if not auth_tcp.authenticated:
                return

            self.successful(f"Authenticated to {auth_tcp.UNAME}",
                f"Please specify the server config you want to append the Peer to")

            addto = FileDialog(forOpen=True, fmt='conf')

            with open(addto, 'r') as addto_file:
                conf = addto_file.read()

            conf +=(f"""\n[Peer]\n"""
                    f"""# User: {auth_tcp.UNAME} \n"""
                    f"""PublicKey = {auth_tcp.PKEYU} \n"""
                    f"""AllowedIPs = {auth_tcp.ASSIGN_IP}/32 \n""")

            self.df.loc[self.df['User']==auth_tcp.UNAME,
                                            'Public Key'] = auth_tcp.PKEYU

            with open(addto, 'w') as addto_file:
                addto_file.write(conf)

            self.successful(f"Added to File: {addto}")

    def auth_client(self):
        auth_request = ClientAuth(self)
        auth_request.setWindowTitle(self.context_action.text())
        auth_result = auth_request.exec_()
        auth_request = auth_request.get_output()

        if auth_result:

            if len(auth_request['S_IP'].split('.')) != 4:
                self.error("Invalid Server IP", "Check input and try again")
                return

            elif len(auth_request['S_PWD']) == 0:
                self.error("Invalid Server Password",
                            "Input string length zero")
                return

            elif len(auth_request['UNAME']) == 0:
                self.error("Invalid Username", "Input string length zero")
                return

            self.auth_request = auth_request

            # By this point, the input is a valid authentication request
            auth_tcp = ClientAuthTCP(self)
            auth_tcp.exec_()
            # output is the conf file

    def auth_server(self):
        auth_new = ServerAuth(self)
        auth_new.setWindowTitle(self.context_action.text())
        auth_result = auth_new.exec_()
        auth_new = auth_new.get_output()

        if auth_result:

            if len(auth_new['ASSIGN_IP'].split('.')) != 4:
                self.error("Invalid Assignment IP", "Check input and try again")
                return

            if (ipaddress.ip_address(auth_new['ASSIGN_IP'])
                            not in ipaddress.ip_network(self.subnet)):
                self.error("Invalid Assignment IP", f"IP must be on subnet {self.subnet}")
                return

            # TODO: Make dynamic "first" IP not string
            if ("9.0.0.1"==auth_new['ASSIGN_IP']):
                self.error("Invalid Assignment IP", f"IP is reserved for admin")
                return

            if (self.df['IP Assigned']==auth_new['ASSIGN_IP']).any():
                self.error("Invalid Assignment IP", f"IP is already assigned")
                return

            if len(auth_new['UNAME']) == 0:
                self.error("Invalid Username", "Check input and try again")
                return

            # By this point, the input is a valid authentication request
            self.df = self.df.append({
                            "User"         : auth_new['UNAME'],
                            "IP Assigned"  : auth_new['ASSIGN_IP'],
                            "Public Key"   : "",
                            "Last Seen IP" : ""},
                                    ignore_index=True)

            self.df.to_csv(Path("./server_database.csv"), index=False)

            self.successful(f"Created {auth_new['UNAME']}",
                            f"IP Assigned: {auth_new['ASSIGN_IP']}")

# ----------------------- PANDAS DATAFRAME TO PYQT

class pandasModel(QAbstractTableModel):

    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parnet=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None

# ----------------------- AUTHENTICATION PROMPTS AND FLOWS

class ClientAuth(QDialog):
    def __init__(self, parent = None):
        super(ClientAuth, self).__init__(parent)

        layout = QVBoxLayout(self)

        self.UNAME = QtWidgets.QLineEdit()
        self.UNAME.setPlaceholderText("Username")

        self.S_IP = QtWidgets.QLineEdit()
        self.S_IP.setPlaceholderText("Server IP")

        self.S_PWD = QtWidgets.QLineEdit()
        self.S_PWD.setPlaceholderText("Server Password")

        layout.addWidget(self.UNAME)
        layout.addWidget(self.S_IP)
        layout.addWidget(self.S_PWD)

        # OK and Cancel buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def get_output(self):

        self.auth_request = {
            "UNAME" : self.UNAME.text(),
            "S_IP" : self.S_IP.text(),
            "S_PWD" : self.S_PWD.text(),
        }

        return (self.auth_request)

class ClientAuthTCP(QDialog):
    def __init__(self, parent = None):
        super(ClientAuthTCP, self).__init__(parent)

        layout = QVBoxLayout(self)

        self.status = QtWidgets.QLabel()
        layout.addWidget(self.status)

        self.authenticate()

    def authenticate(self):

        client = self.parent()
        self.status.setText("Creating request")

        # ------------- INPUTS
        S_IP = client.auth_request['S_IP']
        UNAME = client.auth_request['UNAME']
        SPASS = passkey(client.auth_request['S_PWD'])

        # ------------- GENERATE KEYS
        pk = PrivateKey.generate()
        Pk = pk.public_key()

        # ------------- GENERATE PACKET
        MESSG = f"{SPASS.decode()},{Pk}"

        # ------------- COMMUNICATION
        S_PORT = client.auth_port

        # Authentication request
        encrypted = Fernet(passkey(UNAME)).encrypt(MESSG.encode())

        async def tcp_authenticate_request(loop):

            self.status.setText(f"Connecting to server {S_IP}:{S_PORT}")
            print(">>> Connecting to", S_IP, S_PORT)
            try:
                reader, writer = await asyncio.open_connection(S_IP, S_PORT,
                                                               loop=loop)
            except ConnectionRefusedError:
                self.status.setText(f"Connection to server {S_IP}:{S_PORT} refused")
                return

            except TimeoutError:
                self.status.setText(f"Connection to server {S_IP}:{S_PORT} timed out")
                return

            self.status.setText("Sent request")
            print('>>> Sent encrypted authentication request')
            writer.write(encrypted)

            auth_reply = await reader.read(1024)

            try:
                auth_reply = Fernet(SPASS).decrypt(auth_reply)
                auth_reply = auth_reply.decode()
                print(f">>> Received Authentication Reply: {auth_reply}")

                client.successful("Authenticated",
                        "Next: save your WireGuard Client configuration file")

                # TODO: Add IP_SUBNET
                PKEYS, IP_ASSIGNED = auth_reply.split(',')

                # Client config
                conf = (f"""[Interface]\n"""
                        f"""PrivateKey = {pk}\n"""
                        f"""Address = {IP_ASSIGNED}/32\n"""
                        f"""DNS = 1.1.1.1, 8.8.8.8\n\n"""
                        f"""[Peer]\n"""
                        f"""PublicKey = {PKEYS}\n"""
                        # TODO: Get subnet from server, set here
                        f"""AllowedIPs = {IP_SUBNET}\n"""
                        f"""Endpoint = {S_IP}:{client.wg_port}\n""")

                saveto = FileDialog(forOpen=False, fmt='conf')

                # TODO: Handle Cancel
                # TODO: Enable user to copy to clipboard instead

                with open(saveto, 'w') as save_conf:
                    save_conf.write(conf)

                self.status.setText(f"Saved file: {saveto}")

            except InvalidToken as e:
                print(f"... Received Authentication Error: {auth_reply.decode()}")
                self.status.setText(f"Authentication Error: {auth_reply.decode()}")
                pass

            writer.close()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(tcp_authenticate_request(loop))
        loop.close()

class ServerAuth(QDialog):
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

class ServerAuthTCP(QDialog):
    def __init__(self, parent = None):
        super(ServerAuthTCP, self).__init__(parent)

        layout = QVBoxLayout(self)

        self.status = QtWidgets.QLabel()
        layout.addWidget(self.status)

        self.authenticate()

    def authenticate(self):

        server = self.parent()
        subnet = server.subnet
        self.status.setText("Authenticating...")

        # ------------- INPUTS
        UNAMES = list(server.df['User'])
        SPASS = server.auth_key
        PKEYS = list(server.df['Public Key'][server.df['User'] == 'admin'])[0]

        # ------------- CONFIG
        S_IP = '0.0.0.0'
        S_PORT = server.auth_port

        # ------------- COMMUNICATION

        loop = asyncio.new_event_loop()
        authentication = loop.create_future()
        asyncio.set_event_loop(loop)

        async def handle_authentication(reader, writer):
            auth_request = await reader.read(1024)
            fail_cause = "UNKNOWN ERROR"

            for UNAME in UNAMES:

                key = passkey(UNAME)

                try:
                    message = Fernet(key).decrypt(auth_request)
                    message = message.decode()

                    addr = writer.get_extra_info('peername')
                    print(f">>> Received {message} from {addr}")

                    SPASS_CHECK, PKEYU = message.split(',')

                    if SPASS == SPASS_CHECK:
                        print("... Server password valid!")
                    else:
                        print('!!! Server password INVALID')
                        continue

                    UID = (server.df['User'] == UNAME)
                    ASSIGN_IP = server.df.loc[UID, 'IP Assigned'].values[0]

                    auth_reply = f"{PKEYS},{ASSIGN_IP}"
                    auth_reply = Fernet(SPASS).encrypt(auth_reply.encode())
                    writer.write(auth_reply)
                    await writer.drain()

                    self.PKEYU = PKEYU
                    self.UNAME = UNAME
                    self.ASSIGN_IP = ASSIGN_IP
                    print(f"... Authentication of {UNAME} complete!")
                    break

                except InvalidToken as e:
                    pass
            else:
                print(f">>> Invalid request message (could be UNAME or SPASS): {message}")
                writer.write("INVALID REQUEST".encode())

            writer.close()
            authentication.set_result(True)

        coro = asyncio.start_server(handle_authentication, S_IP, S_PORT, loop=loop)
        async_server = loop.run_until_complete(coro)

        # Serve requests until Ctrl+C is pressed
        print('... Serving on {}'.format(async_server.sockets[0].getsockname()))

        try:
            loop.run_until_complete(authentication)
        except KeyboardInterrupt:
            pass

        # Close the server
        async_server.close()
        loop.run_until_complete(async_server.wait_closed())
        loop.close()

        if hasattr(self, "PKEYU"):
            self.status.setText("Authenticated!")
            self.authenticated = True
        else:
            self.status.setText("Authention failed")
            self.authenticated = False


class PromptServerPassword(QDialog):
    def __init__(self, parent = None):
        super(PromptServerPassword, self).__init__(parent)

        layout = QVBoxLayout(self)

        self.S_PWD = QtWidgets.QLineEdit()
        self.S_PWD.setPlaceholderText("Server Password")

        self.PKEYS = QtWidgets.QLineEdit()
        self.PKEYS.setPlaceholderText("Public Key (optional)")

        layout.addWidget(self.S_PWD)
        layout.addWidget(self.PKEYS)

        # OK and Cancel buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def get_output(self):
        return self.S_PWD.text(), self.PKEYS.text()


class DatabaseAuth(QDialog):
    def __init__(self, parent = None):
        super(DatabaseAuth, self).__init__(parent)

        layout = QVBoxLayout(self)

        self.DB_NAME = QtWidgets.QLineEdit()
        self.DB_NAME.setPlaceholderText("Database Name")

        self.DB_USER = QtWidgets.QLineEdit()
        self.DB_USER.setPlaceholderText("Database Username")

        self.DB_PASS = QtWidgets.QLineEdit()
        self.DB_PASS.setPlaceholderText("Database Password")

        layout.addWidget(self.DB_NAME)
        layout.addWidget(self.DB_USER)
        layout.addWidget(self.DB_PASS)

        # OK and Cancel buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            Qt.Horizontal, self)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def get_output(self):
        return self.DB_NAME.text(),  self.DB_USER.text(), self.DB_PASS.text()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Window(app)
    w.show()
    sys.exit(app.exec_())
