# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Batch GPS Importer
                                 A QGIS plugin
 Batch Importer
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
import glob
import shutil
from collections import OrderedDict
import os
from PyQt5.QtCore import QObject, QVariant, pyqtSignal

from PyQt5.QtWidgets import QApplication, QLabel, QProgressDialog

from qgis.core import (
    QgsGeometry,
    QgsFeature,
    QgsPoint,
   
    QgsVectorLayer,
    QgsRectangle,
    QgsField,
    QgsProject
)

from osgeo import ogr
from .gpx_util import GpxUtil

VALID_GPX_FILES = []
INVALID_GPX_FILES = []
ID_NUMBER = 0
FEATURE_TYPES = OrderedDict([
    ('tracks', 'Track'), ('waypoints', 'Waypoint'), ('routes', 'Routes')
])

GPX_FIELDS = OrderedDict([
    ('ele', 'elevation'), ('name', 'name'), ('cmt', 'comment'),
    ('desc', 'description'), ('url', 'url'), ('urlname', 'url_name'),
    ('sym', 'symbol'), ('src', 'source'), ('type', 'type'),
    ('time', 'capture_time'), ('feature_type', 'feature_type'),
    ('file_name', 'file_name')
])
STOP_IMPORT = False


class ParamStore(object):
    """
    Stores parameters and required fields of Batch GPX Importer. It servers
    both the Import Initializer class Process Combine and GPXToFeature.
    """

    def __init__(self):
        """
        Initializes the parameter properties.
        """
        self.input_path = None
        self.geometry_type = None
        self.feature_types = None
        self.gpx_projection = None
        self.required = None
        self.extent_bound = None
        self.file_name_prefix = None
        self.file_name_suffix = None
        self.extent_bound_enabled = False
        self.exclude_with_error = False
        self.exclude_with_few_points = False
        self.scan_sub_folders = True
        self.valid_gpx_folder = None
        self.invalid_gpx_folder = None
        self.layer_name = QApplication.translate(
            'ParamStore', 'combined_gpx'
        )
        self.excluded_fields = []

        line_str = QApplication.translate('ParamStore', 'Line')
        polygon_str = QApplication.translate('ParamStore', 'Polygon')
        point_str = QApplication.translate('ParamStore', 'Point')

        self.geometry_types = OrderedDict([
            ('Linestring', line_str),
            ('Point', point_str),
            ('Polygon', polygon_str)
        ])

        self.iface = None

    def set_required(self):
        """
        Sets a required fields of the parameters.
        """
        self.required = {
            QApplication.translate(
                'ParamStore', 'GPX folder'
            ): self.input_path,
            QApplication.translate(
                'ParamStore', 'Geometry type'
            ): self.geometry_type,
            QApplication.translate(
                'ParamStore', 'GPX format'
            ): self.feature_types
        }


