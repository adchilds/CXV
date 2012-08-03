#########################################################
# CXV - Coral X-Ray Viewer
#
# @author:    Luke Mueller
# @contact:   muellelj@eckerd.edu or lmueller62@gmail.com
#
# @author:    Adam Childs
# @contact:   adchilds@eckerd.edu
#
# @copyright: owned and maintained by the
#             US Geological Survey (USGS),
#             Department of Interior (DOI)
#########################################################
from Controllers import coral_controller
from Controllers import polyline_controller
from Controllers import calibrate_controller
from Controllers import xml_controller
from Models import polyline_model
import chilkat # XML API

class SaveSession():
    
    def __init__(self, controller, path):
        self.controller = controller
        self.path = path
        self.fn = None  # file name

    def load_file(self):
        xml = chilkat.CkXml()
        path = self.path.encode('ascii', 'ignore')
        xml.LoadXmlFile(path)
        xml.UnzipTree()
        self.fn = xml.getChildContent("filename")

    def load(self):
        """ Loads the data (polylines, target area, calibration region,
        zoom factor, scrollbars, etc.) from the saved session (*.xml) file.
        """
        xml = chilkat.CkXml()
        path = self.path.encode('ascii', 'ignore')
        xml.LoadXmlFile(path)

        # Load Calibration Region
        calib = xml.SearchForContent(xml, "calibration_region", "")
        calib = calib.attr("exists")
        if calib == "True":
            calib = xml.SearchForTag(xml, "calibration_region") # Reset calib


            self.controller.view.toolbar.ToggleTool(self.controller.view.toolbar_ids['Adjust Calibration Region'], True)
            #self.controller.on_calibrate(None)
            self.controller.calibrate_controller = calibrate_controller.Controller(self.controller.view, self.controller.background)

            # Thickness Range
            thickness = xml.SearchForTag(calib, "thickness_range")
            if thickness is not None:
                self.controller.calibrate_controller.min_thickness = float(thickness.getChildContent("min"))
                self.controller.calibrate_controller.max_thickness = float(thickness.getChildContent("max"))

            # AL Grayscale Range
            range = xml.SearchForTag(calib, "al_grayscale_range")
            if range is not None:
                i = 0
                data = []
                while xml.SearchForTag(range, str(i)):
                    data.append(range.getChildContent(str(i)))
                    i = i + 1
                self.controller.calibrate_controller.dw_grayscales = data

            # Grayscale to AL Thickness
            range = xml.SearchForTag(calib, "grayscale_to_al_thick")
            if range is not None:
                i = 0
                data = []
                while xml.SearchForTag(range, str(i)) is not None:
                    data.append(range.getChildContent(str(i)))
                    i = i + 1
                self.controller.calibrate_controller.dw_linfit = data

            # Grayscale to Relative Density
            range = xml.SearchForTag(calib, "grayscale_to_relative_density")
            if range is not None:
                i = 0
                data = []
                while range.SearchForTag(range, str(i)) is not None:
                    data.append(range.getChildContent(str(i)))
                    i = i + 1
                self.controller.calibrate_controller.dw_reldenfit = data

            # Density
            density = xml.SearchForTag(calib, "density")
            if density is not None:
                self.controller.calibrate_controller.density = float(calib.getChildContent("density"))

            # Pixels Per Unit
            ppu = xml.SearchForTag(calib, "pixels_per_unit")
            if ppu is not None:
                self.controller.calibrate_controller.pixels_per_unit = float(calib.getChildContent("pixels_per_unit"))

            # Unit selected
            unit = xml.SearchForTag(calib, "unit_selected")
            if unit is not None:
                self.controller.calibrate_controller.unit = calib.getChildContent("unit_selected")
    
            # Region (x, y, width, height)
            region = xml.SearchForTag(calib, "region")
            if region is not None:
                data = []
                data.append(float(region.getChildContent("x_pos")))
                data.append(float(region.getChildContent("y_pos")))
                data.append(float(region.getChildContent("width")))
                data.append(float(region.getChildContent("height")))
                data[2] = data[2] + data[0]
                data[3] = data[3] + data[1]
                self.controller.calib_region = data
                self.controller.calibrate_controller.model.sx = data[0]
                self.controller.calibrate_controller.model.sy = data[1]
                self.controller.calibrate_controller.model.dx = data[2]
                self.controller.calibrate_controller.model.dy = data[3]

            self.controller.enable_tools(['Set Calibration Parameters'], True)
            self.controller.view.toolbar.ToggleTool(self.controller.view.toolbar_ids['Adjust Calibration Region'], False)

        # Load Target Area
        target = xml.SearchForContent(xml, "target_area", "")
        target = target.attr("exists")
        if target == 'True':
            target = xml.SearchForTag(xml, "target_area") # Reset target

            self.controller.view.toolbar.ToggleTool(self.controller.view.toolbar_ids['Adjust Target Area'], True)
            #self.controller.on_coral(None)
            self.controller.coral_controller  = coral_controller.Controller(self.controller.view, self.controller.background)

            coords = []
            coords.append(float(target.getChildContent("x_pos")))
            coords.append(float(target.getChildContent("y_pos")))
            dx = float(target.getChildContent("width")) + float(target.getChildContent("x_pos"))
            coords.append(dx)
            dy = float(target.getChildContent("height")) + float(target.getChildContent("y_pos"))
            coords.append(dy)
            self.controller.coral_slab = coords
            self.controller.coral_controller.model.sx = coords[0]
            self.controller.coral_controller.model.sy = coords[1]
            self.controller.coral_controller.model.dx = coords[2]
            self.controller.coral_controller.model.dy = coords[3]

            self.controller.enable_tools(['Lock Target Area'], True)
            self.controller.view.toolbar.ToggleTool(self.controller.view.toolbar_ids['Adjust Target Area'], False)

        # Load Polylines
        poly = xml.SearchForContent(xml, "polylines", "")
        poly = poly.attr("exists")
        if poly == 'True':
            poly = xml.SearchForTag(xml, "polylines")

            polylines = []
            num_of_lines = poly.NumChildrenHavingTag("poly")
            if num_of_lines > 0:
                # Loop over all the lines in the XML file
                for i in xrange(num_of_lines):
                    polyline = polyline_model.Polyline(self.controller, self.controller.view.axes)
                    x_pos = 0
                    y_pos = 0
                    vertex = None
                    line = poly.GetNthChildWithTag("poly", i)
                    name = line.attr("name")
                    color = line.attr("color")
                    num_of_vertices = line.NumChildrenHavingTag("vertex")
                    if num_of_vertices > 0:
                        # Loop over all the vertices for each line
                        for v in xrange(num_of_vertices):
                            vertex = line.GetNthChildWithTag("vertex", v)
                            x_pos = vertex.getChildContent("x_pos")
                            y_pos = vertex.getChildContent("y_pos")
                            
                            if v != 0:
                                prev_vertex = polyline.get_vertex(v-1)
                                polyline.add_line([prev_vertex.get_xdata()[0], float(x_pos)],
                                                  [prev_vertex.get_ydata()[0], float(y_pos)])
                            polyline.add_vertex(float(x_pos), float(y_pos))
                            polyline.color = color
                            polyline.set_colors()
                        polylines.append(polyline)
                for polyline in polylines:
                    polyline.set_label(polylines.index(polyline))
                self.controller.polyline_controller = polyline_controller.Controller(
                                                                self.controller, 
                                                                self.controller.view, 
                                                                self.controller.background)
                self.controller.polyline_controller.polylines = polylines
                self.controller.polyline_controller.curr_pl = polylines[0]

        # Set the zoom ratio and scrollbar positions
        screen = xml.SearchForTag(xml, "screen")
        aspect = screen.getChildContent("aspect")
        scrollbars = xml.SearchForTag(screen, "scrollbars")
        scroll_x = scrollbars.getChildContent("x_pos")
        scroll_y = scrollbars.getChildContent("y_pos")

        # Redraw and resize the screen
        self.controller.view.aspect = float(aspect)
        self.controller.view.aspect_cb.SetValue(str(int(round(float(aspect)*100.0)))+'%')
        self.controller.on_aspect(None, int(scroll_x), int(scroll_y))

    def write(self):
        """ Write the contents of the workspace to an external XML file. """

        # Save the session to the given xml file (self.path)
        xml = xml_controller.Controller(self.path)
        xml.create_session(self.controller)

        # No changes have occurred since saving
        self.controller.changed = False