#From Nand to Tetris Virtual Machine
#JediKoder

# VM language to Hack Assembly

import os
import sys
import re

arithmeticExp = re.compile(r"(add)|(sub)|(neg)|(eq)|(gt)|(lt)|(and)|(or)|(not)")
memoryExp = re.compile(r"(push|pop) (argument|local|static|constant|this|that|pointer|temp) (\d+|[a-zA-Z_\.:][a-zA-Z0-9_\.:]*)")
labelExp = re.compile(r"(label|goto|if-goto) ([a-zA-Z_\.:][a-zA-Z0-9_\.:]*)")
functionExp = re.compile(r"(function|call) ([a-zA-Z_\.:][a-zA-Z0-9_\.:]*) (\d+)")
returnExp = re.compile(r"(return)")

segPointers = {"sp": 0, "temp": 5, "pointer": 3, "argument": 2, "local": 1, "this": 3, "that": 4, "static": 16}

class addLine(object):
  def updater(self, vmFile, vmFunction, lineNumber):
    self.code = [
      "@SP",
      "M=M-1",
      "A=M",
      "D=M",
      "A=A-1",
      "M=D+M"
      ]

class subLine(object):
  def updater(self, vmFile, vmFunction, lineNumber):
    self.code = [
      "@SP",
      "M=M-1",
      "A=M",
      "D=M",
      "A=A-1",
      "M=M-D"
      ]

class negLine(object):
  def updater(self, vmFile, vmFunction, lineNumber):
    self.code = [
      "@SP",
      "A=M",
      "A=A-1",
      "M=-M",
      ]

class eqLine(object):
  def updater(self, vmFile, vmFunction, lineNumber):
    trueLabel = "%s$%d$true" % (vmFunction, lineNumber)
    falseLabel = "%s$%d$false" % (vmFunction, lineNumber)
    self.code = [
      "@SP",
      "M=M-1",
      "A=M",
      "D=M",
      "A=A-1",
      "D=D-M",
      "@%s" % (trueLabel,),
      "D;JEQ",
      "@SP",
      "A=M-1",
      "M=0",
      "@%s" % (falseLabel,),
      "0;JMP",
      "(%s)" % (trueLabel,),
      "@SP",
      "A=M-1",
      "M=0",
      "M=!M",
      "(%s)" % (falseLabel,)
    ]
    
class gtLine(object):
  def updater(self, vmFile, vmFunction, lineNumber):
    trueLabel = "%s$%d$true" % (vmFunction, lineNumber)
    falseLabel = "%s$%d$false" % (vmFunction, lineNumber)
    self.code = [
      "@SP",
      "M=M-1",
      "A=M",
      "D=M",
      "A=A-1",
      "D=D-M",
      "@%s" % (trueLabel,),
      "D;JLT",
      "@SP",
      "A=M-1",
      "M=0",
      "@%s" % (falseLabel,),
      "0;JMP",
      "(%s)" % (trueLabel,),
      "@SP",
      "A=M-1",
      "M=0",
      "M=!M",
      "(%s)" % (falseLabel,)
    ]
    
class ltLine(object):
  def updater(self, vmFile, vmFunction, lineNumber):
    trueLabel = "%s$%d$true" % (vmFunction, lineNumber)
    falseLabel = "%s$%d$false" % (vmFunction, lineNumber)
    self.code = [
      "@SP",
      "M=M-1",
      "A=M",
      "D=M",
      "A=A-1",
      "D=D-M",
      "@%s" % (trueLabel,),
      "D;JGT",
      "@SP",
      "A=M-1",
      "M=0",
      "@%s" % (falseLabel,),
      "0;JMP",
      "(%s)" % (trueLabel,),
      "@SP",
      "A=M-1",
      "M=0",
      "M=!M",
      "(%s)" % (falseLabel,)
    ]
    
class andLine(object):
  def updater(self, vmFile, vmFunction, lineNumber):
    self.code = [
      "@SP",
      "M=M-1",
      "A=M",
      "D=M",
      "A=A-1",
      "M=D&M"
      ]
    
