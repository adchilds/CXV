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
from Models import dxf_model

class Controllers():
    """ Entrance point for CXV components using DXF capabilities """

    def __init__(self):
        self.model = dxf_model.Model()

    def get_model(self):
        return self.model