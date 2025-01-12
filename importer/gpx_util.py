from collections import OrderedDict
from PyQt5.QtCore import QFile
from PyQt5.QtWidgets import QApplication
from PyQt5.QtXml import QDomDocument

class GpxUtil():

    def __init__(self, gpx_path):
        """
        A utility class to read gpx file contents.
        :param gpx_path: The GPX file path
        :type gpx_path: String
        """
        self.gpx_path = gpx_path
        self.gpx_node_name = 'gpx'
        self.read_gpx_file()

    def read_gpx_file(self):
        """
        Reads the gpx file contents and creates QDomDocument version of it.
        """
        gpx_file_path = QFile(self.gpx_path)

        self.document = QDomDocument()
        status, msg, line, col = self.document.setContent(gpx_file_path)
        if status:
            self.gpx_element = self.document.documentElement()

    def find_gpx_node(self, name):
        """
        Get nodes inside a document by a tag name.
        :param name: The tag name
        :type name: String
        :return: The nodes list
        :rtype: List
        """
        node_list = self.document.elementsByTagName(name)
        nodes = []
        for i in range(node_list.length()):
            node = node_list.item(i)
            nodes.append(node)
        return nodes

    def gpx_feature_by_name(self, tag_name):
        """
        Gets the gpx feature by name with a specified tag name.
        :param tag_name: The tag name to be used to search the child.
        :type tag_name: String
        :return: Dictionary of parent node and the child element.
        :rtype: OrderedDict
        """
        gpx_nodes = self.find_gpx_node(self.gpx_node_name)
        first_child = OrderedDict()
        for gpx_node in gpx_nodes:
            gpx_child = gpx_node.firstChildElement(tag_name)
            first_child[gpx_node] = gpx_child
        return first_child

    def gpx_point_attributes(self, gpx_feature_name):
        node_list = self.find_gpx_node(gpx_feature_name)
        point_attributes = OrderedDict()
        QApplication.processEvents()

        for point_row, nod in enumerate(node_list):
            child = nod.childNodes()

            attribute = {}
            for i in range(child.length()):
                n = child.item(i)
                # print(n.nodeName(), n.toElement().text())
                attribute[n.nodeName()] = n.toElement().text()
            point_attributes[point_row] = attribute
        print (point_row, point_attributes)
        return point_attributes
