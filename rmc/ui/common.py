from PyQt5 import QtWidgets, QtCore, QtGui
Qt = QtCore.Qt

# Give aliases to clean up code dramatically
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

QAbstractTableModel = QtCore.QAbstractTableModel

QPixmap = QtGui.QPixmap
QIcon = QtGui.QIcon

class UI_Panel(QFrame):
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

class UI_Common(QWidget):
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
                                }""")


class UI_User(QFrame):
    # Controller for a particular user
    def __init__(self, name, users):
        super().__init__()

        self.setSizePolicy(QSizePolicy.Maximum,
                            QSizePolicy.Maximum)
        self.lay = QVBoxLayout(self)
        users.lay.addWidget(self)

        self.icon = QLabel()
        if name == 'Server':
            icon = QPixmap('icons/database_50.png')
        else:
            icon = QPixmap('icons/user_50.png')
        # icon = icon.scaledToWidth(50, Qt.SmoothTransformation)
        self.icon.setPixmap(icon)

        self.name = QLabel("__"+name+"__")
        self.name.setTextFormat(Qt.MarkdownText)

        self.ping = QLabel("`0ms`")
        self.ping.setTextFormat(Qt.MarkdownText)

        self.lay.addWidget(self.ping, alignment=Qt.AlignCenter)
        self.lay.addWidget(self.icon, alignment=Qt.AlignCenter)
        self.lay.addWidget(self.name, alignment=Qt.AlignCenter)

    def set_ping(ping):
        self.ping.setText(str(ping))

class UI_Users(QFrame):
    def __init__(self, parent):
        super().__init__()

        # self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Minimum,
                            QSizePolicy.Minimum)

        self.lay = QHBoxLayout(self)
        parent.addWidget(self, alignment=Qt.AlignTop)

        self.add_user('Server')

    def add_user(self, name):
        self.lay.addWidget(UI_User(name, self))


class UI_Database(QFrame):
    # Controller for a particular database
    def __init__(self, name, db_list):
        super().__init__()

        self.setSizePolicy(QSizePolicy.Maximum,
                            QSizePolicy.Maximum)
        self.lay = QHBoxLayout(self)
        db_list.lay.addWidget(self)

        icon = QPixmap('icons/database_50.png')
        # icon = icon.scaledToWidth(50, Qt.SmoothTransformation)
        self.icon = QLabel()
        self.icon.setPixmap(icon)

        self.name = QLabel("__"+name+"__")
        self.name.setTextFormat(Qt.MarkdownText)

        self.lay.addWidget(self.icon, alignment=Qt.AlignCenter)
        self.lay.addWidget(self.name, alignment=Qt.AlignCenter)

    def set_ping(ping):
        self.ping.setText(str(ping))

class UI_Databases(QFrame):
    def __init__(self, parent):
        super().__init__()

        # self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Minimum,
                            QSizePolicy.Maximum)

        self.lay = QVBoxLayout(self)
        parent.addWidget(self, alignment=Qt.AlignTop)

        self.add_database('Database 1')

    def add_database(self, name):
        self.lay.addWidget(UI_Database(name, self))

# ----------------------- File Dialogs

def FileDialog(directory='', forOpen=True, fmt='', isFolder=False):
    """ Standard file selection dialog """
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
