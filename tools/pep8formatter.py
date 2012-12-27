#!/usr/bin/python
''' Tool for fomatting python files to standard '''

import os
import py_compile
import sys

# Only signle character operators are valid, you must check for double-operators
# explicitly.
ARITH_OPERATORS = ('=', '+', '-', '*', '/', '!', '<', '>', '|', '&', '~')

if len(sys.argv) < 2:
    sys.stderr.write("Usage: " + sys.argv[0] + " [file]\n")
    sys.exit(1)

if len(sys.argv) > 2:
    import subprocess
    print "Distributing pep8formatting..."
    cmd = "disttask \"pep8formatter.py %s\" 32 " + ' '.join(sys.argv[1:])
    pipe = subprocess.Popen(cmd, shell=True).wait()
    sys.exit(0)


try:
    myname = sys.argv[0]
    if '/' in myname:
        myname = myname[myname.rfind('/') + 1:]
    if myname == sys.argv[1]:
        sys.stderr.write("Cannot pep8format myself!\n")
        sys.exit(1)
    f = open(sys.argv[1])
except IOError:
    sys.stderr.write("Cannot open " + sys.argv[1] + " for reading!\n")
    sys.exit(1)

#print "Formatting " + sys.argv[1] + "..."
contents = f.read() #Unformatted contents
f.close()

os.system("touch " + sys.argv[1]) # A totally different pyc file is generated without doing this.

try:
    os.remove(sys.argv[1] + "c")
except:
    pass
py_compile.compile(sys.argv[1])
try:
    f = open(sys.argv[1] + "c", "r")
    compiled = f.read()
    f.close()
except:
    sys.stderr.write("Can't compile file (" + sys.argv[1] + ")! Exiting...\n")
    sys.exit(1)

inString = '' # The current string contained within(' " ''' or """ ), or '' for none.
inParen = 0 # How many levels of parenthesis
inComment = False
newContents = '' # Formatted contents

# Because python won't let me change i
skip = 0

i = 0
lineNum = 1 # current line number

bracket = False

didPdb = False

for i in range(0, len(contents)):
    if skip > 0:
        skip -= 1
        continue

    c = contents[i]

    if inComment:
        if c == '\n':
            inComment = False
            lineNum += 1
        newContents += c
        continue

    addedSpace = False
    exponential = False
    prevSpace = False
    overrideSpace = False
    singleIdx = False


    if c == '[' and not inString:
        bracket = True
    elif c == ']' and not inString:
        bracket = False

    if c == '(' and not inString:
        inParen += 1
    elif c == ')' and not inString:
        inParen -= 1
    elif c == '\\':
        newContents += c
        continue
    elif c == '\n':
        lineNum += 1
    elif (c == '\"' or c == '\'') and (contents[i - 1] != '\\' or (contents[i - 1] == '\\' and contents[i - 2] == '\\')):
        if not inString: # Not currently in a string
            inString = c
            if i + 2 < len(contents) and contents[i + 1] == c and contents[i + 2] == c: #triple str
                inString = c + c + c
                newContents += c + c + c
                skip = 2
            else:
                newContents += c
            continue
        elif c == inString[0]: # Pontential match for closing string character
            if len(inString) == 1:
                if i >= 1 and (contents[i - 1] != '\\' or (contents[i - 1] == '\\' and contents[i - 2] == '\\')): #single str
                    newContents += c
                    inString = ''
                    continue
                else:
                    newContents += c
                    continue
            else:
                if i + 2 < len(contents) and contents[i + 1] == c and contents[i + 2] == c: #triple str
                    newContents += c + c + c
                    inString = ''
                    skip = 2
                    continue
                else:
                    newContents += c
                    continue
        else: # Just some string character
            newContents += c
            continue
    elif c == '\t' and not inString:
        newContents += '\t'
        sys.stderr.write(sys.argv[1] + ":" + str(lineNum) + "  WARNING: Found a tab. Did not correct.\n")
        continue

    elif c in ARITH_OPERATORS + (',',) and not inString and (not inParen or c == ','): # Space before and after assignment

        #LEFT
        if c != ',' and contents[i - 1] != ' ' and contents[i - 1] not in ARITH_OPERATORS:
            if c in ('+', '-') and contents[i - 1] in ('e', 'E'):
                exponential = True
            elif c == '-' and contents[i - 1] == '[' and contents[i + 1].isdigit():
                singleIdx = True
            elif contents[i - 1] == ':':
                overrideSpace = True
            elif contents[i - 1] == '(':
                overrideSpace = True
            else:
                newContents += ' '
                addedSpace = True
        elif contents[i - 1] == ' ' and not contents[i - 2].isalnum():
            prevSpace = True
        newContents += c

        #rIGHT
        if not overrideSpace and not exponential and not singleIdx and not prevSpace and (contents[i + 1] != ' ' and (contents[i + 1] not in ARITH_OPERATORS or contents[i + 1] == '-')):
            if c == '-' and not bracket and contents[i + 1].isdigit():
                pass
            elif contents[i + 1] in (')', '\n', ']'):
                pass
            elif c == '*' and contents[i - 1] == '*':
                pass
            elif c == '-' and contents[i - 2] == 'n' and contents[i - 3] == 'r' and contents[i - 4] == 'u': #probably return a negative number
                pass
            else:
                newContents += ' '
                addedSpace = True

        if addedSpace:
            sys.stderr.write(sys.argv[1] + ":" + str(lineNum) + "  Added space around operator ('" + c + "')\n")
        continue
    elif c == '#' and not inString:
        inComment = True
        newContents += c
        continue


    if inString:
        newContents += c
        continue

    if inParen and not inString:
        if c == ',' and (i + 1 < len(contents)) and contents[i + 1] not in (' ', '\n'): # Put a space after commas
            newContents += c + ' '
            sys.stderr.write(sys.argv[1] + ":" + str(lineNum) + "  Corrected comma after space\n")
            continue

    newContents += c # No special handler
#end for

output = open(sys.argv[1], "w")
output.write(newContents)
output.close()

try:
    os.remove(sys.argv[1] + "c")
except:
    pass
py_compile.compile(sys.argv[1])
try:
    f = open(sys.argv[1] + "c", "r")
    compiled2 = f.read()
    f.close()
except:
    compiled2 = ""

compiled = compiled[6:]
compiled2 = compiled2[6:]

if compiled != compiled2:
    sys.stderr.write(sys.argv[1] + ":  Compiled code changed! Check diff!\n")
