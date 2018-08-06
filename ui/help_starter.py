# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Batch GPS Importer
                                 A QGIS plugin
 GUI wrapper for Batch GPS Importer
                             -------------------
        begin                : 2017-03-18
        copyright            : (C) 2017 by Wondimagegn Tesfaye Beshah
        email                : wondim81@gmail.com
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 3 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt5.QtWidgets import QDialog

from .help import Ui_StaticHelp
STATIC_HELP_FILE = 'help.html'
class StaticHelp(QDialog, Ui_StaticHelp):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.resize(920, self.height())
