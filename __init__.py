from PyQt5.QtCore import QSettings


def classFactory(iface):
  from .batch_gps_importer import BatchGpsImporter
  return BatchGpsImporter(iface)

from os.path import expanduser
HOME = expanduser("~")
LOCALE = QSettings().value("locale/userLocale")[0:2]
PLUGIN_FOLDER = 'batch_gps_importer'
PLUGIN_DIR = '{}/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/{}'.\
  format(HOME, PLUGIN_FOLDER)
if LOCALE.startswith('en_'):
  LOCALE = 'en'
DYNAMIC_HELP = '{}/help/dynamic/{}'.format(PLUGIN_DIR, LOCALE)
STATIC_HELP = '{}/help/html/{}'.format(PLUGIN_DIR, LOCALE)
EN_HELP = '{}/help/html/en'.format(PLUGIN_DIR)