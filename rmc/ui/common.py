from PyQt5 import QtWidgets, QtCore, QtGui
from pathlib import Path
import pickle
import psycopg2
from ipaddress import ip_address, ip_network

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
                self.database_connect(db=db)

    def closeEvent(self, event):
        """Close window"""

        # Helpful eventually maybe:
        # quit_msg = "Are you sure you want to exit the program?"
        # reply = QtWidgets.QMessageBox.question(self, 'Message',
        #                  quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        #
        # if reply == QtWidgets.QMessageBox.Yes:
        #     event.accept()
        # else:
        #     event.ignore()

        for db in self.dbses.databases:
            db.disconnect()

    def database_connect(self, db=None):
        """ Create/retrieve database connection """

        # retrieving from saved
        if db:
            connection = self.dbses.add_database(db, connect=False)
            return connection

        # creating new
        auth_db = DatabaseAuth(self)
        auth_result = auth_db.exec_()

        if auth_result:
            db_name, db_host, db_user, db_pass = auth_db.get_output()

            # catch user errors

            try:
                ip_address(db_host)
            except ValueError as e:
                UI_Error(self,"Invalid Database IP", str(e))
                self.database_connect()
                return

            if len(db_pass) == 0:
                UI_Error(self,"Invalid Server Password",
                            "Input length zero")
                self.database_connect()
                return

            elif len(db_user) == 0:
                UI_Error(self,"Invalid Server Password",
                            "Input length zero")
                self.database_connect()
                return

            elif len(db_name) == 0:
                UI_Error(self,"Invalid Server Password",
                            "Input length zero")
                self.database_connect()
                return

            # open handle to database

            db = {
                        'host' : db_host,
                        'user' : db_user,
                        'name' : db_name,
                        'pass' : db_pass,
            }

            connection = self.dbses.add_database(db, connect=True)

            if connection:
                self.message.setText(f"_Added database_ {db_name}")
                self.config['dbses'].append(db)
                self.config.save()


class UI_User(QFrame):
    """ Controller for a particular user in the users view """

    def __init__(self, user, users):
        super().__init__()

        self.setSizePolicy(QSizePolicy.Maximum,
                            QSizePolicy.Maximum)
        self.lay = QVBoxLayout(self)
        users.lay.addWidget(self)

        self.icon = QLabel()
        if user['name'] == 'Server':
            icon = QPixmap('icons/database_50.png')
        else:
            icon = QPixmap('icons/user_50.png')

        # icon = icon.scaledToWidth(50, Qt.SmoothTransformation)
        self.icon.setPixmap(icon)

        self.name = QLabel("__"+user['name']+"__")
        self.name.setTextFormat(Qt.MarkdownText)

        self.ping = QLabel("`-- ms`")
        self.ping.setTextFormat(Qt.MarkdownText)

        self.ip = QLabel(f"`{user['ip']}`")
        self.ip.setTextFormat(Qt.MarkdownText)

        self.lay.addWidget(self.ping, alignment=Qt.AlignCenter)
        self.lay.addWidget(self.icon, alignment=Qt.AlignCenter)
        self.lay.addWidget(self.name, alignment=Qt.AlignCenter)
        self.lay.addWidget(self.ip, alignment=Qt.AlignCenter)

    def set_ping(ping):
        self.ping.setText("`"+str(ping)+"ms`")

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

        # Remove all
        for i in reversed(range(self.lay.count())):
            self.lay.itemAt(i).widget().setParent(None)

        for user in userlist:
            self.lay.addWidget(UI_User(user, self))

class UI_Database(QFrame):
    """ Controller for a particular database in the database list """

    def __init__(self, db, db_list=None, connect=False):
        super().__init__()

        self.setSizePolicy(QSizePolicy.Maximum,
                            QSizePolicy.Maximum)
        self.lay = QHBoxLayout(self)
        db_list.lay.addWidget(self)

        icon = QPixmap('icons/database_50.png')
        icon = icon.scaledToWidth(50, Qt.SmoothTransformation)
        self.select = QPushButton()
        self.select.setCheckable(False)
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
        self.select.clicked.connect(lambda: self.connect(db))

        self.name = QLabel("__"+db['name']+"__")
        self.name.setTextFormat(Qt.MarkdownText)

        self.host = QLabel(db['host'])
        self.host.setTextFormat(Qt.MarkdownText)

        self.status = QLabel("_Disconnected_")
        self.status.setTextFormat(Qt.MarkdownText)

        details = QVBoxLayout()
        details.addWidget(self.name, alignment=Qt.AlignLeft)
        details.addWidget(self.host, alignment=Qt.AlignLeft)
        details.addWidget(self.status, alignment=Qt.AlignLeft)
        details.setSpacing(0)

        self.lay.addWidget(self.select, alignment=Qt.AlignCenter)
        self.lay.addLayout(details)

        self.connection = None

        if connect:
            success = self.connect(db)

            if not success:
                db_list.lay.removeWidget(self)
                del self

        # make exportable resolve xml file

    def connect(self, db):
        try:
            self.connection = psycopg2.connect(
                                  host    =  db['host'],
                                  user    =  db['user'],
                                  database=  db['name'],
                                  password=  db['pass'],
                                  port    = "5432",
                                  connect_timeout=1,
                                )

            self.status.setText("""<span style="color:Aqua">*Connected*</span>""")
            # self.parent().enable(self)
            self.select.setChecked(True)

        except psycopg2.OperationalError as e:
            UI_Error(self,"Database Error", e)
            return False

        return True

    def disconnect(self):

        if self.connection:
            print(f"... Closing {self.name.text()}")
            self.connection.close()

    def set_ping(ping):
        self.ping.setText(str(ping))

class UI_Databases(QFrame):
    """ Databases list """

    def __init__(self, parent):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Minimum,
                            QSizePolicy.Maximum)

        self.lay = QVBoxLayout(self)
        parent.addWidget(self, alignment=Qt.AlignTop)

        self.databases = []

    def add_database(self, db, connect=False):
        db = UI_Database(db, db_list=self, connect=connect)
        self.databases.append(db)
        return db.connection

    def select_database(self, db):
        pass

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
        layout.addWidget(self.DB_USER)
        layout.addWidget(self.DB_NAME)
        layout.addWidget(self.DB_PASS)

        # OK and Cancel buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            Qt.Horizontal, self)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def get_output(self):
        return (self.DB_NAME.text(),
                self.DB_IP.text(),
                self.DB_USER.text(),
                self.DB_PASS.text())

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

# ----------------------- Configuration handler
class Config:
    """ Configuration file handler class.
        Saves config details to pickled bytes.

        If peak security is required, we could encrypt the bytes of the config
        file (because it holds the server password hash)
    """

    default = {
                'auth' : {},
                'dbses': [],
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
