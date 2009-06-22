#! /usr/bin/env python

import sys

sys.path.insert(0, 'gamelib')


try:
    import Image
except Exception:
    print 'ERROR: You should install python-imaging.'
    print 'Get it from: http://www.pythonware.com/products/pil/'
    exit(0)

import main
main.main()
