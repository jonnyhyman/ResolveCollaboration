from PyQt5 import QtWidgets, QtCore, QtGui
from pathlib import Path
import pickle
import psycopg2
import psycopg2.extras
from ipaddress import ip_address, ip_network

from util.networking import ping_many, get_pings

Qt = QtCore.Qt

# Give aliases to clean up code dramatically
# QApplication
QApplication = QtWidgets.QApplication
QPushButton = QtWidgets.QPushButton
QLabel = QtWidgets.QLabel
QSizePolicy = QtWidgets.QSizePolicy
QSlider = QtWidgets.QSlider
QSpacerItem = QtWidgets.QSpacerItem
QVBoxLayout = QtWidgets.QVBoxLayout
QHBoxLayout = QtWidgets.QHBoxLayout
QGridLayout = QtWidgets.QGridLayout
QWidget = QtWidgets.QWidget
QDialog = QtWidgets.QDialog
QMessageBox = QtWidgets.QMessageBox
QFrame = QtWidgets.QFrame
QFileDialog = QtWidgets.QFileDialog
QDialog = QtWidgets.QDialog
QApplication = QtWidgets.QApplication
QTableView = QtWidgets.QTableView

# QtCore
QAbstractTableModel = QtCore.QAbstractTableModel
QTimer = QtCore.QTimer

# Qt Gui
QPixmap = QtGui.QPixmap
QIcon = QtGui.QIcon

# Pyinstaller pathfinding
from pathlib import Path

def link(relpath):
    bundle_dir = Path(__file__).parent
    absolute = str((Path.cwd() / bundle_dir / relpath).absolute())
    # print(">>> LINK >>>", absolute)
    # print("...", bundle_dir)
    # print("...", relpath)
    return absolute

class UI_Panel(QFrame):
    """ Panel frame with borders and Resolve-like styling """
    def __init__(self, layout, parent, borders = "all", bg="#212126"):
        super().__init__()

        self.setFrameShape(QtWidgets.QFrame.Panel)

        if layout == 'g':
            self.lay = QGridLayout(self)
        elif layout == 'v':
            self.lay = QVBoxLayout(self)
            self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        elif layout == 'h':
            self.lay = QHBoxLayout(self)
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        parent.addWidget(self)

        self.setObjectName("UI_Panel")

        stylesheet  = """QFrame#UI_Panel {"""
        stylesheet += f"""background: {bg};"""

        if borders == 'all':
            borders = 'left-right-bottom-top'

        # All start invisible
        for wall in ("left-right-bottom-top").split('-'):
            stylesheet += (f"""border-{wall}: 0px solid transparent;""")

        # Override
        if borders != '':

            for wall in borders.split('-'):
                stylesheet += (f"""border-{wall}: 1px solid #0A0A0A;""")

        stylesheet += "}"

        self.setStyleSheet(stylesheet)

class UI_Dialog(QDialog):
    """ Dialog window """
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("UI_Dialog")

        stylesheet  = """QDialog#UI_Dialog {"""
        stylesheet += f"""background-color: #28282E;"""
        stylesheet += """}"""
        stylesheet += """QLabel { color: white; }"""

        self.setStyleSheet(stylesheet)

