#!/usr/bin/python

import os
import shutil
import sys

if len(sys.argv) < 2:
    print "Usage: " + sys.argv[0] + " [filename]"
    sys.exit(23)
elif len(sys.argv) > 2:
    import subprocess
    print "Distributing stripWhitespace"
    cmd = "disttask \"stripWhitespace.py %s\" 32 " + ' '.join(sys.argv[1:])
    pipe = subprocess.Popen(cmd, shell=True).wait()
    sys.exit(0)

fname = sys.argv[1]

shutil.copyfile(fname, fname + '.bak')

## os.system("cp %s %s.bak" % (fname, fname))

infile = open(fname, 'r')
contents = infile.read()
contents = contents.rstrip()
infile.close()

lines = contents.split('\n')

outfile = open(fname, 'w')

inString = False
for line in lines:
    if inString:
        if inString in line:
            inString = False
    else:
        if '"""' in line:
            inString = '"""'
        elif "'''" in line: 
            inString = "'''"
    if not inString:
        line = line.rstrip()
    outfile.write(line + "\n")
outfile.flush()
outfile.close()
