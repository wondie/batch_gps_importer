# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'help.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_StaticHelp(object):
    def setupUi(self, StaticHelp):
        StaticHelp.setObjectName("StaticHelp")
        StaticHelp.resize(698, 595)
        self.verticalLayout = QtWidgets.QVBoxLayout(StaticHelp)
        self.verticalLayout.setObjectName("verticalLayout")
        self.help_view = QtWebKitWidgets.QWebView(StaticHelp)
        self.help_view.setUrl(QtCore.QUrl("about:blank"))
        self.help_view.setObjectName("help_view")
        self.verticalLayout.addWidget(self.help_view)
        self.buttonBox = QtWidgets.QDialogButtonBox(StaticHelp)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Close)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(StaticHelp)
        self.buttonBox.accepted.connect(StaticHelp.accept)
        self.buttonBox.rejected.connect(StaticHelp.reject)
        QtCore.QMetaObject.connectSlotsByName(StaticHelp)

    def retranslateUi(self, StaticHelp):
        _translate = QtCore.QCoreApplication.translate
        StaticHelp.setWindowTitle(_translate("StaticHelp", "Batch GPS Importer"))

from PyQt5 import QtWebKitWidgets
