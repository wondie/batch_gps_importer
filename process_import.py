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
import re
from collections import OrderedDict
import os

from PyQt4.QtCore import QObject
from PyQt4.QtCore import QThread
from PyQt4.QtCore import QVariant, pyqtSignal
from PyQt4.QtGui import QApplication
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QProgressDialog
from qgis.core import (
    QgsGeometry,
    QgsFeature,
    QgsPoint,
    QgsPointV2,
    QgsVectorLayer,
    QgsRectangle,
    QgsField
)
from qgis.core import QgsMapLayerRegistry

from osgeo import ogr

USED_GPX_FILES = []
FEATURE_TYPES = OrderedDict([
    (u'tracks', 'Track'), (u'waypoints', 'Waypoint'), (u'routes', 'Routes')
])
GEOMETRY_TYPES = OrderedDict([
    ('Polygon', 'Polygon'), ('Point', 'Point'), ('Linestring', 'Line')
])


class ParamStore:
    def __init__(self):
        self.input_path = None
        self.layer_name = None
        self.geometry_type = None
        self.feature_types = None
        self.gpx_projection = None
        self.required = None
        self.layer_name = None
        self.extent_bound = None
        self.extent_bound_enabled = False
        self.exclude_with_error = False
        self.iface = None

    def set_required(self):
        self.required = [self.input_path, self.geometry_type]

