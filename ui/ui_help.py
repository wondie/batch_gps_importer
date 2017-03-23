# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_help.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_StaticHelp(object):
    def setupUi(self, StaticHelp):
        StaticHelp.setObjectName(_fromUtf8("StaticHelp"))
        StaticHelp.resize(698, 595)
        self.verticalLayout = QtGui.QVBoxLayout(StaticHelp)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.help_view = QtWebKit.QWebView(StaticHelp)
        self.help_view.setUrl(QtCore.QUrl(_fromUtf8("about:blank")))
        self.help_view.setObjectName(_fromUtf8("help_view"))
        self.verticalLayout.addWidget(self.help_view)
        self.buttonBox = QtGui.QDialogButtonBox(StaticHelp)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(StaticHelp)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), StaticHelp.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), StaticHelp.reject)
        QtCore.QMetaObject.connectSlotsByName(StaticHelp)

    def retranslateUi(self, StaticHelp):
        StaticHelp.setWindowTitle(_translate("StaticHelp", "Batch GPS Importer", None))

from PyQt4 import QtWebKit
