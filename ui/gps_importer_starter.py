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
import os.path
from PyQt4.QtCore import QUrl, Qt
from PyQt4.QtGui import (
    QApplication,
    QCheckBox,
    QCursor,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLabel,
    QPushButton,
    QMessageBox,
    QStandardItem,
    QStandardItemModel
)
from PyQt4.QtWebKit import QWebSettings

from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform

from gps_importer import Ui_BatchGpsImporter
from ..importer.process_import import (
    ParamStore, ProcessCombine, GEOMETRY_TYPES, GPX_FIELDS
)
from .. import HOME, STATIC_HELP, EN_HELP
from help_starter import StaticHelp, STATIC_HELP_FILE

class GpsImporter(QDialog, Ui_BatchGpsImporter):
    """
    A GUI class that enable users set parmeters to batch import gpx files.
    """
    def __init__(self, iface):
        """
        Initializes the user interface and properties.
        :param iface: The QGis interface
        :type iface: qgis.utils.iface
        """

        QDialog.__init__(self, iface.mainWindow())
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.help_box_width = 206
        self.curr_help_box_width = 0  # the width of the help box before hiding
        self.setupUi(self)
        self.field_items = {}
        self.param_store = ParamStore()
        self.init_gui()
        self._valid_gpx_folder_path = None
        self._invalid_gpx_folder_path = None
        self._help_anchor = ''
        self._help_text = ''
        self._input_gpx_folder_path = None
        self.excluded_fields = []

        self.input_projection_cbo.setCrs(
            QgsCoordinateReferenceSystem('EPSG:4326')
        )
        self.waypoint.setProperty('name', 'waypoints')
        self.track.setProperty('name', 'tracks')
        self.route.setProperty('name', 'routes')

        self.connect_signals_and_events()

    def init_gui(self):
        """
        Initializes the GUI.
        """
        self.populate_geometry_type()
        self.populate_field_box()
        self.rename_buttonbox()
        self.add_dynamic_help_button()
        self.hide_dynamic_help(on_load_hide=True)
        self.hide_extent_buttons()
        self.tab_widget.removeTab(3)
        self.exclude_fields_view.setHeaderHidden(True)
        self.exclude_fields_view.setColumnWidth(0, 150)
        self.exclude_fields_groupbox.toggled.connect(
            self.on_fields_group_box_toggled
        )
        self.extent_box.setChecked(False)
        self.layer_name_edit.setText(self.param_store.layer_name)

    def connect_signals_and_events(self):
        """
        Connects signals and events.
        :return:
        :rtype:
        """
        self.buttonBox.helpRequested.connect(self.on_show_static_help)
        self.input_gpx_file_btn.clicked.connect(
            lambda: self.file_dialog(self.input_gpx_folder)
        )
        self.input_gpx_folder.textChanged.connect(self.validate_folder_path)
        self.valid_folder_btn.clicked.connect(
            lambda: self.file_dialog(self.valid_gpx_folder)
        )
        self.valid_gpx_folder.textChanged.connect(self.validate_folder_path)
        self.invalid_folder_btn.clicked.connect(
            lambda: self.file_dialog(self.invalid_gpx_folder)
        )
        self.invalid_gpx_folder.textChanged.connect(self.validate_folder_path)
        self.canvas.extentsChanged.connect(self.on_update_extent_box)
        self.extent_box.clicked.connect(self.on_update_extent_box)
        self.extent_box.collapsedStateChanged.connect(self.on_prevent_collapse)
        self.dynamic_help_btn.clicked.connect(self.on_dynamic_help)
        self.dynamic_help_box.loadFinished.connect(self.on_help_loaded)
        self.mousePressEvent = self.set_help_text

    def on_show_static_help(self):
        static_help = StaticHelp(self)
        help_url = QUrl()
        help_path = os.path.join(STATIC_HELP, STATIC_HELP_FILE)
        if not os.path.isfile(help_path) and not os.path.isdir(STATIC_HELP):
            help_path = os.path.join(EN_HELP, STATIC_HELP_FILE)
        help_url.setPath(help_path)
        static_help.help_view.load(help_url)
        static_help.show()

    def hide_extent_buttons(self):
        """
        Hides the extent box buttons as they are not necessary. The extent box
        updates automatically on map zoom.
        """
        for button in self.extent_box.findChildren(QPushButton):
            button.setHidden(True)
            button.parent().setHidden(True)
            button.deleteLater()
            button.parent().deleteLater()

    def set_help_text(self, event):
        """
        Help event listener that responds to mouse click on labels to show
        dynamic help text.
        :param event: The event
        :type event: QMouseEvent
        """
        if not self.dynamic_help_box.isVisible():
            return
        widget = QApplication.widgetAt(QCursor.pos())
        if isinstance(widget, QLabel):
            text = widget.text()
            self.load_html_from_text(text)

    def load_html_from_text(self, text):
        """
        Loads html file by constructing the path using a clicked label.
        :param text: The label text
        :type text: String
        """
        self.dynamic_help_box.setHtml('')
        anchor_text = text.replace(' ', '_').lower().replace('-', '_')
        file_name = 'help'
        help_path = '{}/{}.html'.format(STATIC_HELP, file_name)

        if not os.path.isfile(help_path) and not os.path.isdir(STATIC_HELP):
            help_path = '{}/{}.html'.format(EN_HELP, file_name)
        help_url = QUrl()
        help_url.setPath(help_path)
        self._help_anchor = anchor_text
        self._help_text = text

        # allow JavaScript to run
        self.dynamic_help_box.page().settings().testAttribute(
            QWebSettings.JavascriptEnabled
        )
        self.dynamic_help_box.load(help_url)

    def on_help_loaded(self, ok):
        """
        A slot raised when an HTML loading finishes.
        :param ok: The success or failure of the load status.
        True if successful.
        :type ok: Boolean
        """
        if ok:
            if self._help_anchor == '':
                return

            self.dynamic_help_box.page().mainFrame().scrollToAnchor(
                self._help_anchor
            )

    def add_dynamic_help_button(self):
        """
        Adds the dynamic help button.
        """
        self.dynamic_help_btn = QPushButton(
            QApplication.translate(
                'GpsImporter', 'Show Dynamic Help'
            )
        )
        self.buttonBox.addButton(
            self.dynamic_help_btn, QDialogButtonBox.ActionRole
        )

    def hide_dynamic_help(self, on_load_hide=False):
        """
        Hides the dynamic help button.
        :param on_load_hide: Determins weather the method is called when the
        GUI is loaded or not.
        :type on_load_hide: Boolean
        """
        if not on_load_hide:
            self.curr_help_box_width = self.dynamic_help_box.width()

        self.dynamic_help_box.setVisible(False)
        self.resize(self.width() - self.curr_help_box_width, self.height())

        self.resize(self.width() - 30, self.height())
        hide_text = QApplication.translate(
            'GpsImporter', 'Show Dynamic Help'
        )
        self.dynamic_help_btn.setText(hide_text)

    def show_dynamic_help(self):
        """
        Shows the dynamic help box.
        """
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
        """
        A slot raised when the show/hide dynamic help button is clicked.
        """
        if self.dynamic_help_box.isVisible():
            self.hide_dynamic_help()
        else:
            self.show_dynamic_help()

    def rename_buttonbox(self):
        """
        Rename the Ok and Cancel buttons to Import and Exit.
        :return:
        :rtype:
        """
        import_txt = QApplication.translate(
            'GpsImporter', 'Import'
        )
        exit_txt = QApplication.translate(
            'GpsImporter', 'Exit'
        )
        self.buttonBox.button(QDialogButtonBox.Ok).setText(import_txt)
        self.buttonBox.button(QDialogButtonBox.Cancel).setText(exit_txt)

    def on_update_progress(self, text):
        """
        A slot raised used to update the progress by emitting progress message.
        :param text: The progress message.
        :type text: String
        """
        QApplication.processEvents()

        self.progress_text_edit.append(text)

    def on_prevent_collapse(self):
        """
        Prevent the extent box collapse when the checkbox is clicked.
        """
        self.extent_box.setCollapsed(False)

    def on_update_extent_box(self):
        """
        A slot raised to automatically update the bounding box coordinates when
        the the map zoom level changes and when the extent box is enabled.
        :return:
        :rtype:
        """
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
            pass

    def populate_geometry_type(self):
        """
        Populate the geometry type combobox.
        """
        self.geometry_type_cbo.addItem('', None)
        for key, value in GEOMETRY_TYPES.iteritems():
            self.geometry_type_cbo.addItem(value, key)

    def populate_field_box(self):
        """
        Populate the fields combobox.
        """
        model = QStandardItemModel(1, 0)
        model.setColumnCount(2)
        field_count = len(GPX_FIELDS)
        half_count = int(field_count/2)
        for i, item_text in enumerate(GPX_FIELDS.values()):
            item = QStandardItem(item_text)
            item.setCheckState(2)
            item.setCheckable(True)
            if i >= half_count:
                model.setItem(i-half_count, 1, item)
                self.field_items[item_text] = 1
            else:
                model.setItem(i, 0, item)
                self.field_items[item_text] = 0
        self.exclude_fields_view.setModel(model)
        self.exclude_fields_view.model().itemChanged.connect(
            self.on_fields_toggled
        )

    def on_fields_group_box_toggled(self):
        """
        A slot raised when the fields group box is checked or unchecked.
        Removes the selection from all fields when unchecked and selects all
        fields when checked.
        """
        for text, column in self.field_items.iteritems():
            items = self.exclude_fields_view.model().findItems(
                text, Qt.MatchExactly, column
            )
            for item in items:
                if self.exclude_fields_groupbox.isChecked():
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)

    def on_fields_toggled(self, item):
        """
        A slot raised when a field is checked or unchecked.
        The field unchecked is added to excluded_fields list. If checked,
        the field will be removed from the excluded_list.
        :param item: The field item
        :type item: QStandardItem
        """
        if item.checkState() == Qt.Unchecked:
            self.excluded_fields.append(item.text())
        else:
            self.excluded_fields.remove(item.text())

    def file_dialog(self, line_edit):
        """
        Displays a file dialog for a user to specify a GPX Folder.
        :param line_edit: The line edit in which the folder is going to be set.
        :type line_edit: QLineEdit
        """
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
        if len(path) > 0:
            line_edit.setText(path)

        if line_edit == self.input_gpx_folder:
            self._input_gpx_folder_path = path
        if line_edit == self.valid_gpx_folder:
            self._valid_gpx_folder_path = path
        if line_edit == self.invalid_gpx_folder:
            self._invalid_gpx_folder_path = path

    def validate_folder_path(self, text):
        """
        Checks the folder path corresponds to a real folder.
        :param text: The path
        :type text: String
        :return: None
        :rtype: NoneType
        """
        if text == '':
            return
        if not os.path.isdir(text):
            title = QApplication.translate('GpsImporter', 'Invalid Path')
            message = QApplication.translate(
                'GpsImporter', 'The folder is not valid.'
            )
            QMessageBox.critical(
                self, title, message
            )
            # if invalid, set the earlier accepted path
            if self.sender() == self.input_gpx_folder:
                self.sender().setText(self._input_gpx_folder_path)
            if self.sender() == self.valid_gpx_folder:
                self.sender().setText(self._valid_gpx_folder_path)
            if self.sender() == self.invalid_gpx_folder:
                self.sender().setText(self._invalid_gpx_folder_path)

    def set_input_value(self):
        """
        Sets the input values to the ParamStore properties.
        """
        self.param_store.input_path = self.input_gpx_folder.text()
        self.param_store.file_name_prefix = self.file_name_prefix.text()
        self.param_store.file_name_suffix = self.file_name_suffix.text()
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
        self.param_store.exclude_with_error = self.exclude_with_errors_rbtn. \
            isChecked()
        self.param_store.extent_bound_enabled = self.extent_box.isChecked()
        self.param_store.extent_bound = self.extent_box.outputExtent()

        self.param_store.exclude_with_few_points = \
            self.exclude_with_few_points.isChecked()
        self.param_store.scan_sub_folders = \
            self.scan_sub_folders_rdb.isChecked()
        self.param_store.valid_gpx_folder = self.valid_gpx_folder.text()
        self.param_store.invalid_gpx_folder = self.invalid_gpx_folder.text()
        self.param_store.excluded_fields = self.excluded_fields

        if len(self.layer_name_edit.text()) > 1:
            self.param_store.layer_name = self.layer_name_edit.text()

        self.param_store.iface = self.iface
        self.param_store.set_required()

    def validate_mandatory_inputs(self):
        """
        Validates mandatory inputs are filled.
        :return: Return true if valid and false if not valid.
        :rtype:
        """
        unfilled = []
        for input_name, input_var in self.param_store.required.iteritems():
            if input_var == '' or input_var is None:
                unfilled.append(input_name)
            elif isinstance(input_var, list) and len(input_var) < 1:
                unfilled.append(input_name)

        if len(unfilled) > 0:
            title = QApplication.translate(
                'GpsImporter', 'Mandatory Field Error')
            message = QApplication.translate(
                'GpsImporter', 'The following mandatory fields are empty:'
                               '\n{}'.format(', '.join(unfilled))
            )
            QMessageBox.critical(
                self, title, message
            )
            return False
        return True

    def accept(self):
        """
        A builtin slot raised when the dialog is accepted with the click of
        the Import button. It starts the import process.
        :return: None if mandatory inputs are not filled.
        :rtype: NoneType
        """
        self.set_input_value()
        if not self.validate_mandatory_inputs():
            return
        log_name = QApplication.translate(
            'GpsImporter',
            'Log'
        )
        self.tab_widget.insertTab(3, self.log_tab, log_name)
        self.progress_text_edit.clear()

        text_1 = QApplication.translate(
            'GpsImporter',
            '<html><b>Started the importing from'
        )
        text_2 = QApplication.translate('GpsImporter', '</b></html>')

        start_text = u'{} {}{}'.format(
            text_1, self.param_store.input_path, text_2
        )

        self.progress_text_edit.append(start_text)
        self.tab_widget.setCurrentIndex(4)
        self.tab_widget.setCurrentWidget(self.log_tab)
        self.process = ProcessCombine(self.iface.mainWindow())
        self.process.progress.connect(self.on_update_progress)
        self.process.finish_import(self.param_store)
