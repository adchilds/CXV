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
import wx

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
        
        @return - True if the file has saved successfully
        """
        self.xml.put_Tag("settings")
        self.xml.NewChild2("plugin_directory", "")
        return self.xml.SaveXml(self.file_path)

    def create_session(self, dc):
        """ Creates an XML file with data from the user's current session.
        This method is called when the user attempts to save their session.
        
        @var dc - dicom_controller instance
        @return - True if the file has saved successfully
        """
        # Root element
        self.xml.put_Tag("session")

        # File path/name
        self.xml.NewChild2("filename", dc.model.get_dicom_path())

        # Zoom factor/viewable area of screen
        screen = self.xml.NewChild("screen", "")
        screen.NewChild2("aspect", str(dc.view.aspect))
        scrollbars = screen.NewChild("scrollbars", "")
        vertical = dc.view.scroll.GetScrollPos(wx.VERTICAL)
        horizontal = dc.view.scroll.GetScrollPos(wx.HORIZONTAL)
        scrollbars.NewChild2("x_pos", str(horizontal))
        scrollbars.NewChild2("y_pos", str(vertical))

        # Calibration Region
        calib = self.xml.NewChild("calibration_region", "")
        calib.AddAttribute("exists", str(dc.calibrate_controller is not None))
        if dc.calibrate_controller:
            thickness = calib.NewChild("thickness_range", "")
            thickness.NewChild2("min", str(dc.calibrate_controller.min_thickness))
            thickness.NewChild2("max", str(dc.calibrate_controller.max_thickness))
    
            grayscale = calib.NewChild("al_grayscale_range", "")
            i = 0
            for each in dc.calibrate_controller.dw_grayscales:
                grayscale.NewChild2(str(i), str(each))
                i = i + 1
    
            grayscale_al_thick = calib.NewChild("grayscale_to_al_thick", "")
            i = 0
            for each in dc.calibrate_controller.dw_linfit:
                grayscale_al_thick.NewChild2(str(i), str(each))
                i = i + 1
    
            grayscale_relative_density = calib.NewChild("grayscale_to_relative_density", "")
            i = 0
            for each in dc.calibrate_controller.dw_reldenfit:
                grayscale_relative_density.NewChild2(str(i), str(each))
                i = i + 1
    
            calib.NewChild2("density", str(dc.calibrate_controller.density))
    
            x, y, dx, dy = dc.calib_region
            w = dx-x
            h = dy-y
            coords = [x, y, w, h]
            region = calib.NewChild("region", "")
            region.NewChild2("x_pos", str(coords[0]))
            region.NewChild2("y_pos", str(coords[1]))
            region.NewChild2("width", str(coords[2]))
            region.NewChild2("height", str(coords[3]))

        # Target Area
        target = self.xml.NewChild("target_area", "")
        target.AddAttribute("exists", str(dc.coral_controller is not None))
        if dc.coral_controller:
            x, y, dx ,dy = dc.coral_slab
            w = dx - x
            h = dy - y
            coords = [x, y, w, h]
            target.NewChild2("x_pos", str(coords[0]))
            target.NewChild2("y_pos", str(coords[1]))
            target.NewChild2("width", str(coords[2]))
            target.NewChild2("height", str(coords[3]))

        # Polylines
        polylines = self.xml.NewChild("polylines", "")
        polylines.AddAttribute("exists", str(dc.polyline_controller is not None))
        if dc.polyline_controller:
            for polyline in dc.polyline_controller.polylines:
                poly = polylines.NewChild("poly", "")
                poly.AddAttribute("name", polyline.label.get_text())
                poly.AddAttribute("color", polyline.get_color())
                i = 0
                for vertex in polyline.verticies:
                    x, = vertex.get_xdata()
                    y, = vertex.get_ydata()
                    vert = poly.NewChild("vertex", "")
                    vert.AddAttribute("num", str(i))
                    vert.NewChild2("x_pos", str(x))
                    vert.NewChild2("y_pos", str(y))
                    i = i + 1

        # Save the file after we're done creating it
        return self.xml.SaveXml(self.file_path)

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