class UI_Common(QWidget):
    """ Main window for Resolve Mission Control, common between server/client"""
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self.app = app

        print(">>> Here is:", Path(".").absolute())

        self.lay0 = QHBoxLayout(self)
        self.lay0.setSpacing(0)
        self.lay0.setContentsMargins(0,0,0,0)

        # Left pane
        self.layL = QVBoxLayout(); self.lay0.addLayout(self.layL)
        self.layR = QVBoxLayout(); self.lay0.addLayout(self.layR)
        self.layL.setSpacing(0)
        self.layR.setSpacing(0)

        # LU : Left upper, LB : Left bottom (etc...)
        self.p_LU = UI_Panel('h', parent=self.layL, borders='right-bottom')
        self.p_LB = UI_Panel('v', parent=self.layL, borders='right', bg="#28282E")
        self.p_RU = UI_Panel('h', parent=self.layR, borders='bottom')
        self.p_RB = UI_Panel('v', parent=self.layR, borders='')

        # Size policies
        self.p_LU.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.users = UI_Users(parent=self.p_RB.lay)
        self.dbses = UI_Databases(parent=self.p_LB.lay)

        # Styless
        self.setStyleSheet("""QLabel {
                                    color: white;
                                }
                            QMessageBox {
                                    background-color: #28282E;
                                    color: white;
                                }
                                """)

        self.config = Config(self)

        # Recreate database list
        if self.config['dbses'] != []:
            for db in self.config['dbses']:
                self.dbses.add_database(db)

    def closeEvent(self, event):
        """Close window"""

        for db, ui_db in self.dbses.ui_dbses.items():
            if ui_db.connection:
                ui_db.disconnect()

        self.app.closeAllWindows()

    def database_connect(self):
        """ Create a new database connection """

        # Creating a new connection
        auth_db = DatabaseAuth(self)
        auth_result = auth_db.exec_()

        if auth_result:
            db = auth_db.get_output()

            # catch user errors

            try:
                ip_address(db['host'])
            except ValueError as e:
                UI_Error(self,"Invalid Database IP", str(e))
                self.database_connect()
                return

            if len(db['name']) == 0:
                UI_Error(self,"Invalid Database Name",
                            "Input length zero")
                self.database_connect()
                return

            elif len(db['pass']) == 0:
                UI_Error(self,"Invalid Server Password",
                            "Input length zero")
                self.database_connect()
                return

            elif len(db['user']) == 0:
                UI_Error(self,"Invalid Server Username",
                            "Input length zero")
                self.database_connect()
                return

            # open handle to database
            connection = self.dbses.add_database(db, select=True)

            if connection:
                # If connection was successful, add to configuration
                self.message.setText(f"_Added database_ {db['name']}")
                self.config['dbses'].append(db)
                self.config.save()

                return True
            else:
                self.database_remove(self.dbses.ui_dbses[db['name']])
                self.database_connect()

        return False

    def database_remove(self, ui_db_to_remove):
        """ Remove a created database connection """

        # remove it from the layout list
        self.dbses.lay.removeWidget(ui_db_to_remove)

        # remove it from the gui
        ui_db_to_remove.setParent(None)

        # remove it from the ui_dbses dict
        del self.dbses.ui_dbses[ui_db_to_remove.db_details['name']]

        # remove it from the config
        if ui_db_to_remove.db_details in self.config['dbses']:
            self.config['dbses'].remove(ui_db_to_remove.db_details)
            self.config.save()


