#########################################################
# CXV - Coral X-Ray Viewer
#
# @author:    Adam Childs
# @contact:   adchilds@eckerd.edu
#
# @copyright: owned and maintained by the
#             US Geological Survey (USGS),
#             Department of Interior (DOI)
#########################################################
import sys
import chilkat # XML API

class Controller():
    """ xml_controller controls all xml file querying. Methods
    related to setting and getting information from an xml file
    for CXV can be found here.
    """

    def __init__(self, file_path):
        self.xml = chilkat.CkXml()
        self.file_path = file_path

    def load_file(self):
        """ Attempts to load the XML file on the given file_path """
        return self.xml.LoadXmlFile(self.file_path)

    def create_config(self):
        """ Creates an XML file with default data that will later be loaded
        and accessed by a field name. By default, the fields contain no data.
        """
        self.xml.put_Tag("settings")
        self.xml.NewChild2("plugin_directory", "")
        self.xml.SaveXml(self.file_path)

    def get_plugin_directory(self):
        """ Returns the user's default plugin directory as a string """
        return self.xml.childContent('plugin_directory')
    
    def set_plugin_directory(self, file_path):
        """ Sets the user's plugin directory to the given path.
        
        @var file_path - The path to set plugin_directory to
        """
        self.xml.UpdateChildContent('plugin_directory', file_path)
        self.xml.SaveXml(self.file_path)

    def print_xml_file(self):
        self.xml.getXml()