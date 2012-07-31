import cx_Freeze
import sys

base = None
if sys.platform == "win32":
    base = "Win32GUI"

buildOptions = dict(
        
        # Here we need to include modules that aren't picked up by cx_Freeze
        # Also, we include any modules that the plugins supplied by the user
        # might need, such as all of scipy, numpy, and PIL.
        includes = ["matplotlib.backends.backend_tkagg",
                    
                    # Scipy Libraries
                    "scipy",
                    "scipy.cluster",
                    "scipy.constants",
                    "scipy.fftpack",
                    "scipy.integrate",
                    "scipy.interpolate",
                    "scipy.io",
                    "scipy.lib",
                    "scipy.linalg",
                    "scipy.maxentropy",
                    "scipy.misc",
                    "scipy.ndimage",
                    "scipy.odr",
                    "scipy.optimize",
                    "scipy.signal",
                    "scipy.sparse",
                    "scipy.spatial",
                    "scipy.special",
                    "scipy.stats",
                    "scipy.weave",
                    
                    # Numpy Libraries
                    "numpy",
                    "numpy.compat",
                    "numpy.core",
                    "numpy.distutils",
                    "numpy.doc",
                    "numpy.f2py",
                    "numpy.fft",
                    "numpy.lib",
                    "numpy.linalg",
                    "numpy.ma",
                    "numpy.matrixlib",
                    "numpy.numarray",
                    "numpy.oldnumeric",
                    "numpy.polynomial",
                    "numpy.random",
                    
                    # PIL Libraries
                    "PIL.Image",
                    "PIL.ImageChops",
                    "PIL.ImageColor",
                    "PIL.ImageDraw",
                    "PIL.ImageEnhance",
                    "PIL.ImageFile",
                    "PIL.ImageFileIO",
                    "PIL.ImageFilter",
                    "PIL.ImageFont",
                    "PIL.ImageGrab",
                    "PIL.ImageMath",
                    "PIL.ImageOps",
                    "PIL.ImagePalette",
                    "PIL.ImagePath",
                    "PIL.ImageQt",
                    "PIL.ImageSequence",
                    "PIL.ImageStat",
                    "PIL.ImageTk",
                    "PIL.ImageWin",
                    "PIL.PSDraw",
                    "PIL.ImageGL"],
        
        # Here we include dependencies such as images used by CXV or the
        # pre-made plugins included within the distributed binary.
        include_files = ['plugins/butterworth.plugin',
                         'plugins/butterworth.py',
                         'plugins/sobel.plugin',
                         'plugins/sobel.py',
                         'plugins/template (plugin)',
                         'plugins/template (py)',
                         'images/calibrate.png',
                         'images/contrast.png',
                         'images/coral.png',
                         'images/cursor_cross.png',
                         'images/cursor_hand_closed.gif',
                         'images/cursor_hand_open.gif',
                         'images/cursor_hand.png',
                         'images/density.png',
                         'images/info.png',
                         'images/lock_calibrate.png',
                         'images/lock_coral.png',
                         'images/lock_polyline.png',
                         'images/open.png',
                         'images/overlay.png',
                         'images/overview.png',
                         'images/polyline.png',
                         'images/save.png',
                         'images/zoom_in_toolbar.png',
                         'images/zoom_out_toolbar.png',
                         'images/Thumbs.db'
                        ]
        )

executables = [
        cx_Freeze.Executable("main.py",
                             base = base,
                             compress = True,
                             copyDependentFiles = True,
                             appendScriptToExe = True,
                             shortcutName = 'Coral X-Ray Viewer',
                             shortcutDir = 'ProgramMenuFolder')
]

cx_Freeze.setup(
        name = "Coral X-Ray Viewer",
        version = "0.1",
        author = 'US Geological Survey',
        description = "Coral x-ray image viewing software for USGS",
        executables = executables,
        options = dict(build_exe = buildOptions))