class UI_User(QFrame):
    """ Controller for a particular user in the users view """

    def __init__(self, user, users):
        super().__init__()

        self.setSizePolicy(QSizePolicy.Maximum,
                            QSizePolicy.Maximum)
        self.lay = QVBoxLayout(self)
        users.lay.addWidget(self)

        # reference back to main ui class
        self.ui_main = users.parent().parent()
        self.user_details = user

        scaled = lambda i: i.scaledToWidth(100, Qt.SmoothTransformation)
        self.icon = QLabel()
        if user['name'] == 'Server':
            # The Server cannot be disconnected, because... you're running it.
            #  so both images are of a connected database
            self.icon_disc = scaled(QPixmap(link('ui/icons/database.png')))
            self.icon_conn = scaled(QPixmap(link('ui/icons/database.png')))
        else:
            self.icon_disc = scaled(QPixmap(link('ui/icons/user_disconnected.png')))
            self.icon_conn = scaled(QPixmap(link('ui/icons/user.png')))
        self.icon.setPixmap(self.icon_disc)

        if user['name'] != "Server":
            self.remove = QPushButton("×")
            self.remove.setObjectName("b_remove")
            self.remove.setToolTip(f"Remove {user['name']} from the user list")
            self.remove.setSizePolicy(QSizePolicy.Minimum,
                                        QSizePolicy.Minimum)

            self.remove.setStyleSheet("""QPushButton#b_remove {
                                        color: #848484;
                                        border: 1px solid transparent;
                                        background: transparent;
                                        }
                                        QPushButton#b_remove::hover{
                                            color: white;
                                        }
                                        QPushButton#b_remove::pressed{
                                            color: #848484;
                                        }""")


            self.remove.clicked.connect(
                lambda: self.ui_main.remove_user(user['name'])
            )

        self.name = QLabel("__"+user['name']+"__")
        self.name.setTextFormat(Qt.MarkdownText)

        self.ping = QLabel("`-- ms`")
        self.ping.setTextFormat(Qt.MarkdownText)

        self.ip = QLabel(f"`{user['ip']}`")
        self.ip.setTextFormat(Qt.MarkdownText)

        self.proj = QLabel("")
        self.proj.setTextFormat(Qt.MarkdownText)
        self.proj.setText(self.get_project(user))

        if user['name'] != "Server":
            self.lay.addWidget(self.remove, alignment=Qt.AlignCenter)

        self.lay.addWidget(self.icon, alignment=Qt.AlignCenter)
        self.lay.addWidget(self.name, alignment=Qt.AlignCenter)
        self.lay.addWidget(self.ip, alignment=Qt.AlignCenter)
        self.lay.addWidget(self.ping, alignment=Qt.AlignCenter)
        self.lay.addWidget(self.proj, alignment=Qt.AlignCenter)

    def set_ping(self, ping):

        if '--' not in ping:
            ping = f'<span style="color:Aqua"><code>{ping}</code></span>'
        else:
            ping = (f"`{ping}`")

        self.ping.setText(ping)

        # Update icon

        if ping in ['``', '`-- ms`']:
            self.icon.setPixmap(self.icon_disc)

        else:
            self.icon.setPixmap(self.icon_conn)

        # while we're at it...
        self.proj.setText(self.get_project(self.user_details))

    def get_project(self, user):
        """ Determine what project this user is in, if at all! """

        # Get connection from UI
        ui_db = self.ui_main.dbses.selected(fail_queitly=True)

        if ui_db == None:
            # if there is no database selected
            return ""

        if ui_db.connection == None:
            return ""

        connection = ui_db.connection

        sysid_columns = ['SysId','Name','LastSeen','ClientAddr','UserDefinedClientName']
        sql = f'''SELECT "{'","'.join(sysid_columns)}" FROM public."Sm2SysIdEntry" '''

        try:
            crs = connection.cursor(cursor_factory = psycopg2.extras.NamedTupleCursor)
            crs.execute(sql) # this command can cause the exceptions

        except psycopg2.OperationalError as e:
            # Can occur if restart happens
            print(f">>> Error getting projects, database restarted? : {e}")
            return

        except psycopg2.InterfaceError as e:
            # Can happen after a restart, connection has been severed
            # try to reconnect:
            success = ui_db.connect()
            return # just quit, we'll check next time timer calls this

        sysids = crs.fetchall()

        project_columns = ['ProjectName', 'IsLiveCollaborationEnabled', 'SysIds', 'SM_Project_id']
        sql = f'''SELECT "{'","'.join(project_columns)}" FROM public."SM_Project" '''

        crs = connection.cursor(cursor_factory = psycopg2.extras.NamedTupleCursor)
        crs.execute(sql)
        projects = crs.fetchall()


        if len(sysids) == 0:
            # if there are no users in database this won't work...
            return

        user_ip = user['ip']

        if user['name'] == 'Server':
            # remap to home address if looking at server user
            #  because resolve reports the home address, not first_ip
            user_ip = '127.0.0.1'

        # get sysid of user with user_ip
        for select in sysids:

            if user_ip == select.ClientAddr:
                # carry to after the loop
                user_sysid = select.SysId
                break

        else:
            # print(f">>> User with ip {user_ip} was not found in Resolve database")
            return ""

        for project in projects:

            if project.SysIds is not None:
                # Someone's in there!
                user_ids = project.SysIds.split(',')

                # Map to user

                for sysid in user_ids:

                    if user_sysid == sysid:

                        # print(f">>> {user['name']} is in {project.ProjectName}")

                        formatted = f"Working on\n__{project.ProjectName}__"

                        return formatted

        # Not found in any project
        return ""