class GpxToFeature(QObject):
    progress = pyqtSignal(str)
    def __init__(self, param_store):

        self.iface = param_store.iface
        QObject.__init__(self, self.iface.mainWindow())
        self.map_canvas = self.iface.mapCanvas()
        self.input_path = param_store.input_path
        self.feature_types = param_store.feature_types
        self.feature_type = None
        self.geometry_type = param_store.geometry_type
        self.gpx_projection = param_store.gpx_projection
        self.layer_name = param_store.layer_name
        self.extent_bound_enabled = param_store.extent_bound_enabled
        self.gpx_file_name = None
        self.gpx_path = None
        self.file_name = None
        self.exclude_with_error = param_store.exclude_with_error
        self.extent_bound = param_store.extent_bound
        self.gpx_fields =OrderedDict([
            ('ele', 'elevation'), ('name', 'name'), ('cmt', 'comment'),
            ('desc', 'description'), ('url', 'url'), ('urlname', 'url_name'),
            ('sym', 'symbol'), ('src', 'source'), ('type', 'type'),
            ('time', 'capture_time'), ('file_name', 'file_name')
        ])
        # TODO add scan sub-folder option
        # TODO exclude/invalid features
        # TODO included and excluded folders

        self.layer_fields = []
        self.final_features = []
        self.error_type = None
        self.ogr_layer = None
        self.gpx_data = OrderedDict()

    def init_gpx_import(self, gpx_path):
        # Open GPX file
        if self._file_is_readable(gpx_path):
            self.gpx_file_name = os.path.basename(gpx_path)
            self.file_name = self.gpx_file_name.rstrip('.gpx')
            self.gpx_path = gpx_path
            data_source = ogr.Open(gpx_path)
            if data_source is not None:
                for feature_type in self.feature_types:
                    self.feature_type = feature_type.encode('utf-8')
                    self.ogr_layer = data_source.GetLayerByName(
                        self.feature_type
                    )

                    if self.ogr_layer.GetFeatureCount() > 0:
                        #try:
                        self.gpx_to_point_list()
                        # except Exception as ex:
                        #     self.error_type = ex.message
                        #     self.add_progress()

    def _file_is_readable(self, gpx_path):
        """
        Checks if the gpx file is readable.

        :return: True if it is a file and readable at
                 the same time. otherwise return None
        :rtype: Boolean
        """
        try:
            if not os.access(gpx_path, os.R_OK):
                return False
            else:
                return True
        except Exception as ex:
            self.error_type = ex

    def gpx_to_point_list(self):
        self.extract_from_waypoints()
        self.extract_from_tracks()
        self.extract_from_routes()

        if len(self.gpx_data) < 1:
            return
        self.create_polygon()
        self.create_point()
        self.create_line()

        self.add_progress()

    def extract_from_routes(self):
        if self.feature_type == 'routes':
            for ogr_feature in self.ogr_layer:
                # Get point lon lat from GPX file
                if ogr_feature is None:
                    return

                field_attributes = self.extract_attributes(ogr_feature)
                geom = ogr_feature.GetGeometryRef()
                wkt = geom.ExportToWkt()
                qgs_geom = QgsGeometry.fromWkt(wkt)
                points = geom.GetPointCount()
                if self.geometry_type in ['Polygon', 'Point']:
                    for p in xrange(points):
                        lon, lat, z = geom.GetPoint(p)
                        gpx_layer_point = QgsPoint(lon, lat)
                        self.gpx_data[gpx_layer_point] = field_attributes
                else:
                    self.gpx_data[qgs_geom] = field_attributes

    def extract_from_tracks(self):
        if self.feature_type == 'tracks':
            for ogr_feature in self.ogr_layer:

                if ogr_feature is None:
                    continue

                field_attributes = self.extract_attributes(ogr_feature)
                geom = ogr_feature.GetGeometryRef()
                wkt = geom.ExportToWkt()
                qgs_geom = QgsGeometry.fromWkt(wkt)

                if self.geometry_type in ['Polygon','Point']:
                    point_list = []
                    line_list = qgs_geom.asMultiPolyline()[0]
                    for point in line_list:
                        gpx_layer_point = QgsPoint(point[0], point[1])
                        point_list.append(gpx_layer_point)
                        self.gpx_data[gpx_layer_point] = field_attributes
                else:
                    self.gpx_data[qgs_geom] = field_attributes

    def extract_from_waypoints(self):
        if self.feature_type == 'waypoints':
            for ogr_feature in self.ogr_layer:
                if ogr_feature is None:
                    return

                field_attributes = self.extract_attributes(ogr_feature)
                geom = ogr_feature.GetGeometryRef()
                wkt = geom.ExportToWkt()
                qgs_geom = QgsGeometry.fromWkt(wkt)
                # Get point lon lat from GPX file
                if self.geometry_type in ['Polygon', 'Linestring']:
                    lon, lat, ele = ogr_feature.GetGeometryRef().GetPoint()
                    # TODO fix the decimal places length
                    # TODO consider using QgsPointV2
                    gpx_layer_point = QgsPoint(lon, lat)
                    self.gpx_data[gpx_layer_point] = field_attributes
                else:
                    self.gpx_data[qgs_geom] = field_attributes

    def extract_attributes(self, ogr_feature):
        """
        Extracts the attributes of a feature.
        :param ogr_feature: The gpx feature
        :type ogr_feature: ogr.Feature
        :return: Dictionary of fields and attributes as key and value.
        :rtype: OrderedDict
        """
        field_attributes = OrderedDict()
        for original_field, final_field in self.gpx_fields.iteritems():
            QApplication.processEvents()
            try:
                if original_field != 'file_name':
                    attribute = ogr_feature.GetField(original_field)
                    field_attributes[final_field] = attribute
                else:
                    if final_field == 'file_name':
                        field_attributes['file_name'] = self.gpx_file_name
            except Exception:
                field_attributes[final_field] = None

        return field_attributes

    def create_line(self):
        if self.geometry_type == 'Linestring':
            QApplication.processEvents()

            qgs_points = [
                point for point in self.gpx_data.keys()
                if isinstance(point, QgsPoint)
            ]
            if len(self.gpx_data.keys()) < 2 and self.feature_type == 'waypoints':
                self.error_type = QApplication.translate(
                    'GpxToFeature', 'Insufficient points to '
                                  'create a valid {}'.
                        format(GEOMETRY_TYPES[self.geometry_type])
                )
                return

            for geom, attribute in self.gpx_data.iteritems():
                QApplication.processEvents()

                if isinstance(geom, QgsPoint):
                    geom = QgsGeometry.fromPolyline(qgs_points)

                if self.exclude_with_error:
                    errors = geom.validateGeometry()
                    if len(errors) == 0:
                        self.create_feature(geom, attribute)
                    else:
                        error_desc = [er.what() for er in errors]
                        self.error_type = QApplication.translate(
                            'GpxToFeature', ' '.join(error_desc)
                        )
                else:
                    self.create_feature(
                        geom, attribute
                    )
                if self.feature_type == 'waypoints':

                    break

    def create_point(self):
        if self.geometry_type == 'Point':
            invalid_geom = []
            errors = None
            for point_geom, attributes in self.gpx_data.iteritems():
                QApplication.processEvents()

                if isinstance(point_geom, QgsPoint):

                    point_geom = QgsGeometry.fromPoint(point_geom)

                if self.exclude_with_error:
                    errors = point_geom.validateGeometry()
                    if len(errors) == 0:
                        self.create_feature(point_geom, attributes)
                    else:
                        invalid_geom.append(point_geom)

                else:

                    self.create_feature(point_geom, attributes)

            if len(invalid_geom) > 0:
                if errors is None:
                    return
                error_desc = [er.what() for er in errors]
                self.error_type = QApplication.translate(
                    'GpxToFeature', ' '.join(error_desc)
                )

    def create_polygon(self):
        if self.geometry_type == 'Polygon':
            QApplication.processEvents()
            if len(self.gpx_data.keys()) < 3:
                self.error_type = QApplication.translate(
                    'GpxToFeature', 'Insufficient points to create a valid {}'.
                    format(GEOMETRY_TYPES[self.geometry_type])
                )
                return
            poly_geom = QgsGeometry.fromPolygon([self.gpx_data.keys()])
            if self.exclude_with_error:
                errors = poly_geom.validateGeometry()
                if len(errors) == 0:
                    self.create_feature(
                        poly_geom, self.gpx_data[self.gpx_data.keys()[0]]
                    )
                else:
                    error_desc = [er.what() for er in errors]
                    self.error_type = QApplication.translate(
                        'GpxToFeature', ' '.join(error_desc)
                    )

            else:
                self.create_feature(
                    poly_geom, self.gpx_data[self.gpx_data.keys()[0]]
                )

    def add_progress(self):
        QApplication.processEvents()
        if len (self.final_features) == 0:
            if self.error_type is not None:
                error_message = QApplication.translate(
                    'GpxToFeature',
                    '{} in {}'.format(
                        self.error_type, self.gpx_file_name
                    )
                )
                self.progress.emit(error_message)
        else:
            success_message = QApplication.translate(
                'GpxToFeature',
                'Created feature(s) for {}'.format(self.gpx_file_name)
            )
            self.progress.emit(success_message)

    def create_feature(self, gpx_geom, attributes):

        for field in attributes.keys():
            self.layer_fields.append(QgsField(field, QVariant.String))

        feature = QgsFeature()

        feature.setGeometry(gpx_geom)
        USED_GPX_FILES.append(self.gpx_file_name)

        feature.setAttributes(
            [len(USED_GPX_FILES)] + attributes.values()
        )

        bounding_box = gpx_geom.boundingBox()
        if self.validate_extent(bounding_box):
            self.final_features.append(feature)

    def validate_extent(self, extent_rect):

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

    progress = pyqtSignal(str)

    def __init__(self, parent):
        QObject.__init__(self, parent)
        self._parent = parent
        self.init_progress_dialog()
        self.stop_import = False

    def init_progress_dialog(self):
        self.layer_fields = None
        self.progress_dlg = QProgressDialog(self._parent)
        self.progress_dlg.resize(340, self.progress_dlg.height())
        title = QApplication.translate('ProcessCombine', 'Importing...')
        self.progress_dlg.setWindowTitle(title)
        self.progress_dlg.open()
        self.progress_dlg.setValue(0)
        self.progress_dlg.canceled.connect(self.stop_importing)
        label = QLabel()
        label.setWordWrap(True)
        label.setMinimumHeight(17)
        self.progress_dlg.setMaximumWidth(440)
        self.progress_dlg.setLabel(label)
        self.progress_dlg.open()

    def stop_importing(self):
        self.stop_import = True

    def update_progress(self, progress):
        self.progress.emit(progress)

    def gpx_to_feature_list(self, parm_store):
        feature_list = []
        parent_path = os.path.dirname(parm_store.input_path)
        for dir_path, sub_dirs, files in os.walk(parm_store.input_path):
            QApplication.processEvents()
            if self.stop_import:
                break
            relative_path = os.path.relpath(dir_path, parent_path)

            text = QApplication.translate(
                'ProcessCombine', 'Scanning {}'.format(relative_path)
            )
            self.progress_dlg.setLabelText(text)
            gpx_files = glob.glob('{}/*.gpx'.format(dir_path))
            if len(gpx_files) == 0:
                continue
            self.progress_dlg.setRange(0, len(gpx_files))

            for i, gpx_file in enumerate(gpx_files):
                QApplication.processEvents()
                if self.stop_import:
                    break
                gpx_path = os.path.join(dir_path, gpx_file)
                gpx_to_layer = GpxToFeature(parm_store)

                gpx_to_layer.progress.connect(self.update_progress)

                gpx_to_layer.init_gpx_import(gpx_path)
                self.progress_dlg.setValue(i)

                if len(gpx_to_layer.final_features) > 0:
                    if self.layer_fields is None:
                        self.layer_fields = gpx_to_layer.layer_fields
                    feature_list.extend(gpx_to_layer.final_features)

        return feature_list

    def combine_layers(self, parm_store):
        parm = parm_store
        final_layer = QgsVectorLayer(
            "{0}?crs=epsg:{1}&field=id:integer&index=yes".format(
                parm.geometry_type, parm.gpx_projection
            ),
            "final_layer",
            "memory"
        )

        feature_list = self.gpx_to_feature_list(parm)

        if self.stop_import:
            abort_text = QApplication.translate(
                'ProcessCombine',
                '<html><b>The importing process is aborted!</b</html>'
            )
            self.progress.emit(abort_text)
            return
        if feature_list is None:
            return
        if len(feature_list) < 1:
            end_text = QApplication.translate(
                'ProcessCombine',
                '<html><b>Sorry, no valid GPX features found '
                'in the folder!</b</html>'
            )
            self.progress.emit(end_text)
            self.progress_dlg.blockSignals(True)
            self.progress_dlg.cancel()
            self.progress_dlg.blockSignals(False)
            return

        provider = final_layer.dataProvider()
        final_layer.startEditing()

        provider.addAttributes(self.layer_fields)
        final_layer.updateFields()

        provider.addFeatures(feature_list)

        final_layer.commitChanges()
        final_layer.updateExtents()
        QgsMapLayerRegistry.instance().addMapLayer(final_layer)
        self.progress_dlg.cancel()
        end_text = QApplication.translate(
            'ProcessCombine',
            '<html><b>Successfully imported {} features!</b</html>'.format(
                len(feature_list)
            )
        )
        self.progress.emit(end_text)