class orLine(object):
  def updater(self, vmFile, vmFunction, lineNumber):
    self.code = [
      "@SP",
      "M=M-1",
      "A=M",
      "D=M",
      "A=A-1",
      "M=D|M"
      ]
    
class notLine(object):
  def updater(self, vmFile, vmFunction, lineNumber):
    self.code = [
      "@SP",
      "A=M",
      "A=A-1",
      "M=!M",
      ]

class pushLine(object):
  def __init__(self, seg, loc):
    self.seg = seg
    self.loc = loc
    
  def updater(self, vmFile, vmFunction, lineNumber):
    if self.seg == 'constant':     
      self.code = [
        "@" + self.loc,
        "D=A",
        "@SP",
        "A=M",
        "M=D",
        "@SP",
        "M=M+1"
        ]
    elif self.seg in ('temp', 'pointer'):
      self.code = [
        "@%d" % (segPointers[self.seg] + int(self.loc),),
        "D=M",
        "@SP",
        "A=M",
        "M=D",
        "@SP",
        "M=M+1"
        ]
    elif self.seg in ('argument', 'local', 'this', 'that'):
      self.code = [
        "@%d" % (segPointers[self.seg],),
        "D=M",
        "@" + self.loc,
        "A=D+A",
        "D=M",
        "@SP",
        "A=M",
        "M=D",
        "@SP",
        "M=M+1"
        ]
    elif self.seg in ('static'):
      self.code = [
        "@" + vmFunction + '.' + self.loc,
        "D=M",
        "@SP",
        "A=M",
        "M=D",
        "@SP",
        "M=M+1"
        ]

class popLine(object):
  def __init__(self, seg, loc):
    self.seg = seg
    self.loc = loc
    
  def updater(self, vmFile, vmFunction, lineNumber):
    if self.seg in ('temp', 'pointer'):
      self.code = [
        "@SP",
        "M=M-1",
        "A=M",
        "D=M",
        "@%d" % (segPointers[self.seg] + int(self.loc),),
        "M=D"
        ]
    elif self.seg in ('argument', 'local', 'this', 'that'):
      self.code = [
        "@%d" % (segPointers[self.seg],),
        "D=M",
        "@" + self.loc,
        "D=D+A",
        "@13",
        "M=D",
        "@SP",
        "M=M-1",
        "A=M",
        "D=M",
        "@13",
        "A=M",
        "M=D"
        ]
    elif self.seg in ('static'):
      self.code = [
        "@SP",
        "M=M-1",
        "A=M",
        "D=M",
        "@" + vmFunction + '.' + self.loc,
        "M=D"
        ]
    
class emptyLine(object):
  def updater(self, vmFile, vmFunction, lineNumber):
    self.code = []

class labelLine(object):
  def __init__(self, label):
    self.label = label

  def updater(self, vmFile, vmFunction, lineNumber):
    self.code = ["(%s$%s)" % (vmFunction, self.label)]

class gotoLine(object):
  def __init__(self, label):
    self.label = label

  def updater(self, vmFile, vmFunction, lineNumber):
    self.code = [
      "@%s$%s" % (vmFunction, self.label),
      "0;JMP"
    ]

class ifgotoLine(object):
  def __init__(self, label):
    self.label = label

  def updater(self, vmFile, vmFunction, lineNumber):
    self.code = [
        "@SP",
        "M=M-1",
        "A=M",
        "D=M",
        "@%s$%s" % (vmFunction, self.label),
        "D;JNE"
    ]

class functionLine(object):
  def __init__(self, functionName, localVars):
    self.functionName = functionName
    self.localVars = int(localVars)

  def updater(self, vmFile, vmFunction, lineNumber):
    self.code = sum([["(" + str(self.functionName) + ")"],[
      "@0",
      "D=A",
      "@SP",
      "M=M+1",
      "A=M-1",
      "M=D"
      ] * self.localVars],[])

