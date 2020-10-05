from io import StringIO

import os
import xml.etree.ElementTree as ET

from xml.dom import minidom

WILDCARD_CHAR = '*'
STUF_WILDCARD_CHAR = '%'


class StufMessage:
    """Workable representation of a StUF message, based on ElementTree.

    If namespaces is not defined this class builds namespaces based on the input message to keep the representation
    consistent and readable, and to make searching through a known XML string easier.
    """

    def __init__(self, msg: str, namespaces=None):
        self.namespaces = namespaces
        self.tree = None
        self.load(msg)

    def load(self, msg: str):
        if not self.namespaces:
            self.set_namespaces(msg)
        self.tree = ET.fromstring(msg)

    def set_namespaces(self, msg):
        self.namespaces = dict([node for _, node in ET.iterparse(StringIO(msg), events=['start-ns'])])

        for prefix, url in self.namespaces.items():
            ET.register_namespace(prefix, url)

    def find_elm(self, elements_str: str, tree=None):
        """Returns the first element in tree. Tree defaults to the message root.

        Accepts element paths as well as a single element.

        Example:
            find_elm('a b c') finds the first element c in the tree a -> b -> c
            find_elm('a', sometree) finds the first element 'a' in sometree

        :param elements_str:
        :param tree:
        :return:
        """
        if tree is None:
            tree = self.tree

        elements = elements_str.split(' ')
        elm = tree.find(elements[0], self.namespaces)

        if len(elements) > 1:
            next_elements = " ".join(elements[1:])
            return self.find_elm(next_elements, elm)
        else:
            return elm

    def find_all_elms(self, elements_str: str, tree=None):
        """Returns all elements matching elements_str that are children from the first parent found.

        If elements_str is 'a b c d', then the first element matching 'a b c' is found. Then all children d of this
        element are returned.

        :param elements_str:
        :param tree:
        :return:
        """
        elements = elements_str.split(' ')

        if len(elements) > 1:
            parent = self.find_elm(' '.join(elements[:-1]))
        else:
            parent = tree or self.tree

        if parent is None:
            return []
        return parent.findall(elements[-1], self.namespaces)

    def set_elm_value(self, elements_str: str, value: str, exact_match=True, tree=None):
        """Set the value of the first element identified by elements_str.

        :param elements_str: the path to the element relative to tree
        :param value: the new value
        :param exact_match: match the field exact or use wildcards
        :param tree: defaults to the message root
        :return:
        """
        elm = self.find_elm(elements_str, tree)

        if not exact_match:
            # Add exact false for wildcard fields
            elm.set('StUF:exact', 'false')
            value = value.replace(WILDCARD_CHAR, STUF_WILDCARD_CHAR)

        elm.text = value

    def create_elm(self, elements_str: str, tree=None):
        """Creates an element when it doesn't exist yet and returns newly created element. If the element already
        exists, the existing element is returned.

        :param elements_str:
        :param tree:
        :return:
        """
        elm = self.find_elm(elements_str, tree)

        if elm is not None:
            # Already exists
            return elm

        elements = elements_str.split(' ')

        if len(elements) == 1:
            # Parent is tree
            parent = tree or self.tree
        else:
            # Create parent
            parent = self.create_elm(' '.join(elements[:-1]), tree)

        create_elm = elements[-1]

        if ':' in create_elm:
            ns, tag = create_elm.split(':')
            assert ns in self.namespaces, f"Namespace {ns} not defined"

            # Add namespaced tag, of the format '{http://example.com/namespace-definition}tag'
            return ET.SubElement(parent, '{%s}%s' % (self.namespaces[ns], tag))
        else:
            return ET.SubElement(parent, create_elm)

    def get_elm_value(self, elements_str: str, tree=None):
        """Get the value of the first element identified by elements_str

        :param elements_str: the path to the element relative to tree
        :param tree: defaults to the message root
        :return:
        """
        elm = self.find_elm(elements_str, tree)
        if elm is not None:
            return elm.text

    def get_elm_value_by_path(self, elements_str: str, path: str, tree=None):
        """
        Get an element by its XPath path

        :param path: XPath spec
        :param tree: defaults to the message root
        :return:
        """
        elm = self.find_elm(elements_str, tree)
        if elm is not None:
            # Find element using XPath expression
            elm = elm.find(path, self.namespaces)
            if elm is not None:
                return elm.text

    def get_elm_attr(self, elements_str: str, element_attr: str, tree=None):
        """Get the attribute value for element_attr

        Attribute names can be prefixed by a namespace

        :param elements_str: the path to the element relative to tree
        :param element_attr: the name of the attribute
        :param tree: defaults to the message root
        :return:
        """
        elm = self.find_elm(elements_str, tree)
        if elm is not None:
            if ':' in element_attr:
                # namespace attribute
                # example StUF:attr => {http://www.egem.nl/StUF/StUF0301}attr
                ns, attr = element_attr.split(':')
                element_attr = '{%s}%s' % (self.namespaces.get(ns, ''), attr)
            return elm.get(element_attr)

    def to_string(self):
        return ET.tostring(self.tree, encoding='utf-8')

    def pretty_print(self):
        xml_string = minidom.parseString(ET.tostring(self.tree, encoding='utf-8')).toprettyxml()

        # normalise newlines
        xml_string = os.linesep.join([s for s in xml_string.splitlines() if s.strip()])
        return xml_string
