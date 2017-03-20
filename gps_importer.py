import os.path

from PyQt4.QtCore import QUrl
from PyQt4.QtGui import QApplication
from PyQt4.QtGui import QCheckBox
from PyQt4.QtGui import QCursor
from PyQt4.QtGui import QDialog
from PyQt4.QtGui import QDialogButtonBox
from PyQt4.QtGui import QFileDialog
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QPushButton
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform

from .ui_gps_importer import Ui_BatchGpsImporter
from .process_import import (
    ParamStore, ProcessCombine, GEOMETRY_TYPES
)
from . import DYNAMIC_HELP, HOME



class GpsImporter(QDialog, Ui_BatchGpsImporter):
    def __init__(self, iface):
        #TODO add a flag for scan sub-folders, included and excluded folders
        QDialog.__init__(self, iface.mainWindow())
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.help_box_width = 206
        self.curr_help_box_width = 0  # the width of the help box before hiding
        self.setupUi(self)
        self.init_gui()
        self.param_store = ParamStore()
        self.input_gpx_file_btn.clicked.connect(
            self.file_dialog
        )
        self.input_projection_cbo.setCrs(
            QgsCoordinateReferenceSystem('EPSG:4326')
        )
        self.waypoint.setProperty('name', 'waypoints')
        self.track.setProperty('name', 'tracks')
        self.route.setProperty('name', 'routes')
        #print self.waypoint.property('name')
        self.extent_box.setChecked(False)
        self.canvas.extentsChanged.connect(self.update_extent_box)
        self.extent_box.clicked.connect(self.update_extent_box)
        self.extent_box.collapsedStateChanged.connect(self.prevent_collapse)
        self.dynamic_help_btn.clicked.connect(self.on_dynamic_help)
        self.help_events()

    def init_gui(self):
        self.populate_geometry_type()
        self.rename_buttonbox()
        self.add_dynamic_help_button()
        self.hide_dynamic_help(on_load_hide=True)
        self.hide_extent_buttons()

    def hide_extent_buttons(self):
        for button in self.extent_box.findChildren(QPushButton):
            button.setHidden(True)
            button.parent().setHidden(True)
            button.deleteLater()
            button.parent().deleteLater()

    def help_events(self):
        self.mousePressEvent = self.set_help_text

    def set_help_text(self, event):
        if not self.dynamic_help_box.isVisible():
            return
        widget = QApplication.widgetAt(QCursor.pos())

        if isinstance(widget, QLabel):
            text = widget.text()
            file_name = text.replace(' ', '_').lower().replace('-','_')
            help_path = '{}/{}.html'.format(DYNAMIC_HELP, file_name)
            if not os.path.isfile(help_path):
                no_translation = QApplication.translate(
                    'GpsImporter', 'Sorry, the help is not translated '
                    'to your language. Please contact us via '
                    'wondim81@gmail.com to translate '
                    'it to your language.'
                )
                self.dynamic_help_box.setHtml(no_translation)
            help_url = QUrl()
            help_url.setPath(help_path)
            self.dynamic_help_box.load(help_url)

    def add_dynamic_help_button(self):
        self.dynamic_help_btn = QPushButton(
            QApplication.translate(
                'GpsImporter', 'Show Dynamic Help'
            )
        )
        self.buttonBox.addButton(
            self.dynamic_help_btn, QDialogButtonBox.ActionRole
        )

    def hide_dynamic_help(self, on_load_hide=False):
        if not on_load_hide:
            self.curr_help_box_width = self.dynamic_help_box.width()

        self.dynamic_help_box.setVisible(False)
        self.resize(self.width() - self.curr_help_box_width, self.height())

        self.resize(self.width() - 30, self.height())
        hide_text = QApplication.translate(
            'GpsImporter', 'Show Dynamic Help'
        )
        self.dynamic_help_btn.setText(hide_text)

    def on_help_box_resize(self, event):
        # if dynamic help box width changes, set the help_box_width
        if self.dynamic_help_box.width() > 0:
            self.help_box_width = self.dynamic_help_box.width()

    def show_dynamic_help(self):
        self.dynamic_help_box.setVisible(True)

        if self.curr_help_box_width > 0:
            self.resize(self.width() + self.curr_help_box_width, self.height())
            self.dynamic_help_box.resize(
                self.curr_help_box_width, self.dynamic_help_box.height()
            )
        else:

            self.resize(self.width() + self.help_box_width, self.height())

            self.dynamic_help_box.resize(
                self.help_box_width, self.dynamic_help_box.height()
            )
            first_info = QApplication.translate(
                'GpsImporter', 'To read the description of each input here, '
                               'click on any input label on the left side. '
            )
            self.dynamic_help_box.setHtml(first_info)
        hide_text = QApplication.translate(
            'GpsImporter', 'Hide Dynamic Help'
        )
        self.dynamic_help_btn.setText(hide_text)

    def on_dynamic_help(self):
        if self.dynamic_help_box.isVisible():
            self.hide_dynamic_help()
        else:
            self.show_dynamic_help()

    def rename_buttonbox(self):
        import_txt = QApplication.translate(
            'GpsImporter', 'Import'
        )
        exit_txt = QApplication.translate(
            'GpsImporter', 'Exit'
        )
        self.buttonBox.button(QDialogButtonBox.Ok).setText(import_txt)
        self.buttonBox.button(QDialogButtonBox.Cancel).setText(exit_txt)

    def update_progress(self, text):
        QApplication.processEvents()

        self.progress_text_edit.append(text)

    def prevent_collapse(self):
        self.extent_box.setCollapsed(False)

    def update_extent_box(self):
        if not self.extent_box.isChecked():
            return
        try:
            canvas_extent = self.canvas.extent()

            transformer = QgsCoordinateTransform(
                self.canvas.mapRenderer().destinationCrs(),
                self.input_projection_cbo.crs()
            )

            transformer.setDestCRS(
                self.input_projection_cbo.crs()
            )
            transformed_extent = transformer.transform(canvas_extent)

            self.extent_box.setOriginalExtent(
                transformed_extent,
                QgsCoordinateReferenceSystem(
                    self.input_projection_cbo.crs().authid()
                )
            )

            self.extent_box.setOutputCrs(
                QgsCoordinateReferenceSystem(
                    self.input_projection_cbo.crs().authid()
                )
            )
            self.extent_box.setOutputExtentFromOriginal()
            self.extent_box.setCurrentExtent(
                transformed_extent,
                QgsCoordinateReferenceSystem(
                    self.input_projection_cbo.crs().authid()
                )
            )
        except Exception as ex:
            print ex

    def populate_geometry_type(self):
        self.geometry_type_cbo.addItem('', None)
        for key, value in GEOMETRY_TYPES.iteritems():
            self.geometry_type_cbo.addItem(value, key)

    def file_dialog(self):
        """
        Displays a file dialog for a user to specify a source document
        :param title: The title of the file dialog
        :type title: String
        """
        #Get last path for supporting documents
        title = QApplication.translate(
            "GpsImporter",
            "Select a Folder"
        )
        last_path = HOME
        path = QFileDialog.getExistingDirectory(
            self.iface.mainWindow(),
            title,
            last_path,
            QFileDialog.ShowDirsOnly
        )
        self.input_gpx_folder.setText(path)

    def show_importer(self):
        self.show()

    def set_input_value(self):
        self.param_store.input_path = self.input_gpx_folder.text()
        self.param_store.layer_name = None
        self.param_store.geometry_type = self.geometry_type_cbo.itemData(
            self.geometry_type_cbo.currentIndex()
        )
        feature_types = [
            widget.property('name')
            for widget in self.input_output_tab.findChildren(QCheckBox)
            if widget.isChecked() and widget.property('name')
        ]

        self.param_store.feature_types = feature_types

        epsg = self.input_projection_cbo.crs().authid()
        if len(epsg.split(':')) > 0:
            self.param_store.gpx_projection = epsg.split(':')[1]
        self.param_store.exclude_with_error = self.exclude_with_errors_rbtn.\
            isChecked()
        self.param_store.extent_bound_enabled = self.extent_box.isChecked()
        self.param_store.extent_bound = self.extent_box.outputExtent()
        self.param_store.iface = self.iface
        self.param_store.set_required()

    def accept(self):
        self.set_input_value()
        self.progress_text_edit.clear()
        start_text = QApplication.translate(
            'GpsImporter',
            '<html><b>Started the importing from {}</b></html>'.format(
                self.param_store.input_path
            )
        )

        self.progress_text_edit.append(start_text)
        self.tab_widget.setCurrentIndex(3)
        self.tab_widget.setCurrentWidget(self.log_tab)
        self.process = ProcessCombine(self.iface.mainWindow())
        self.process.progress.connect(self.update_progress)
        self.process.combine_layers(self.param_store)