class callLine(object):
  def __init__(self, functionName, arguments):
    self.functionName = functionName
    self.arguments = int(arguments)
               
  def updater(self, vmFile, vmFunction, lineNumber):
    returnAddress = "%s$%d$return_address" % (vmFile, lineNumber)
    modArgs = -self.arguments - 5
    if modArgs < 0:
      op = '-'
      modArgs = -modArgs
    else:
      op = '+'
    self.code = sum([[
      "@" + returnAddress,
      "D=A",
      "@SP",
      "M=M+1",
      "A=M-1",
      "M=D"
      ],[
      "@" + str(segPointers['local']),
      "D=M",
      "@SP",
      "M=M+1",
      "A=M-1",
      "M=D"
      ],[
      "@" + str(segPointers['argument']),
      "D=M",
      "@SP",
      "M=M+1",
      "A=M-1",
      "M=D"
      ],[
      "@" + str(segPointers['this']),
      "D=M",
      "@SP",
      "M=M+1",
      "A=M-1",
      "M=D"
      ],[
      "@" + str(segPointers['that']),
      "D=M",
      "@SP",
      "M=M+1",
      "A=M-1",
      "M=D"
      ],[
      "@" + str(segPointers['sp']),
      "D=M"
      ],[
      "@%d" % (modArgs,),
      "D=D%sA" % (op,)
      ],[
      "@" + str(segPointers['argument']),
      "M=D"
      ],[
      "@" + str(segPointers['sp']),
      "D=M",
      "@" + str(segPointers['local']),
      "M=D"
      ],[
      "@" + str(self.functionName),
      "0;JMP"
      ],["(" + returnAddress + ")"]],[])

class returnLine(object):
  def updater(self, vmFile, vmFunction, lineNumber):
    self.code = sum([[
      "@" + str(segPointers['local']),
      "D=M",
      "@13",
      "M=D"
      ],[
      "@13",
      "D=M"
      ],[
      "@5",
      "D=D-A"
      ],[
      "A=D",
      "D=M"
      ],[
      "@14",
      "M=D"
      ],[
      "@SP",
      "M=M-1",
      "A=M",
      "D=M"
      ],[
      "@" + str(segPointers['argument']),
      "A=M",
      "M=D"
      ],[
      "@" + str(segPointers['argument']),
      "D=M"
      ],[
      "@1",
      "D=D+A"
      ],[
      "@" + str(segPointers['sp']),
      "M=D"
      ],[
      "@13",
      "D=M"
      ],[
      "@1",
      "D=D-A"
      ],[
      "A=D",
      "D=M"
      ],[
      "@" + str(segPointers['that']),
      "M=D"
      ],[
      "@13",
      "D=M"
      ],[
      "@2",
      "D=D-A"
      ],[
      "A=D",
      "D=M"
      ],[
      "@" + str(segPointers['this']),
      "M=D"
      ],[
      "@13",
      "D=M"
      ],[
      "@3",
      "D=D-A"
      ],[
      "A=D",
      "D=M"
      ],[
      "@" + str(segPointers['argument']),
      "M=D"
      ],[
      "@13",
      "D=M"
      ],[
      "@4",
      "D=D-A"
      ],[
      "A=D",
      "D=M"
      ],[
      "@" + str(segPointers['local']),
      "M=D"
      ],[
      "@14",
      "A=M",
      "0;JMP"
      ]],[])

lineDict = {
  'add'  : addLine,
  'sub'  : subLine,
  'neg'  : negLine,
  'eq'   : eqLine,
  'gt'   : gtLine,
  'lt'   : ltLine,
  'and'  : andLine,
  'or'   : orLine,
  'not'  : notLine,
  'push' : pushLine,
  'pop'  : popLine,
  'empty': emptyLine,
  'label': labelLine,
  'goto' : gotoLine,
  'if-goto' : ifgotoLine,
  'function': functionLine,
  'call' : callLine,
  'return'  : returnLine
}


def removeComments(line):
  try:
    return line[:line.index("//")]
  except ValueError:
    return line

