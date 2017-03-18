from PyQt4.QtGui import QAction
from PyQt4.QtGui import QIcon
from gps_importer import GpsImporter
import resources
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
        # use painter for drawing to map canvas
        self.importer = GpsImporter(self.iface)
        self.importer.show_importer()