class UI_Users(QFrame):
    """ List of users """

    def __init__(self, parent):
        super().__init__()

        # self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Minimum,
                            QSizePolicy.Minimum)

        self.lay = QHBoxLayout(self)
        parent.addWidget(self, alignment=Qt.AlignTop)

    def update(self, userlist):
        """ Update the userlist """

        # Remove all
        for i in reversed(range(self.lay.count())):
            to_remove = self.lay.itemAt(i).widget()
            # remove it from the layout list
            self.lay.removeWidget(to_remove)
            # remove it from the gui
            to_remove.setParent(None)

        # Add 'em back in
        for user in userlist:
            self.lay.addWidget(UI_User(user, self))
            self.ping_users(only_set=True)

        if not hasattr(self,'ping_timer'):

            # If just loaded up
            self.ping_timer = QTimer(self)
            self.ping_timer.timeout.connect(self.ping_users)
            self.ping_timer.start(4000)

    def ping_users(self, only_set = False):
        """ Ping users in the userview, and update from last pings
        """

        # Update from last
        if hasattr(self,'pings'):
            pings = get_pings(self.pings)

            # update userview
            # print('... ...',pings['returns'])
            self.set_pings(pings)

        if not only_set:

            # Go get new ones
            self.pings = ping_many(self.get_ips())
            # print('...', self.pings)

    def get_ips(self):
        ips = {}

        for i in range(self.lay.count()):
            ip = self.lay.itemAt(i).widget().ip.text()[1:-1]

            if ip != "":
                ips[i] = ip

        return ips

    def set_pings(self, pings):

        n = 0
        for i in range(self.lay.count()):
            item = self.lay.itemAt(i).widget()
            ip = item.ip.text()[1:-1]

            if ip != "" and len(pings['returns']) > i:
                # If list length has changed, it's not guaranteed it'll work yet
                # print('... set >>>', i, n, pings['returns'][n])
                item.set_ping(str(pings['returns'][n]))
                n += 1


