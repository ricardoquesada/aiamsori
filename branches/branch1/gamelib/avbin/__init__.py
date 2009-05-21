import os.path
import platform
import sys, imp
import ctypes


def init_avbin():
    # lib gets loaded from:
    # avbin/libavbin32.so.7, -64.so, .dll or .dylib

    libname = 'avbin'
    s = platform.system()
    arch, arch2 = platform.architecture()

    path = os.path.dirname(os.path.abspath(__file__))
    try:
        if hasattr(sys, "frozen") or \
            hasattr(sys, "importers") or \
            hasattr(imp, "is_frozen") and imp.is_forzen("__main__"):
            path = os.path.dirname(os.path.abspath(sys.executable))
    except:
        pass
    libfn_specific = None

    if s == 'Linux':
        libfn = "lib%s.so.7" % libname
        libfn_specific = "lib%s%s.so.7" % (libname, arch[:2])

    elif s == 'Windows':
        libfn = "%s.dll" % libname
        return

    elif s == 'Darwin':
        libfn = "lib%s.5.dylib" % libname

    libfn = os.path.join(path, libfn)

    if libfn_specific != None:
        libfn_specific = os.path.join(path, libfn_specific)

        try:
            print "Loading avbin for %s (%s) [%s]" % (s, arch, libfn_specific)
            lib = ctypes.cdll.LoadLibrary(libfn_specific)
        except:
            print "Loading avbin for %s (%s) [%s]" % (s, arch, libfn)
            lib = ctypes.cdll.LoadLibrary(libfn)
    else:
        print "Loading avbin for %s (%s) [%s]" % (s, arch, libfn)
        lib = ctypes.cdll.LoadLibrary(libfn)
    return lib
