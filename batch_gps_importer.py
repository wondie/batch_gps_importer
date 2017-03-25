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


class BatchGpsImporter(object):
    """
    BatchGpsImport initializes the whole plugin and adds the plugin on toolbar
    and Vector menu of GGIS.
    """
    def __init__(self, iface):
        """
        Initializes iface and importer object.
        :param iface:
        :type iface:
        """
        self.iface = iface
        self.importer = None

    def initGui(self):
        """
        Initializes the plugin GUI.
        """

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
        """
        Removes the plugin properly.
        """
        # remove the plugin menu item and icon
        self.iface.removePluginMenu("&Batch GPS Importer", self.action)
        self.iface.removeToolBarIcon(self.action)
        # disconnect form signal of the canvas
        self.action.triggered.disconnect(self.run)

    def run(self):
        """
        Starts the plugin GUI.
        :return:
        :rtype:
        """
        if self.importer is None:
            self.importer = GpsImporter(self.iface)
            self.importer.show()
        else:
            self.importer.show()
            self.importer.activateWindow()