class GpxToFeature(QObject):
    """
    Creates a QGIS features from gpx file path.
    """
    progress = pyqtSignal(str)

    def __init__(self, param_store):
        """
        Initializes and sets the parameter properties.
        :param param_store: The ParamStore object containing all parameters
        required to create a QgsFeature from a gpx file.
        :type param_store: Object
        """
        self.iface = param_store.iface
        QObject.__init__(self, self.iface.mainWindow())
        self.param_store = param_store
        self.map_canvas = self.iface.mapCanvas()
        self.input_path = param_store.input_path
        self.feature_types = param_store.feature_types
        self.feature_type = None
        self.geometry_type = param_store.geometry_type
        self.gpx_projection = param_store.gpx_projection
        self.exclude_with_few_points = param_store.exclude_with_few_points
        self.extent_bound_enabled = param_store.extent_bound_enabled
        self.gpx_file_name = None
        self.gpx_path = None
        self.file_name = None
        self.exclude_with_error = param_store.exclude_with_error
        self.extent_bound = param_store.extent_bound

        self.valid_gpx_folder = param_store.valid_gpx_folder
        self.invalid_gpx_folder = param_store.invalid_gpx_folder
        self.excluded_fields = param_store.excluded_fields
        self.gpx_util = None
        self.layer_fields = []
        self.final_features = []
        self.error_type = None
        self.ogr_layer = None
        self.gpx_data = OrderedDict()
        self.valid_gpx_files = []
        self.invalid_gpx_files = []
        self._point_attributes = OrderedDict()
        self._point_row = 0
        self.feature_points = {
            'tracks': 'trkpt', 'routes': 'rtept', 'waypoints': 'wpt'
        }
        self.xml_feature_types = {
            'tracks': 'trk', 'routes': 'rte', 'waypoints': 'wpt'
        }
        self.stop_feature_creation = False

    def init_gpx_import(self, gpx_path):
        """
        Initializes the gpx import by setting the gpx path. This method must be
        called outside the class to properly connect signals.
        :param gpx_path: The gpx file path.
        :type gpx_path: String
        """
        # Open GPX file
        if self._file_is_readable(gpx_path):
            self.gpx_file_name = os.path.basename(gpx_path)
            self.file_name = self.gpx_file_name.rstrip('.gpx')
            self.gpx_path = gpx_path
            self.gpx_util = GpxUtil(self.gpx_path)

            data_source = ogr.Open(gpx_path)
            if data_source is not None:
                for feature_type in self.feature_types:
                    if STOP_IMPORT:
                        return
                    # self.feature_type = feature_type.encode('utf-8')
                    self.feature_type = feature_type
                    self.ogr_layer = data_source.GetLayerByName(
                        self.feature_type
                    )

                    if self.ogr_layer.GetFeatureCount() > 0:
                        # try:
                        self.gpx_to_point_list()
                        # except Exception as ex:
                        #     self.error_type = ex
                        #     self.add_progress()
                        if STOP_IMPORT:
                            return
                        self.save_valid_folders()
                        self.save_invalid_folders()

    def _file_is_readable(self, gpx_path):
        """
        Checks if the gpx file is readable.
        :param gpx_path: The gpx file path.
        :type gpx_path: String
        :return: True if it is a file and readable otherwise return False.
        :rtype: Boolean
        """
        try:
            if not os.access(gpx_path, os.R_OK):
                return False
            else:
                return True
        except Exception as ex:
            self.error_type = str(ex)

    def gpx_to_point_list(self):
        """
        A container method that runs all other methods that extract geometry,
        attributes, and creates point, line, and polygon features.
        """
        self.join_points_and_attributes()
        if STOP_IMPORT:
            return
        if len(self.gpx_data) < 1:
            return
        if self.feature_type == 'waypoints':
            self.create_polygon()
            self.create_point()
            self.create_line()
        self.add_progress()

    def save_valid_folders(self):
        """
        Saves valid folder to a supplied folder. If no path is give,
        nothing will be saved.
        """
        if len(self.valid_gpx_folder) > 2:
            if self.error_type is None:
                VALID_GPX_FILES.append(self.gpx_path)

    def save_invalid_folders(self):
        """
        Saves invalid folder to a supplied folder. If no path is give,
        nothing will be saved.
        """
        if len(self.invalid_gpx_folder) > 2:
            if self.error_type is not None:
                INVALID_GPX_FILES.append(self.gpx_path)

    def join_points_and_attributes(self):
        """
        Joins geometry and attributes to be used to create a feature.
        """
        self.gpx_data.clear()
        for i, ogr_feature in enumerate(self.ogr_layer):
            if STOP_IMPORT:
                return
            if ogr_feature is None:
                continue
            qgs_geom = self.extract_geometry(ogr_feature)

            if qgs_geom is None:
                continue

            feature_name = self.feature_points[self.feature_type]
            if self.geometry_type != 'Point':
                feature_name = self.xml_feature_types[self.feature_type]

            self._point_attributes = self.gpx_util.gpx_point_attributes(feature_name)

            if self.feature_type == 'waypoints':
                field_attributes = self.extract_attributes(i)
                point = qgs_geom.asMultiPoint()
                self.gpx_data[point[0]] = field_attributes
            else:
                # To prevent all tracks or routes in a file are treated as one
                # feature clear the gpx_data.
                self.gpx_data.clear()
                points = qgs_geom.asMultiPolyline()
                if self.geometry_type == 'Point':
                    for point_row, single_point in enumerate(points[0]):

                        if STOP_IMPORT:
                            return

                        field_attributes = self.extract_attributes(point_row)
                        self.gpx_data[single_point] = field_attributes
                else:
                    field_attributes = self.extract_attributes(0)
                    self.gpx_data[points[0][0]] = field_attributes

            if self.feature_type != 'waypoints':
                self.create_polygon()
                self.create_point()
                self.create_line()

    @staticmethod
    def extract_geometry(ogr_feature):
        """
        Extracts QgsGeometry from OGR feature.
        :param ogr_feature: The OGR feature
        :type ogr_feature: Object
        :return: The extracted geometry
        :rtype: QgsGeometry
        """
        geom = ogr_feature.GetGeometryRef()
        wkt = geom.ExportToWkt()
        qgs_geom = QgsGeometry.fromWkt(wkt)
        qgs_geom.convertToMultiType()
        return qgs_geom

    def extract_attributes(self, point_row=0):
        """
        Extracts the attributes of a feature.
        :param point_row: The point row a vertex
        :type point_row: Integer
        :return: Dictionary of fields and attributes as key and value.
        :rtype: OrderedDict
        """
        field_attributes = OrderedDict()
        if len(self._point_attributes) >= 1:
            current_attributes = self._point_attributes[point_row]
        else:
            current_attributes = OrderedDict()

        QApplication.processEvents()
        for original_field, final_field in GPX_FIELDS.items():
            if final_field in self.excluded_fields:
                continue
            if original_field in current_attributes.keys():
                field_attributes[final_field] = current_attributes[
                    original_field
                ]
            elif original_field == 'feature_type':
                field_attributes['feature_type'] = self.feature_type
            elif original_field == 'file_name':
                field_attributes['file_name'] = self.gpx_file_name
            else:
                field_attributes[final_field] = None
        return field_attributes

    def create_line(self):
        """
        Creates a line feature.
        """
        if self.geometry_type == 'Linestring':
            line_geom = QgsGeometry.fromPolylineXY(self.gpx_data.keys())
            attributes = list(self.gpx_data.values())[0]
            # validate_insufficient_points
            if not self.validate_insufficient_points(self.gpx_data.keys(), 2):
                return
            # remove the ungroupped dictionary
            self.gpx_data.clear()
            if self.validate_geometry(line_geom):
                self.gpx_data[line_geom] = attributes
                self.create_feature(line_geom, list(self.gpx_data.values())[0])

    def create_point(self):
        """
        Creates a point feature.
        """
        if self.geometry_type == 'Point':
            invalid_geom = []
            for points, attributes in self.gpx_data.items():
                QApplication.processEvents()
                point_geom = QgsGeometry.fromPointXY(points)
                # error message is suppressed for points to improve performance
                if self.validate_geometry(point_geom, suppress_errors=True):
                    self.create_feature(point_geom, attributes)
                else:
                    invalid_geom.append(point_geom)
            if len(invalid_geom) > 0:
                self.error_type = QApplication.translate(
                    'GpxToFeature', 'Geometry error'
                )

    def create_polygon(self):
        """
        Creates a polygon feature.
        """
        if self.geometry_type == 'Polygon':
            poly_geom = QgsGeometry.fromPolygonXY([list(self.gpx_data.keys())])
            attributes = list(self.gpx_data.values())[0]
            # update the gpx_data to contain polygon geometry as a key and
            # and only the first attributes
            if not self.validate_insufficient_points(self.gpx_data.keys(), 3):
                return
            # remove the ungroupped dictionary as polygon
            self.gpx_data.clear()
            if self.validate_geometry(poly_geom):
                self.gpx_data[poly_geom] = attributes

                self.create_feature(
                    poly_geom, self.gpx_data[list(self.gpx_data.keys())[0]]
                )

    def create_feature(self, gpx_geom, attributes):
        """
        Creates a QgsFeature from QgsGeometry and attributes.
        :param gpx_geom: The gpx geometry
        :type gpx_geom: QgsGeometry
        :param attributes: The attribute of the gpx feature.
        :type attributes: OrderedDict
        """
        global ID_NUMBER
        ID_NUMBER += 1
        for field in attributes.keys():
            self.layer_fields.append(QgsField(field, QVariant.String))
        feature = QgsFeature()
        feature.setGeometry(gpx_geom)

        feature.setAttributes(
            [ID_NUMBER] + list(attributes.values())
        )

        bounding_box = gpx_geom.boundingBox()
        if self.validate_extent(bounding_box):
            self.final_features.append(feature)

    def add_progress(self):
        """
        Adds a progress text by emitting progress and sending a message through
        the emitted signal.
        """
        if len(self.final_features) == 0:
            if self.error_type is not None:
                text_in = QApplication.translate('GpxToFeature', 'in')
                error_message = '{} {} {}'.format(
                    self.error_type, text_in, self.gpx_file_name
                )
                self.progress.emit(error_message)
        else:
            message = QApplication.translate(
                'GpxToFeature',
                'Created feature(s) for'
            )
            success_message = '{} {}'.format(message, self.gpx_file_name)
            self.progress.emit(success_message)

    def validate_insufficient_points(self, geoms, point_counts):
        """
        Validates for the presence of insufficient points when creating lines
        and polygons.
        :param geoms: The geometry to be validated.
        :type geoms: list of QgsGeometry
        :param point_counts: The minimum number of points allowed to create
        a geometry. For line it is 2 and for polygon it is 3.
        :type point_counts: Integer
        :return: The state of the validity. It returns true if valid and false
        if invalid.
        :rtype: Boolean
        """
        error_state = True
        if self.exclude_with_few_points:

            if len(geoms) < point_counts:
                error_type = QApplication.translate(
                    'GpxToFeature',
                    'Insufficient points to create a valid'
                )
                self.error_type = '{} {}'.format(
                    error_type,
                    self.param_store.geometry_types[self.geometry_type])
                error_state = False
                return error_state
            else:
                return error_state
        else:
            return error_state

    def validate_geometry(self, geom, suppress_errors=False):
        """
        Checks if geometry errors exists in a geometry.
        :param geom: The geometry to be validated.
        :type geom: QgsGeometry
        :param suppress_errors: If True, prevents error message from
        appearing in the log. Otherwise, if False, errors will be shown in
        the log.
        :type suppress_errors: Boolean
        :return: The state of the validity. It returns true if valid and false
        if invalid.
        :rtype: Boolean
        """
        if self.exclude_with_error:
            errors = geom.validateGeometry()
            if len(errors) == 0:
                return True
            else:
                if not suppress_errors:
                    error_desc = [er.what() for er in errors]
                    self.error_type = ' '.join(error_desc)

                return False
        else:
            return True

    def validate_extent(self, extent_rect):
        """
        It checks the supplied extent is the within the bounding box of the
        map.
        :param extent_rect: The bonding box of the geometry.
        :type extent_rect: QgsRectangle
        :return: A boolean showing the geometry is within the boundary with
         true or outside the extent with false.
        :rtype: Boolean
        """
        if self.extent_bound_enabled:
            x_min = extent_rect.xMinimum()
            x_max = extent_rect.xMaximum()
            y_min = extent_rect.yMinimum()
            y_max = extent_rect.yMaximum()
            user_x_min = self.extent_bound.xMinimum()
            user_x_max = self.extent_bound.xMaximum()
            user_y_min = self.extent_bound.yMinimum()
            user_y_max = self.extent_bound.yMaximum()
            if x_min > user_x_min and y_min > user_y_min and \
                            x_max < user_x_max and y_max < user_y_max:
                return True
            else:
                return False
        else:
            return True