class vmParse(object):
  """Categorize input vm files by line"""
  
  @staticmethod 
  def parseLine(line):
    line = removeComments(line)
    matchArith = arithmeticExp.match(line)
    matchMem = memoryExp.match(line)
    matchLabel = labelExp.match(line)
    matchFunction = functionExp.match(line)
    matchReturn = returnExp.match(line)
    if matchArith:
      return lineDict[matchArith.group()]()
    elif matchMem:
      return lineDict[matchMem.group(1)](matchMem.group(2), matchMem.group(3))
    elif matchLabel:
      return lineDict[matchLabel.group(1)](matchLabel.group(2))
    elif matchFunction:
      return lineDict[matchFunction.group(1)](matchFunction.group(2),matchFunction.group(3))
    elif matchReturn:
      return lineDict[matchReturn.group()]()
    else:
      return lineDict['empty']()

class vmWrite(object):
  """Write assembly code from parsed vm files"""

  @staticmethod
  def writeCode(line, vmFile, vmFunction, lineNumber):
    line.updater(vmFile, vmFunction, lineNumber)
    return line.code

def parseLines(lines):
  return map(vmParse.parseLine, lines)

def findFunctions(lines):
  functionList = []
  thisFunction = 'defaultFunction'
  for line in lines:
    if line.__class__.__name__ == 'functionLine':
      thisFunction = line.functionName
    functionList.append(thisFunction)
  return functionList

def decorateLines(lines, name):
  return zip(lines, [name] * len(lines), findFunctions(lines), range(len(lines)))

def writeAssembly(lines):
  return map(lambda x: vmWrite.writeCode(x[0], x[1], x[2], x[3]), lines)

def putTogetherOne(lines, name):
  return sum(writeAssembly(decorateLines(parseLines(lines),name)),[])

def putTogetherAll(lines):
  return sum(map(lambda x: putTogetherOne(x[1], x[0]), lines),[])

def bootstrapCode(lines):
  bootstrapLine = callLine('Sys.init', 0)
  bootstrapLine.updater('Sys','',1000000)
  startCode = ["@256", "D=A", "@0", "M=D"]
  midCode = bootstrapLine.code
  return sum([startCode,midCode,lines],[])

def getFile(fil):
  inFile = open(fil,'r')
  return inFile.readlines()

def testWrite(outF, lines):
  fileName = open(outF, 'w')
  for line in lines: fileName.write(line + '\n')
  fileName.close()

def testMain(prog):
  progLines = getFile(prog)
  return putTogether(progLines, prog)

def testMain2(prog1, prog2, outName):
  lines=[]
  lines1 = getFile(prog1)
  lines2 = getFile(prog2)
  lines.append((prog1[:-3], lines1))
  lines.append((prog2[:-3], lines2))
  asmCode = bootstrapCode(putTogetherAll(lines))
  testWrite(outName, asmCode)
 
def main():
  if len(sys.argv) != 2:
    print "Please enter a file or directory."
    return

  lines = []
  totalRead = 0
  if os.path.isfile(sys.argv[1]):
    print "File read:"
    print sys.argv[1]
    if sys.argv[1].endswith(".vm"):
      try:
        with open(sys.argv[1], "r") as programFile:
          programLines = programFile.readlines()
          lines.append((sys.argv[1][:-3], programLines))
      except IOError as error:
        print error.message
  elif os.path.isdir(sys.argv[1]):
    print "Directory read:"
    print sys.argv[1]
    for fileName in os.listdir(sys.argv[1]):
      if fileName.endswith(".vm"):
        try:
          with open(fileName, "r") as programFile:
            programLines = programFile.readlines()
            lines.append((fileName[:-3], programLines))
            totalRead = totalRead + 1
        except IOError as error:
          print error.message

  print 'Total .vm files read: %d' % (totalRead,)

  try:
    programAsm = bootstrapCode(putTogetherAll(lines))
    with open("out.asm", "w") as asmFile:
      asmFile.write(os.linesep.join(programAsm))
  except IOError as error:
    print error.message


if __name__ == "__main__":
  main()
