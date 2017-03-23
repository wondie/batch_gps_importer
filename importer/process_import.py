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
from PyQt4.QtCore import QObject
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
from gpx_util import GPXUtil
VALID_GPX_FILES = []
INVALID_GPX_FILES = []
ID_NUMBER = 0
FEATURE_TYPES = OrderedDict([
    (u'tracks', 'Track'), (u'waypoints', 'Waypoint'), (u'routes', 'Routes')
])
GEOMETRY_TYPES = OrderedDict([
    ('Polygon', 'Polygon'), ('Point', 'Point'), ('Linestring', 'Line')
])
GPX_FIELDS = OrderedDict([
    ('ele', 'elevation'), ('name', 'name'), ('cmt', 'comment'),
    ('desc', 'description'), ('url', 'url'), ('urlname', 'url_name'),
    ('sym', 'symbol'), ('src', 'source'), ('type', 'type'),
    ('time', 'capture_time'), ('feature_type', 'feature_type'),
    ('file_name', 'file_name')
])


class ParamStore:
    def __init__(self):
        self.input_path = None
        self.geometry_type = None
        self.feature_types = None
        self.gpx_projection = None
        self.required = None
        self.extent_bound = None
        self.extent_bound_enabled = False
        self.exclude_with_error = False
        self.exclude_with_few_points = False
        self.scan_sub_folders = True
        self.valid_gpx_folder = None
        self.invalid_gpx_folder = None
        self.layer_name = 'final_layer'
        self.excluded_fields = []
        self.iface = None

    def set_required(self):
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
        self.feature_points = {
            'tracks':'trkpt', 'routes':'rtept', 'waypoints':'wpt'
        }
        self.xml_feature_types = {
            'tracks':'trk', 'routes':'rte', 'waypoints':'wpt'
        }




    def init_gpx_import(self, gpx_path):
        # Open GPX file
        if self._file_is_readable(gpx_path):
            self.gpx_file_name = os.path.basename(gpx_path)
            self.file_name = self.gpx_file_name.rstrip('.gpx')
            self.gpx_path = gpx_path
            self.gpx_util = GPXUtil(self.gpx_path)

            data_source = ogr.Open(gpx_path)
            if data_source is not None:
                for feature_type in self.feature_types:
                    self.feature_type = feature_type.encode('utf-8')
                    self.ogr_layer = data_source.GetLayerByName(
                        self.feature_type
                    )


                    if self.ogr_layer.GetFeatureCount() > 0:
                        # try:
                        self.gpx_to_point_list()

                        # except Exception as ex:
                        #     self.error_type = ex.message
                        #     self.add_progress()
                        self.save_valid_folders()
                        self.save_invalid_folders()

    def get_point_attribute(self):

        feature_node_elements = self.gpx_util.gpx_feature_by_name(
            self.xml_feature_types[self.feature_type]
        )
        point_attributes = {}
        node = feature_node_elements.keys()[0]
        point_nodes = node.toElement().elementsByTagName(self.xml_feature_types[self.feature_type])
        for i in range(point_nodes.count()):
            attribute_node = point_nodes.at(i)
            attribute_element = attribute_node.toElement()
            #print attribute_element.attribute(field)
            #attribute_nodes = attribute_element.elementsByTagName(field)
            print attribute_element.tagName(), attribute_element.text()
            # for i in range(attribute_nodes.count()):
            #     attribute_node = attribute_nodes.at(i)
            #     attr_value = attribute_node.toElement().text()
            #
            #     point_attributes[field] = attr_value
                #print field, attr_value




        #self._current_attribute = point_attributes[field]
            # for ele in attribute_node.firstChildElement():
            #     print ele
            # print attribute_element.tagName()
            # attr_value = attribute_element.text()
            # point_attribute.append(attr_value)
       # print point_attribute
        # attribute_nodes = element.elementsByTagName(field)
        #
        # for i in range(attribute_nodes.count()):
        #     attribute_node = attribute_nodes.at(i)
        #     # get the value element
        #
        #
        #     attribute_element = attribute_node.toElement()
        #
        #     attr_value = attribute_element.text()
        #     point_attribute.append(attr_value)
       # print point_attribute
        #
        # for node, ele in nodes:
        #     print ele.text()
        #
        #     route_point_nodes = self.gpx_util.find_gpx_node(
        #         self.feature_points[self.feature_type]
        #     )
        #     for route_point_node in route_point_nodes:
        #         names = route_point_node.toElement().elementsByTagName(field)
        #         for i in range(names.count()):
        #             name = names.at(i)
        #             attr_value = name.toElement().text()
        #             point_attribute[j] = {field: attr_value}
        #
        # print point_attribute

    def _file_is_readable(self, gpx_path):
        """
        Checks if the gpx file is readable.
        :return: True if it is a file and readable otherwise return False.
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
        self.extract_geometry()

        if len(self.gpx_data) < 1:
            return
        self.create_polygon()
        self.create_point()
        self.create_line()

        self.add_progress()

    def save_valid_folders(self):
        if len(self.valid_gpx_folder) > 2:
            if self.error_type is None:
                VALID_GPX_FILES.append(self.gpx_path)

    def save_invalid_folders(self):
        if len(self.invalid_gpx_folder) > 2:
            if self.error_type is not None:
                INVALID_GPX_FILES.append(self.gpx_path)

    def extract_geometry(self):
        self.gpx_data.clear()
        for i, ogr_feature in enumerate(self.ogr_layer):
            if ogr_feature is None:
                continue

            field_attributes = self.extract_attributes(ogr_feature)
            geom = ogr_feature.GetGeometryRef()
            wkt = geom.ExportToWkt()
            qgs_geom = QgsGeometry.fromWkt(wkt)

            qgs_geom.convertToMultiType()

            if self.feature_type == 'waypoints':
                point = qgs_geom.asMultiPoint()
                self.gpx_data[point[0]] = field_attributes
            else:
                points = qgs_geom.asMultiPolyline()
                for point in points[0]:
                    self.gpx_data[point] = field_attributes

    def extract_attributes(self, ogr_feature):
        """
        Extracts the attributes of a feature.
        :param ogr_feature: The gpx feature
        :type ogr_feature: ogr.Feature
        :return: Dictionary of fields and attributes as key and value.
        :rtype: OrderedDict
        """

        field_attributes = OrderedDict()

        for original_field, final_field in GPX_FIELDS.iteritems():
            QApplication.processEvents()
            try:
                if final_field in self.excluded_fields:
                    continue
                if original_field not in ['file_name', 'feature_type']:
                    attribute = ogr_feature.GetField(original_field)
                    self.get_point_attribute()
                    field_attributes[final_field] = self._current_attribute

                elif original_field == 'feature_type':
                    field_attributes['feature_type'] = self.feature_type
                else:
                    if final_field == 'file_name':
                        field_attributes['file_name'] = self.gpx_file_name
            except Exception:
                field_attributes[final_field] = None

        return field_attributes

    def create_line(self):
        if self.geometry_type == 'Linestring':
            line_geom = QgsGeometry.fromPolyline(self.gpx_data.keys())
            attributes = self.gpx_data.values()[0]

            # validate_insufficient_points
            if not self.validate_insufficient_points(self.gpx_data.keys(), 2):
                return
            # remove the ungroupped dictionary
            self.gpx_data.clear()
            if self.validate_geometry(line_geom):
                self.gpx_data[line_geom] = attributes
                self.create_feature(line_geom, self.gpx_data.values()[0])

    def create_point(self):
        if self.geometry_type == 'Point':
            invalid_geom = []
            for points, attributes in self.gpx_data.iteritems():
                QApplication.processEvents()
                point_geom = QgsGeometry.fromPoint(points)
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
        if self.geometry_type == 'Polygon':
            poly_geom = QgsGeometry.fromPolygon([self.gpx_data.keys()])
            attributes = self.gpx_data.values()[0]
            # update the gpx_data to contain polygon geometry as a key and
            # and only the first attributes
            if not self.validate_insufficient_points(self.gpx_data.keys(), 3):
                return
            # remove the ungroupped dictionary
            self.gpx_data.clear()
            if self.validate_geometry(poly_geom):
                self.gpx_data[poly_geom] = attributes

                self.create_feature(
                    poly_geom, self.gpx_data[self.gpx_data.keys()[0]]
                )

    def create_feature(self, gpx_geom, attributes):

        global ID_NUMBER
        ID_NUMBER += 1
        for field in attributes.keys():
            self.layer_fields.append(QgsField(field, QVariant.String))
        feature = QgsFeature()
        feature.setGeometry(gpx_geom)

        feature.setAttributes(
            [ID_NUMBER] + attributes.values()
        )

        bounding_box = gpx_geom.boundingBox()
        if self.validate_extent(bounding_box):
            self.final_features.append(feature)

    def add_progress(self):
        QApplication.processEvents()
        if len(self.final_features) == 0:
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

    def validate_insufficient_points(self, geoms, point_counts):
        error_state = True
        if self.exclude_with_few_points:

            if len(geoms) < point_counts:
                self.error_type = QApplication.translate(
                    'GpxToFeature',
                    'Insufficient points to create a valid {}'.
                        format(GEOMETRY_TYPES[self.geometry_type])
                )
                error_state = False
                return error_state
            else:
                return error_state
        else:
            return error_state

    def validate_geometry(self, geom, suppress_errors=False):
        if self.exclude_with_error:
            errors = geom.validateGeometry()
            if len(errors) == 0:
                return True
            else:
                if not suppress_errors:
                    error_desc = [er.what() for er in errors]
                    self.error_type = QApplication.translate(
                        'GpxToFeature', ' '.join(error_desc)
                    )
                return False
        else:
            return True

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
        self.layer_fields = None
        global ID_NUMBER
        ID_NUMBER = 0

    def init_progress_dialog(self):

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
            # Exclude sub-folders if user have chosen not to scan sub-folders
            if not parm_store.scan_sub_folders:
                if dir_path != parm_store.input_path:
                    continue
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
                if not self.stop_import:
                    self.progress_dlg.setValue(i)
                # fet layer fields once
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
            parm.layer_name,
            "memory"
        )
        feature_list = self.gpx_to_feature_list(parm)
        if self.layer_fields is None:
            # TODO fix the cause of abort message dure to failure of blocksignal
            self.blockSignals(True)
            self.progress_dlg.close()
            self.blockSignals(False)
            return None
        if self.stop_import:
            return None
        provider = final_layer.dataProvider()
        final_layer.startEditing()

        provider.addAttributes(self.layer_fields)

        final_layer.updateFields()
        provider.addFeatures(feature_list)

        final_layer.commitChanges()
        final_layer.updateExtents()
        QgsMapLayerRegistry.instance().addMapLayer(final_layer)
        return len(feature_list)

    def finish_import(self, param):
        number_of_features = self.combine_layers(param)
        if self.stop_import:
            abort_text = QApplication.translate(
                'ProcessCombine',
                '<html><b>The importing process is aborted!</b</html>'
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
            self.progress_dlg.blockSignals(True)
            self.progress_dlg.cancel()
            self.progress_dlg.blockSignals(False)
            return

        self.copy_gpx_files(VALID_GPX_FILES, param.valid_gpx_folder)
        self.copy_gpx_files(INVALID_GPX_FILES, param.invalid_gpx_folder)

        self.progress_dlg.cancel()
        end_text = QApplication.translate(
            'ProcessCombine',
            '<html><b>Successfully imported {} features!</b</html>'.format(
                number_of_features
            )
        )
        self.progress.emit(end_text)

    @staticmethod
    def copy_gpx_files(source_files, destination_folder):
        for gpx_path in source_files:
            gpx_file = os.path.basename(gpx_path)
            destination = os.path.join(destination_folder, gpx_file)
            shutil.copyfile(gpx_path, destination)