class UI_Database(QFrame):
    """ Controller for a particular database in the database list """

    def __init__(self, db_details, db_list=None):
        super().__init__()

        self.db_list = db_list

        self.setSizePolicy(QSizePolicy.Maximum,
                            QSizePolicy.Maximum)
        self.lay = QHBoxLayout(self)
        self.db_list.lay.addWidget(self)

        self.remove = QPushButton("×")
        self.remove.setObjectName("b_remove")
        self.remove.setSizePolicy(QSizePolicy.Minimum,
                                    QSizePolicy.Minimum)
        self.remove.setStyleSheet("""QPushButton#b_remove {
                                    color: #848484;
                                    border: 1px solid transparent;
                                    background: transparent;
                                    }
                                    QPushButton#b_remove::hover{
                                        color: white;
                                    }
                                    QPushButton#b_remove::pressed{
                                        color: #848484;
                                    }""")

        ui_main = self.db_list.parent().parent()
        self.remove.clicked.connect(lambda: ui_main.database_remove(self))

        icon = QPixmap(link('ui/icons/database_50.png'))
        icon = icon.scaledToWidth(50, Qt.SmoothTransformation)
        self.select = QPushButton()
        self.select.setCheckable(True)
        self.select.setChecked(False)
        self.select.setObjectName("select")
        self.select.setStyleSheet(
            """QPushButton#select {
                background: transparent;
            }
            QPushButton#select::hover{
            	background: rgba(1,1,1,.5);
            }
            QPushButton#select::checked{
                border: 1px solid aqua;
            	background: transparent;
            }
            QPushButton#select::pressed{
            	background: rgba(0,0,0,1);
            }""")
        self.select.setIcon(QIcon(icon))
        self.select.setIconSize(icon.rect().size())
        self.select.clicked.connect(self.selected)

        self.name = QLabel("__"+db_details['name']+"__")
        self.name.setTextFormat(Qt.MarkdownText)

        self.host = QLabel(db_details['host'])
        self.host.setTextFormat(Qt.MarkdownText)

        self.status = QLabel("_Disconnected_")
        self.status.setTextFormat(Qt.MarkdownText)

        details = QVBoxLayout()
        details.addWidget(self.name, alignment=Qt.AlignLeft)
        details.addWidget(self.host, alignment=Qt.AlignLeft)
        details.addWidget(self.status, alignment=Qt.AlignLeft)
        details.setSpacing(0)

        self.lay.addWidget(self.remove, alignment=Qt.AlignCenter)
        self.lay.addWidget(self.select, alignment=Qt.AlignCenter)
        self.lay.addLayout(details)

        self.connection = None
        self.db_details = db_details

    def selected(self):
        self.db_list.select(self.db_details)

    def connect(self, fail_queitly=False):

        try:
            # these details ultimately come straight from
            #  the config.rmc file, or from a UI Dialog
            self.connection = psycopg2.connect(

                                  host     =  self.db_details['host'],
                                  user     =  self.db_details['user'],
                                  database =  self.db_details['name'],
                                  password =  self.db_details['pass'],

                                  port    = "5432",
                                  connect_timeout=10,
                                )

            self.status.setText("""<span style="color:Aqua">*Connected*</span>""")
            print(f"... Opened {self.db_details['name']}")
            self.select.setChecked(True)

        except psycopg2.OperationalError as e:

            if not fail_queitly:
                UI_Error(self,"Database Error", e)

            return False

        return True

    def disconnect(self):

        if self.connection:
            self.connection.close()
            self.select.setChecked(False)
            self.status.setText("""_Disconnected_""")
            print(f"... Closed {self.db_details['name']}")

    def export(self):
        xml = (f"""<?xml version="1.0" encoding="UTF-8"?>
<DBAccessKey>
  <hostIPAddress>{self.db_details['host']}</hostIPAddress>
  <dbName>{self.db_details['name']}</dbName>
  <dbUsername>{self.db_details['user']}</dbUsername>
  <dbPassword>{self.db_details['pass']}</dbPassword>
</DBAccessKey>
        """)

        # Save config to conf file
        saveto = FileDialog(forOpen=False, fmt='resolvedbkey',
                            title="Save Resolve Database Access Key")

        if saveto:

            with open(saveto, 'w') as save:
                save.write(xml)

class UI_Databases(QFrame):
    """ List of Databases """

    def __init__(self, parent):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Minimum,
                            QSizePolicy.Maximum)

        self.lay = QVBoxLayout(self)
        parent.addWidget(self, alignment=Qt.AlignTop)

        self.ui_dbses = {}

    def add_database(self, db_details, select=False):
        """ Add database connection to list
                - db is a dict containing database login details
                - Called from button-click (select=True)
                - Called from retrieving saved details (select=False)
        """

        ui_db = UI_Database(db_details, db_list=self)

        # add ui object to databases dict
        self.ui_dbses[db_details['name']] = ui_db

        if select:
            self.select(db_details)

        return ui_db.connection

    def select(self, this_db, fail_queitly=False):
        """ Select this db! (called from button click on a database)
            - this_db is a dict containing database login details
        """

        for db_name, ui_db in self.ui_dbses.items():
            if db_name == this_db['name']:
                ui_db.connect(fail_queitly=fail_queitly)
            else:
                ui_db.disconnect()

    def selected(self, fail_queitly=False):
        """ Returns which database is currently selected. Error if none """
        for db_name, ui_db in self.ui_dbses.items():

            if ui_db.select.isChecked():
                return ui_db
        else:
            if fail_queitly:
                return None
            else:
                UI_Error(self, "Selection error", "Please select a database")


    def export_selected(self):
        """ Initiate database connection export of the selected database """
        self.selected().export()


