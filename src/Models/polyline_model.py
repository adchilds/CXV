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
import math

class Polyline():
    
    def __init__(self, controller, axes):
        self.controller = controller
        self.axes = axes
        self.verticies = []
        self.lines = []
        self.color = '#00FF00'
        self.label = self.axes.text(0, 0, 't', color=self.color,
                                    ha='center', va='center',
                                    bbox=dict(facecolor='w', edgecolor=self.color),                                  
                                    zorder=1, animated=True)
        
    def add_vertex(self, x, y):
        vertex, = self.axes.plot(x, y,
                                 c=self.color, marker='o',
                                 ms=7, zorder=0,
                                 animated=True)
        self.verticies.append(vertex)
        return vertex
    
    def insert_vertex(self, index, x, y):
        vertex, = self.axes.plot(x, y,
                                 c=self.color, marker='o',
                                 ms=7, zorder=0,
                                 animated=True)
        self.verticies.insert(index, vertex)
        return vertex
    
    def remove_vertex(self, index):
        self.verticies.remove(self.get_vertex(index))
        
    def set_vertex(self, vertex, x, y):
        vertex.set_xdata([x])
        vertex.set_ydata([y])
        
    def get_vertex(self, index):
        return self.verticies[index]
        
    def get_vertex_index(self, vertex):
        return self.verticies.index(vertex)
    
    def is_first(self, vertex):
        if self.verticies.index(vertex) == 0: 
            return True
        return False
    
    def is_last(self, vertex):
        if self.verticies.index(vertex) == len(self.verticies)-1:
            return True
        return False
    
    def is_alone(self):
        if (len(self.verticies)==1) and (len(self.lines)==0):
            return True
        return False
    
    def add_line(self, xdata, ydata):
        line, = self.axes.plot(xdata, ydata, c=self.color, 
                               marker='-', zorder=1,
                               animated=True)
        self.lines.append(line)
        return line
    
    def insert_line(self, index, xdata, ydata):
        line, = self.axes.plot(xdata, ydata, c=self.color, 
                               marker='-', zorder=1,
                               animated=True)
        self.lines.insert(index, line)
        return line
    
    def remove_line(self, index):
        self.lines.remove(self.get_line(index))
        
    def set_line(self, line, xdata, ydata):
        line.set_xdata(xdata)
        line.set_ydata(ydata)
        
    def get_line(self, index):
        return self.lines[index]
        
    def get_line_index(self, line):
        return self.lines.index(line)
    
    def is_line(self, Line2D):
        return (Line2D in self.lines)

    def set_label(self, i):
        if self.is_alone(): line = self.controller.tmp_line
        else: line = self.lines[0]
        x1, x2 = line.get_xdata()
        y1, y2 = line.get_ydata()
        x_offset = math.fabs((x1-x2)/2.)
        y_offset = math.fabs((y1-y2)/2.)
        if x1 < x2: x = x1
        else: x = x2
        if y1 < y2: y = y1
        else: y = y2
        x += x_offset
        y += y_offset
        self.label.set_text('t'+str(i+1))
        self.label.set_position((x,y))

    def get_label(self):
        return self.label.get_text()

    def set_color(self, Line2D, color):
        Line2D.set_color(color)

    def set_colors(self):
        self.set_color(self.label, self.color)
        if (self.color=='#FFFFFF') or (self.color=='#FFFF00'):
            self.label.set_bbox(dict(facecolor='k', edgecolor=self.color))
        else:
            self.label.set_bbox(dict(facecolor='w', edgecolor=self.color))
        for line in self.lines:
            self.set_color(line, self.color)
        for vertex in self.verticies:
            self.set_color(vertex, self.color)

    def get_color(self):
        return self.color

    def print_info(self):
        print 'Polyline: ', id(self)
        print '\tverticies(%i):' % (len(self.verticies)), self.verticies
        print '\tlines(%i):' % (len(self.lines)), self.lines