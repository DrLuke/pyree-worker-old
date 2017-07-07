from PyQt5.QtWidgets import QMainWindow, QApplication, QListWidgetItem, QFileDialog, QDockWidget
from PyQt5.QtCore import Qt, QMimeData, QMimeType, QTimer, QPointF
from PyQt5.QtGui import QIcon
from bodgegui import Ui_MainWindow

import sys
from uuid import uuid4
import os
from glob import glob
import json

import socket
from select import select


class ProgramData:
    def __init__(self):
        self.command = {}
        self.command["type"] = "program"
        self.command["id"] = int(uuid4())
        self.command["A"] = ""
        self.command["B"] = ""
        self.command["C"] = ""
        self.command["D"] = ""
        self.command["delete"] = False

class TextureData:
    def __init__(self):
        self.command = {}
        self.command["type"] = "texutre"
        self.command["id"] = int(uuid4())
        self.command["path"] = ""
        self.command["start"] = 1
        self.command["length"] = 1
        self.command["texbank"] = 0
        self.command["delete"] = False

class BodgeMainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(BodgeMainWindow, self).__init__(*args, **kwargs)

        self.currentProgram = None
        self.updatingFromData = False

        self.currentTexture = None

        # Import UI from QT designer
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Program Signals
        self.ui.newProgramButton.clicked.connect(self.newProgram)
        self.ui.programListWidget.currentItemChanged.connect(self.programSelectionChanged)
        self.ui.shaderAPath.textChanged.connect(self.pathChanged)
        self.ui.shaderBPath.textChanged.connect(self.pathChanged)
        self.ui.shaderCPath.textChanged.connect(self.pathChanged)
        self.ui.shaderDPath.textChanged.connect(self.pathChanged)

        # Texture Signals
        self.ui.newTextureButton.clicked.connect(self.newTexture)
        self.ui.textureListWidget.currentItemChanged.connect(self.textureSelectionChanged)
        self.ui.pathLineEdit.textChanged.connect(self.texturePathChanged)
        self.ui.startFrameSpinBox.valueChanged.connect(self.textureValueChanged)
        self.ui.lengthSpinBox.valueChanged.connect(self.textureValueChanged)
        self.ui.texComboBox.currentIndexChanged.connect(self.textureBankChanged)

        # Connection to worker
        self.tcpsock = None


    def tryConnect(self):
        if self.tcpsock is None:
            self.tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.tcpsock.connect(("localhost", 31337))
            except ConnectionRefusedError:
                self.tcpsock.close()
                self.tcpsock = None

    def writeToSock(self, msg):
        self.tryConnect()
        if self.tcpsock is not None:
            try:
                rlist, wlist, elist = select([], [self.tcpsock], [], 0)
                if wlist:
                    self.tcpsock.send(str.encode(msg + "\n"))
            except BrokenPipeError:
                self.tcpsock.close()
                self.tcpsock = None

    def newProgram(self):
        if self.ui.newProgramLineEdit.text():
            listitem = QListWidgetItem(self.ui.newProgramLineEdit.text(), self.ui.programListWidget)
            listitem.setData(Qt.UserRole, ProgramData())
            self.currentProgram = listitem.data(Qt.UserRole)

    def programSelectionChanged(self, cur, prev):
        self.currentProgram = cur.data(Qt.UserRole)
        self.updateProgramWidgetsFromData(cur.data(Qt.UserRole))

    def updateProgramWidgetsFromData(self, programData):
        self.updatingFromData = True
        self.ui.shaderAPath.setText(programData.command["A"])
        self.ui.shaderBPath.setText(programData.command["B"])
        self.ui.shaderCPath.setText(programData.command["C"])
        self.ui.shaderDPath.setText(programData.command["D"])
        self.updatingFromData = False

    def pathChanged(self, foo):
        if self.currentProgram is not None and not self.updatingFromData:
            self.currentProgram.command["A"] = self.ui.shaderAPath.text()
            self.currentProgram.command["B"] = self.ui.shaderBPath.text()
            self.currentProgram.command["C"] = self.ui.shaderCPath.text()
            self.currentProgram.command["D"] = self.ui.shaderDPath.text()

            # TODO: Paint lineedits red if path is not valid
            self.writeToSock(json.dumps(self.currentProgram.command))



    def newTexture(self):
        if self.ui.newTextureLineEdit.text():
            listitem = QListWidgetItem(self.ui.newTextureLineEdit.text(), self.ui.textureListWidget)
            listitem.setData(Qt.UserRole, TextureData())
            self.currentTexture = listitem.data(Qt.UserRole)

    def textureSelectionChanged(self, cur, prev):
        self.currentTexture = cur.data(Qt.UserRole)
        self.updateTextureWidgetsFromData()

    def updateTextureWidgetsFromData(self):
        self.updatingFromData = True
        self.ui.pathLineEdit.setText(self.currentTexture.command["path"])
        self.ui.startFrameSpinBox.setValue(self.currentTexture.command["start"])
        self.ui.lengthSpinBox.setValue(self.currentTexture.command["length"])
        self.ui.texComboBox.setCurrentIndex(self.currentTexture.command["texbank"])
        self.updatingFromData = False

    def texturePathChanged(self, path):
        if self.currentTexture is not None:
            self.currentTexture.command["path"] = path
            self.writeToSock(json.dumps(self.currentTexture.command))
            self.scanFolder()

    def scanFolder(self):
        self.updatingFromData = True
        files = []
        if os.path.isdir(self.ui.pathLineEdit.text()):
            files = glob(self.ui.pathLineEdit.text() + "/*.png") + glob(self.ui.pathLineEdit.text() + "/*.jpg") + glob(self.ui.pathLineEdit.text() + "/*.jpeg")
            files.sort()

        self.ui.availableFramesLabel.setText(str(len(files)))
        self.ui.startFrameSpinBox.setMaximum(len(files) - 1)
        self.ui.startFrameSpinBox.setMinimum(1)
        self.ui.lengthSpinBox.setMaximum(len(files) - self.ui.startFrameSpinBox.value())
        self.ui.lengthSpinBox.setMinimum(1)
        self.updatingFromData = False

    def textureValueChanged(self):
        if not self.updatingFromData:
            self.scanFolder()

            if self.currentTexture is not None:
                self.currentTexture.command["start"] = self.ui.startFrameSpinBox.value()
                self.currentTexture.command["length"] = self.ui.lengthSpinBox.value()
                self.writeToSock(json.dumps(self.currentTexture.command))

    def textureBankChanged(self, index):
        if self.currentTexture is not None and not self.updatingFromData:
            self.currentTexture.command["texbank"] = index

            if index > 0:
                for i in range(self.ui.textureListWidget.count()):
                    item = self.ui.textureListWidget.item(i)
                    data = item.data(Qt.UserRole)
                    if not data == self.currentTexture and data.command["texbank"] == index:
                        data.command["texbank"] = 0
            self.writeToSock(json.dumps(self.currentTexture.command))


if __name__ == "__main__":
    app = QApplication(sys.argv)

    mainwin = BodgeMainWindow()
    mainwin.show()

    ret = app.exec()

    sys.exit(ret)