class DatabaseAuth(UI_Dialog):

    """ Form for database connections """

    def __init__(self, parent = None):
        super(DatabaseAuth, self).__init__(parent)

        layout = QVBoxLayout(self)

        self.DB_NAME = QtWidgets.QLineEdit()
        self.DB_NAME.setPlaceholderText("Database Name")

        self.DB_IP = QtWidgets.QLineEdit()
        self.DB_IP.setPlaceholderText("Database IP")

        self.DB_USER = QtWidgets.QLineEdit()
        self.DB_USER.setPlaceholderText("Database Username")

        self.DB_PASS = QtWidgets.QLineEdit()
        self.DB_PASS.setPlaceholderText("Database Password")
        self.DB_PASS.setEchoMode(QtWidgets.QLineEdit.Password)

        layout.addWidget(self.DB_IP)
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
        db = {
                    'host' : self.DB_IP.text(),
                    'name' : self.DB_NAME.text(),
                    'user' : self.DB_USER.text(),
                    'pass' : self.DB_PASS.text()
        }
        return db

# ----------------------- UI functions

def UI_Error(parent, error_message, infotext=""):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Critical)
    msg.setText(str(error_message))
    msg.setInformativeText(str(infotext))
    msg.setWindowTitle(str(error_message))
    msg.exec_()

def UI_Successful(parent, error_message, infotext=""):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Information)
    msg.setText(str(error_message))
    msg.setInformativeText(str(infotext))
    msg.setWindowTitle(str(error_message))
    msg.exec_()

def FileDialog(directory='', forOpen=True, fmt='', isFolder=False, title="Open File"):
    """ Standard file selection dialog """
    # options = QFileDialog.Options()
    # options |= QFileDialog.DontUseNativeDialog
    # options |= QFileDialog.DontUseCustomDirectoryIcons
    dialog = QFileDialog()
    dialog.setWindowTitle(title)
    # dialog.setOptions(options)

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

# ----------------------- PANDAS DATAFRAME TO PYQT
#
# class pandasModel(QAbstractTableModel):
#
#     def __init__(self, data):
#         QAbstractTableModel.__init__(self)
#         self._data = data
#
#     def rowCount(self, parent=None):
#         return self._data.shape[0]
#
#     def columnCount(self, parnet=None):
#         return self._data.shape[1]
#
#     def data(self, index, role=Qt.DisplayRole):
#         if index.isValid():
#             if role == Qt.DisplayRole:
#                 return str(self._data.iloc[index.row(), index.column()])
#         return None
#
#     def headerData(self, col, orientation, role):
#         if orientation == Qt.Horizontal and role == Qt.DisplayRole:
#             return self._data.columns[col]
#         return None

# ----------------------- Configuration handler
class Config:
    """ Configuration file handler class.
        Saves config details to pickled bytes.

        If peak security is required, we could encrypt the bytes of the config
        file (because it holds the server password hash)
    """

    default = {
                'version' : '0.0.2',
                'auth' : {},
                'dbses': [],
                'userlist':[{
                                "name"  : "Server",
                                "Pk"    : "",
                                "ip"    : "",
                            }],
    }

    def __init__(self, parent):

        saveto = Path(QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppConfigLocation))
        saveto = saveto.parent / Path("Resolve Mission Control")

        if not saveto.exists():
            saveto.mkdir()

        self.saveto = saveto
        if parent.context == 'client':
            self.fileto = self.saveto / Path("clientconfig.rmc")
        elif parent.context == 'server':
            self.fileto = self.saveto / Path("serverconfig.rmc")
        else:
            raise(ValueError(f"{parent.context} is not a valid context"))
        print(">>>",self.fileto)
        self.config = self.load()

    def __getitem__(self, key):
        """ makes config act like a dict itself to prevent config.config[key] madness """
        return self.config[key]

    def __setitem__(self, key, new_value):
        """ makes config act like a dict itself to prevent config.config[key]=value madness """
        self.config[key] = new_value

    def load(self):

        if not self.fileto.exists():
            return self.default

        try:
            with open(self.fileto, 'rb') as file:
                config = pickle.load(file)
        except EOFError:
            config = self.default

        return config

    def save(self):

        with open(self.fileto, 'wb') as file:
            pickle.dump(self.config, file)

    def reset(self, areyousure=False):
        if areyousure and self.fileto.exists():
            self.fileto.unlink()
            print(f">>> DELETED {self.fileto}")
