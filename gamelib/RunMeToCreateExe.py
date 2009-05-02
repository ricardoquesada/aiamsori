# RunMeToCreatePackage.py
# Version 0.2
# 2007/04/11
#
# This program was created by Clint (HanClinto) Herron for the April 2007 PyWeek competition.
#
# It packages up basic games created with the Skellington app as EXE files.
# It requires that py2exe be installed on your system.
# Simply run this script, and it will take care of the rest.
#
# This source program is released into the public domain

from distutils.core import setup
import py2exe
import sys
import glob

# First step is to create a temporary launcher file, similar to the run_game.py file, that has the name of the EXE that they wish to create. This is a workaround to a problem where EXEs created with py2exe cannot be renamed to anything other than that which they were originally created with (or else they won't run properly). I don't know of the proper py2exe option to fix this.

program_listing = "#This is an automatically generated file that can be deleted\nimport main\nmain.main()" # The basics needed to run a game packaged with the skellington
filename = 'temp.py' # The name of the temporary launcher script to create

#filename = raw_input("What is the name of the executable that you wish to create (example: BubbleKong.exe or Slacker.exe) ? ")
filename = 'AiamsorI'
package_name = filename.replace(".exe", "") # Remove .exe from the end of the file (if it was added at all)
filename = package_name + ".py" # Add .py to the end so that we can create this as a script file

print "\nCreating our launcher script file '" + filename + "'\n"

FILE = open(filename,"w")
FILE.write(program_listing)
FILE.close()

# Now that we have our script file, we add command line arguments to execute py2exe with the proper bundle options
sys.argv.append("py2exe")
#sys.argv.append("--bundle")
#sys.argv.append("2")

setup(
    options = {'py2exe': {'bundle_files': 1}},
    windows=[
                {
                    "script": filename,
                    "icon_resources": [(1, "py.ico")]
                }
            ],
    zipfile=None,
    dist_dir=package_name,
    data_files=[("data",   glob.glob("../data/*.*")),
                ("data/collision", glob.glob("../data/collision/*.*")),
                ("data/faces", glob.glob("../data/faces/*.*")),
                ("data/fonts", glob.glob("../data/fonts/*.*")),
                ("data/hud", glob.glob("../data/hud/*.*")),
                ("data/img", glob.glob("../data/img/*.*")),
                ("data/newtiles", glob.glob("../data/newtiles/*.*")),
                ("data/sounds", glob.glob("../data/sounds/*.*")),
                ("data/tiles", glob.glob("../data/tiles/*.*")),
                ("data/walls", glob.glob("../data/walls/*.*")),
                (".", glob.glob("../README.txt"))]
    )
