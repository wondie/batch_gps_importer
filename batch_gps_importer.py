# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Batch GPS Importer
                                 A QGIS plugin
 Initializer of the plugin.
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
from PyQt4.QtGui import QAction
from PyQt4.QtGui import QIcon

import resources
from ui.gps_importer import GpsImporter
from . import PLUGIN_FOLDER


class BatchGpsImporter:
    def __init__(self, iface):
        self.iface = iface
        self.importer = None

    def initGui(self):
        # create action that will start plugin configuration
        self.action = QAction(
            QIcon(":/plugins/{}/images/batch.png".format(PLUGIN_FOLDER)),
            "Batch GPS Importer", self.iface.mainWindow()
        )
        self.action.setObjectName("gps_importer_action")
        self.action.setWhatsThis("Configuration for Batch GPS Importer")
        self.action.setStatusTip("Batch import GPX files")
        self.action.triggered.connect(self.run)

        # add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToVectorMenu("&Batch GPS Importer", self.action)

    def unload(self):
        # remove the plugin menu item and icon
        self.iface.removePluginMenu("&Batch GPS Importer", self.action)
        self.iface.removeToolBarIcon(self.action)
        # disconnect form signal of the canvas
        self.action.triggered.disconnect(self.run)

    def run(self):
        if self.importer is None:
            self.importer = GpsImporter(self.iface)
            self.importer.show_importer()
        else:
            #self.importer = GpsImporter(self.iface)
            self.importer.show_importer()
            self.importer.activateWindow()
