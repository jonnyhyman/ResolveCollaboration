# package imports
from ui.common import *

import cryptography.hazmat.backends
default_backend = cryptography.hazmat.backends.default_backend

import cryptography.hazmat.primitives.kdf.pbkdf2
PBKDF2HMAC = cryptography.hazmat.primitives.kdf.pbkdf2.PBKDF2HMAC

import cryptography.fernet
Fernet = cryptography.fernet.Fernet
InvalidToken = cryptography.fernet.InvalidToken

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

# gui
class Client(UI_Common):

    subnet = None #'9.0.0.0/24'
    auth_port = None #4444 # TODO: Test on 51820 instead
    wg_port = None # 51820

    def __init__(self, app, parent=None):
        super().__init__(app, parent=parent)

        self.setWindowTitle("Resolve Mission Control Client")

        # Define buttons
        self.b_dbcon = QPushButton("⇄")
        self.p_LU.lay.addWidget(self.b_dbcon)
        self.b_dbcon.setObjectName("b_dbcon")
        self.b_dbcon.setStyleSheet("""QPushButton#b_dbcon {
                                    color: #848484;
                                    background: transparent;
                                    }
                                    QPushButton#b_dbcon::hover{
                                    	color: white;
                                    }
                                    QPushButton#b_dbcon::pressed{
                                    	color: #848484;
                                    }""")


        self.b_setup = QPushButton("Setup")
        self.b_tunn = QPushButton("Activate Tunnel")
        self.b_sync = QPushButton("Sync Status")

        for b in [self.b_setup, self.b_tunn, self.b_sync]:
            self.p_RU.lay.addWidget(b)

        # TODO: Implement
        self.b_tunn.setEnabled(False)
        self.b_sync.setEnabled(False)

        # TESTING
        self.users.add_user('Jonny')
        self.users.add_user('Mel')
        self.users.add_user('David')
        self.users.add_user('Hendrick')
        self.users.add_user('Mom')
        self.users.add_user('Dad')

        # Resolve database views
        self.resolvedb_connect = False

        # People
        # self.label = QLabel("### People")
        # self.label.setTextFormat(Qt.MarkdownText)
        # self.p_RB.lay.addWidget(self.label)
        #
        # people = self.resolvedb_users()
        # model = pandasModel(people)
        # self.people_view = QTableView()
        # self.people_view.setModel(model)
        # self.p_RB.lay.addWidget(self.people_view)

        # Projects
        self.label = QLabel("### Projects")
        self.label.setTextFormat(Qt.MarkdownText)
        self.p_RB.lay.addWidget(self.label, alignment=Qt.AlignHCenter)

        # model = pandasModel(self.resolvedb_projects(people))
        # self.projects_view = QTableView()
        # self.projects_view.setModel(model)
        # self.p_RB.lay.addWidget(self.projects_view)

        # self.people_view.horizontalHeader().setSectionResizeMode(
        #                                         QtWidgets.QHeaderView.Stretch)
        # self.projects_view.horizontalHeader().setSectionResizeMode(
        #                                         QtWidgets.QHeaderView.Stretch)

        self.message = QLabel("Not connected to Resolve")
        self.message.setTextFormat(Qt.MarkdownText)
        self.p_RB.lay.addWidget(self.message, alignment=Qt.AlignBottom)

        # BUTTON CONNECT
        self.setup_window = ClientSetup(self)
        self.b_setup.clicked.connect(self.setup_window.show)

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

    def reconnect(self):
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

    def auth_client(self):
        auth_request = ClientAuth(self)
        auth_request.setWindowTitle("Authenticate")
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
            # Output is the config file

class ClientSetup(QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent=parent)
        self.client = client
        self.setWindowTitle("Client Setup")

        self.lay = QGridLayout(self)

        # self.setFrameShape(QtWidgets.QFrame.Panel)
        self.setObjectName("ClientSetup")

        stylesheet  = """QWidget#ClientSetup {"""
        stylesheet += f"""background-color: #28282E;"""
        stylesheet += """}"""
        stylesheet += """QLabel { color: white; }"""

        self.setStyleSheet(stylesheet)
        self.b_setup = {}

        b = self.add_step("Authenticate", 'icons/database_secured.png', 0,0)
        b.clicked.connect(self.client.auth_client)

        self.add_arrow(0,1)
        b = self.add_step("Connect to Tunnel", 'icons/user_secured.png', 0,2)
        

        self.add_arrow(0,3)
        b = self.add_step("Connect to Database", 'icons/database_secured.png', 0,4)

    def add_step(self, label_text, icon, i, j):

        slay = QHBoxLayout()
        icon = QPixmap(icon)

        key = label_text.lower()

        self.b_setup[key] = QPushButton(label_text)
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
        self.lay.addWidget(self.b_setup[key], i,j)

        return self.b_setup[key]

    def add_arrow(self, i,j):
        arrow = QLabel("→")
        arrow.setObjectName("arrow")
        arrow.setStyleSheet("""QPushButton#b_dbcon {
                                    color: #848484;
                                    background: transparent;
                                    }
                                    QPushButton#b_dbcon::hover{
                                    	color: white;
                                    }
                                    QPushButton#b_dbcon::pressed{
                                    	color: #848484;
                                    }""")
        self.lay.addWidget(arrow, i,j)

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

    w = Client(app)
    w.show()

    if len(sys.argv[1]) > 1 and sys.argv[1] == 'setup':
        w.setup_window.show()

    sys.exit(app.exec_())