class ProcessCombine(QObject):
    """
    Scans through the gpx files and initialize the GpxToFeature tool to import
    to create the features and finally combine the features as a single layer.
    """
    progress = pyqtSignal(str)

    def __init__(self, parent):
        """
        Initializes the processCombine
        :param parent: The parent of QObject
        :type parent: QWidget
        """
        QObject.__init__(self, parent)
        self._parent = parent
        self.init_progress_dialog()
        self.layer_fields = None
        global ID_NUMBER
        ID_NUMBER = 0
        global STOP_IMPORT
        STOP_IMPORT = False
        self.number_of_gpx_files = 0

    def init_progress_dialog(self):
        """
        Initializes the progress dialog.
        """
        self.progress_dlg = QProgressDialog(self._parent)
        self.progress_dlg.resize(340, self.progress_dlg.height())
        title = QApplication.translate('ProcessCombine', 'Importing...')
        self.progress_dlg.setWindowTitle(title)
        label = QLabel()
        label.setWordWrap(True)
        label.setMinimumHeight(17)
        self.progress_dlg.setMinimumWidth(500)
        self.progress_dlg.setMaximumWidth(500)
        self.progress_dlg.setLabel(label)
        self.progress_dlg.setValue(0)
        self.progress_dlg.canceled.connect(self.on_stop_importing)
        self.progress_dlg.open()

    @staticmethod
    def on_stop_importing():
        """
        A slot raised to stops the importing process. This happens when the
        progress dialog cancel button is clicked.
        """
        global STOP_IMPORT
        STOP_IMPORT = True

    def on_update_progress(self, progress):
        """
        A slot raised used to update the progress by emitting progress message
        from GpxToFeature signal called progress.
        :param progress: The progress message.
        :type progress: String
        """
        self.progress.emit(progress)

    def gpx_to_feature_list(self, parm_store):
        """
        Gets QgsFeature list by supplying gpx files.
        :param parm_store: The parameter store object
        :type parm_store: Class
        """
        feature_list = []
        for dir_path, sub_dirs, files in os.walk(parm_store.input_path):

            QApplication.processEvents()
            if STOP_IMPORT:
                return None
            # Exclude sub-folders if user have chosen not to scan sub-folders
            if not parm_store.scan_sub_folders:
                if dir_path != parm_store.input_path:
                    continue

            gpx_files = glob.glob('{0}/{1}*{2}.gpx'.format(
                dir_path,
                parm_store.file_name_prefix,
                parm_store.file_name_suffix
            ))
            gpx_count = len(gpx_files)
            if gpx_count == 0:
                continue
            self.number_of_gpx_files += gpx_count
            self.progress_dlg.setRange(0, len(gpx_files))

            for i, gpx_file in enumerate(gpx_files):
                QApplication.processEvents()
                if STOP_IMPORT:
                    return None
                gpx_path = os.path.join(dir_path, gpx_file)
                parent_path = os.path.dirname(parm_store.input_path)
                relative_path = os.path.relpath(gpx_path, parent_path)
                scanning = QApplication.translate('ProcessCombine',
                                                  'Scanning')

                text = '{} {}'.format(scanning, relative_path)

                self.progress_dlg.setLabelText(text)

                gpx_to_layer = GpxToFeature(parm_store)
                gpx_to_layer.progress.connect(self.on_update_progress)
                gpx_to_layer.init_gpx_import(gpx_path)
                if not STOP_IMPORT:
                    self.progress_dlg.setValue(i)
                # fet layer fields once
                if len(gpx_to_layer.final_features) > 0:
                    if self.layer_fields is None:
                        self.layer_fields = gpx_to_layer.layer_fields
                    feature_list.extend(gpx_to_layer.final_features)

        return feature_list

    def combine_features(self, parm_store):
        """
        Combines all features under one layer.
        :param parm_store: The parameter store object
        :type parm_store: Class
        :return:
        :rtype:
        """
        final_layer = QgsVectorLayer(
            "{0}?crs=epsg:{1}&field=id:integer&index=yes".format(
                parm_store.geometry_type, parm_store.gpx_projection
            ),
            parm_store.layer_name,
            "memory"
        )

        feature_list = self.gpx_to_feature_list(parm_store)

        if self.layer_fields is None:
            self.progress_dlg.blockSignals(True)
            self.progress_dlg.close()
            self.progress_dlg.blockSignals(False)
            return 0
        if STOP_IMPORT:
            return
        provider = final_layer.dataProvider()

        final_layer.startEditing()
        provider.addAttributes(self.layer_fields)
        final_layer.updateFields()
        provider.addFeatures(feature_list)
        final_layer.commitChanges()

        final_layer.updateExtents()
        QgsProject.instance().addMapLayer(final_layer)
        return len(feature_list)

    def finish_import(self, parm_store):
        """
        Finishes the import process.
        :param parm_store: The parameter store object
        :type parm_store: Class
        :return: None if the process is aborted or number_features is None
        :rtype: NoneType
        """

        number_of_features = self.combine_features(parm_store)
        if STOP_IMPORT:
            abort_text = QApplication.translate(
                'ProcessCombine',
                '<html><b>The importing process is aborted!</b></html>'
            )
            self.progress.emit(abort_text)
            return
        if number_of_features is None:
            return
        if number_of_features < 1:
            end_text = QApplication.translate(
                'ProcessCombine',
                '<html><b>Sorry, no valid GPX features found '
                'in the folder!</b</html>'
            )
            self.progress.emit(end_text)
            self.progress_dlg.cancel()
            return

        self.copy_gpx_files(VALID_GPX_FILES, parm_store.valid_gpx_folder)
        self.copy_gpx_files(INVALID_GPX_FILES, parm_store.invalid_gpx_folder)

        self.progress_dlg.cancel()
        a = QApplication.translate('ProcessCombine',
                                   '<html><b>Successfully imported')
        c = QApplication.translate('ProcessCombine', 'features from')
        d = QApplication.translate('ProcessCombine', 'gpx files!<br>')
        e = QApplication.translate('ProcessCombine',
                                   'You can view the result in')
        g = QApplication.translate('ProcessCombine', 'layer.</b</html>')
        end_text = '{} {} {} {} {} {} {} {}'.format(
            a, number_of_features, c, self.number_of_gpx_files, d, e,
            parm_store.layer_name, g
        )
        self.progress.emit(end_text)

    @staticmethod
    def copy_gpx_files(source_files, destination_folder):
        """
        Copies gpx files from a source folder to a destination folder.
        :param source_files: The source folder
        :type source_files: String
        :param destination_folder: The destination folder
        :type destination_folder: String
        """
        for gpx_path in source_files:
            gpx_file = os.path.basename(gpx_path)
            destination = os.path.join(destination_folder, gpx_file)
            QApplication.processEvents()
            shutil.copyfile(gpx_path, destination)
