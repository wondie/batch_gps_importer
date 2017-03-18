import re
import os

from PyQt4.QtCore import QObject
from PyQt4.QtCore import QVariant, pyqtSignal
from PyQt4.QtGui import QApplication
from qgis.core import (
    QgsGeometry,
    QgsFeature,
    QgsPoint,
    QgsVectorLayer,
    QgsRectangle,
    QgsField
)
from qgis.core import QgsMapLayerRegistry

from osgeo import ogr

USED_GPX_FILES = []

class ParamStore:
    def __init__(self):
        self.input_path = None
        self.layer_name = None
        self.geometry_type = None
        self.feature_type = None
        self.gpx_projection = None
        self.required = None
        self.layer_name = None
        self.extent_bound = None
        self.extent_bound_enabled = False
        self.exclude_with_error = False
        self.iface = None

    def set_required(self):
        self.required = [self.input_path, self.geometry_type]

class GpxToLayer(QObject):
    progress = pyqtSignal(str)
    def __init__(self, param_store, gpx_file):

        self.iface = param_store.iface
        QObject.__init__(self, self.iface.mainWindow())
        self.map_canvas = self.iface.mapCanvas()
        self.input_path = param_store.input_path
        self.feature_type = param_store.feature_type
        self.geometry_type = param_store.geometry_type
        self.gpx_projection = param_store.gpx_projection
        self.layer_name = param_store.layer_name
        self.extent_bound_enabled = param_store.extent_bound_enabled
        self.gpx_file_name = os.path.basename(gpx_file)
        self.gpx_path = os.path.join(self.input_path, gpx_file)
        self.file_name = self.gpx_file_name.rstrip('.gpx')
        self.exclude_with_error = param_store.exclude_with_error
        self.extent_bound = param_store.extent_bound
        self.gpx_layer = None
        self.gpx_layers = []
        self.error_type = None

    def validate_file_path(self, gpx_file):
        """
        Validate source file path since the user is allowed to type in the path
        :param gpx_file: Input GPX file
        :return: True if file path is valid and None when not valid
        :rtype: Boolean
        """
        if gpx_file:
            reg_ex = re.compile(
                r'^(([a-zA-Z]:)|((\\|/){1,2}\w+)\$?)((\\|/)(\w[\w ]*.*))+\.(gpx)$')
            return True if reg_ex.search(gpx_file) and self._file_readable(
                gpx_file) else None
        return None

    def init_gpx(self, gpx_file):
        # Open GPX file
        if self.validate_file_path(gpx_file):

            data_source = ogr.Open(gpx_file)

            if data_source is not None:
                self.feature_type = self.feature_type.encode('utf-8')
                self.gpx_feature = data_source.GetLayerByName(self.feature_type)
                self.gpx_to_point_list()

    def _file_readable(self, file_path):
        """
        Checks if source file is readable.
        :param file_path: Full file path
        :return: True if it is a file and readable at
                 the same time. otherwise return None
        :rtype: Boolean
        """
        try:
            return None if not os.path.isfile(file_path) and not os.access(
                file_path, os.R_OK) else True
        except IOError as ex:
           print ("I/O error({0}): {1}".format(ex.errno, ex.strerror))

    def gpx_to_point_list(self):

        point_list = []
        self.extract_from_waypoints(point_list)
        self.extract_from_tracks(point_list)
        self.extract_from_routes(point_list)
        # TODO Add logic for auto detect feature type

        if len(point_list) < 1:
            return
        self.create_polygon(point_list)

        self.create_point(point_list)

        self.create_line(point_list)
        self.add_progress()

    def extract_from_routes(self, point_list):
        if self.feature_type == 'routes':
            for row in self.gpx_feature:
                # Get point lon lat from GPX file
                geom = row.GetGeometryRef()
                points = geom.GetPointCount()
                for p in xrange(points):
                    lon, lat, z = geom.GetPoint(p)
                    gpx_layer_point = QgsPoint(lon, lat)
                    point_list.append(gpx_layer_point)

    def extract_from_tracks(self, point_list):
        if self.feature_type == 'tracks':
            row = self.gpx_feature.GetFeature(0)
            if row is not None:
                geom = row.GetGeometryRef()
                wkt = geom.ExportToWkt()
                qgs_geom = QgsGeometry.fromWkt(wkt)
                line_list = qgs_geom.asMultiPolyline()[0]
                for point in line_list:
                    gpx_layer_point = QgsPoint(point[0], point[1])
                    point_list.append(gpx_layer_point)

    def extract_from_waypoints(self, point_list):
        if self.feature_type == 'waypoints':
            for row in self.gpx_feature:
                # Get point lon lat from GPX file
                lon, lat, ele = row.GetGeometryRef().GetPoint()
                gpx_layer_point = QgsPoint(lon, lat)
                point_list.append(gpx_layer_point)

    def create_line(self, point_list):
        if self.geometry_type == 'Linestring':

            poly_geom = QgsGeometry.fromPolyline(point_list)

            if self.exclude_with_error:
                if poly_geom.isGeosValid():
                    self.create_feature_layer(poly_geom)
                else:
                    self.error_type = QApplication.translate(
                        'GpxToLayer', 'geometry'
                    )
            else:
                self.create_feature_layer(poly_geom)

    def create_point(self, point_list):
        if self.geometry_type == 'Point':
            valid_geom = []
            for point in point_list:
                point_geom = QgsGeometry.fromPoint(point)
                if self.exclude_with_error:
                    if point_geom.isGeosValid():
                        self.create_feature_layer(point_geom)
                        valid_geom.append(point_geom)
                else:
                    valid_geom.append(point_geom)
                    self.create_feature_layer(point_geom)
            if len(valid_geom) == 0:
                self.error_type = QApplication.translate(
                    'GpxToLayer', 'geometry'
                )

    def create_polygon(self, point_list):
        if self.geometry_type == 'Polygon':
            poly_geom = QgsGeometry.fromPolygon([point_list])
            if self.exclude_with_error:
                if poly_geom.isGeosValid():
                    self.create_feature_layer(poly_geom)
                else:
                    self.error_type = QApplication.translate(
                        'GpxToLayer', 'geometry'
                    )
            else:
                self.create_feature_layer(poly_geom)

    def add_progress(self):
        if len (self.gpx_layers) == 0:
            if self.error_type is not None:
                error_message = QApplication.translate(
                    'GpxToLayer',
                    'Found {} error in {}'.format(
                        self.error_type, self.gpx_file_name
                    )
                )
                self.progress.emit(error_message)
        else:
            success_message = QApplication.translate(
                'GpxToLayer',
                'Created feature(s) for {}'.format(self.gpx_file_name)
            )
            self.progress.emit(success_message)

    def create_feature_layer(self, gpx_geom):
        # create memory layer
        gpx_layer = QgsVectorLayer(
            "{0}?crs=epsg:{1}&field=id:integer&index=yes".format(
                self.geometry_type, self.gpx_projection
            ),
            'temp',
            "memory"
        )
        provider = gpx_layer.dataProvider()
        gpx_layer.startEditing()
        # add fields
        provider.addAttributes([
            QgsField("id", QVariant.Int),
            QgsField("file_name", QVariant.String),
            QgsField("area", QVariant.Double)
        ])
        area = float(format(gpx_geom.area(), '.6f'))

        feature = QgsFeature()
        feature.setGeometry(gpx_geom)
        USED_GPX_FILES.append(self.gpx_file_name)
        feature.setAttributes(
            [len(USED_GPX_FILES), self.file_name, area]
        )
        QApplication.processEvents()

        provider.addFeatures([feature])
        gpx_layer.commitChanges()
        #QgsMapLayerRegistry.instance().addMapLayer(gpx_layer)

        if self.validate_extent(gpx_layer):
            self.gpx_layers.append(gpx_layer)
            self.gpx_layer = gpx_layer

    def validate_extent(self, gpx_layer):
        extent_rect = gpx_layer.extent()
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

    def update_progress(self, progress):
        self.progress.emit(progress)

    def from_gpx_to_layers(self, parm_store):
        layer_list = []
        for dir_path, sub_dirs, files in os.walk(parm_store.input_path):
            for gpx_file in files:
                gpx_to_layer = GpxToLayer(parm_store, gpx_file)
                gpx_to_layer.progress.connect(self.update_progress)
                gpx_path = os.path.join(dir_path, gpx_file)
                gpx_to_layer.init_gpx(gpx_path)
                if len(gpx_to_layer.gpx_layers) > 0:
                    for layer in gpx_to_layer.gpx_layers:
                        layer_list.append(layer)
        return layer_list

    def combine_layers(self, parm_store):
        parm = parm_store
        final_layer = QgsVectorLayer(
            "{0}?crs=epsg:{1}&field=id:integer&index=yes".format(
                parm.geometry_type, parm.gpx_projection
            ),
            "final_layer",
            "memory"
        )
        layer_list = self.from_gpx_to_layers(parm)
        if len(layer_list) == 0:
            return
        provider = final_layer.dataProvider()
        final_layer.startEditing()

        for gpx_layer in layer_list:
            fields = gpx_layer.pendingFields()
            for field in fields:
                provider.addAttributes([field])
            final_layer.updateFields()
            for feat in gpx_layer.getFeatures():
                provider.addFeatures([feat])

        final_layer.commitChanges()
        final_layer.updateExtents()
        QgsMapLayerRegistry.instance().addMapLayer(final_layer)

