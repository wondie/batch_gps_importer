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
from PyQt5.QtCore import QSettings, QFileInfo, QTranslator, qVersion, \
    QCoreApplication
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon

from .ui.gps_importer_starter import GpsImporter
from . import PLUGIN_DIR


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
        # Setup locale

        locale_path = ''
        locale = QSettings().value("locale/userLocale")[0:2]
        if QFileInfo(PLUGIN_DIR).exists():
            # Replace forward slash with backslash
            # PLUGIN_DIR = PLUGIN_DIR.replace("\\", "/")
            locale_path = PLUGIN_DIR + "/i18n/batch_gps_importer_%s.qm" % (locale,)
        if QFileInfo(locale_path).exists():
            self.translator = QTranslator()
            self.translator.load(locale_path)
            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        """
        Initializes the plugin GUI.
        """
        self.action = QAction(
            QIcon(u'{}/images/batch.png'.format(PLUGIN_DIR)),
            'Batch GPS Importer', self.iface.mainWindow()
        )
        self.action.setObjectName('gps_importer_action')
        self.action.setWhatsThis('Configuration for Batch GPS Importer')
        self.action.setStatusTip('Batch import GPX files')
        self.action.triggered.connect(self.run)

        # add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToVectorMenu('&Batch GPS Importer', self.action)

    def unload(self):
        """
        Removes the plugin properly.
        """
        # remove the plugin menu item and icon
        self.iface.removePluginMenu('&Batch GPS Importer', self.action)
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
