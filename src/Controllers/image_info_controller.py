#########################################################
# CXV - Coral X-Ray Viewer
#
# @author:    Luke Mueller
# @contact:   muellelj@eckerd.edu or lmueller62@gmail.com
#
# @copyright: owned and maintained by the
#             US Geological Survey (USGS),
#             Department of Interior (DOI)
#########################################################
from Views import image_info_view

class Controller():
    
    def __init__(self, dicom_controller, model):
        self.dicom_controller = dicom_controller
        self.model = model
        self.view = image_info_view.View(self, self.model)
        self.populate_table()
        self.view.Show()
        
    def populate_table(self):
        self.view.grid.SetColLabelValue(0, "Value")
        i = 0
        for data_element in self.model.ds:
            self.view.grid.SetRowLabelSize(185)
            self.view.grid.SetRowLabelValue(i, self.model.get_meta_description(data_element))
            self.view.grid.SetCellValue(i, 0, self.model.get_meta_value(data_element))
            self.view.grid.SetReadOnly(i, 0, True)
            if (i % 2) == 0:
                self.view.grid.SetCellBackgroundColour(i, 0, 'light blue')
            i += 1
            
        self.view.grid.AutoSizeColumns()
        self.view.grid.AutoSizeRows()