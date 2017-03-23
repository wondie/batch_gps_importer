from collections import OrderedDict
from PyQt4.QtCore import QFile
from PyQt4.QtXml import QDomDocument

class GPXUtil():

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

    def set_attribute_to_nodes(self, nodes, attr, value):
        """
        Sets an attribute with value to node lists.
        :param nodes: List of nodes
        :type nodes: QNodeList
        :param attr: The attribute text
        :type attr: String
        :param value: The value of the attribute.
        :type value: String
        :return:
        :rtype:
        """
        for node in nodes:
            element = node.toElement()
            element.setAttribute(attr, value)

    def set_attribute_by_node_name(self, node_name, attr, value):
        """
        Sets attribute with value to nodes by node name.
        :param node_name: The name of the node.
        :type node_name: Strong
        :param attr: The attribute text
        :type attr: String
        :param value: The value of the attribute.
        :type value: String
        :return:
        :rtype:
        """
        nodes = self.find_gpx_node(node_name)
        self.set_attribute_to_nodes(nodes, attr, value)

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
