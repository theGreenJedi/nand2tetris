# Project 6 Assembler
# JediKoder

# Assembles the machine language from a given Hack Assembly program
# Usage is:
# python cmdHackAssembler.py Pong.asm

import os
import re
import sys

# These "regular expressions" are used to match string formats in the .asm files
# The re module is provided with Python
symbolExpression = r"[a-zA-Z_\$\.:][a-zA-Z0-9_\$\.:]*"
A_CommandExpression = re.compile(r"^@(\d*|" + symbolExpression + ")$")
A_SymbolExpression = re.compile(r"^@(" + symbolExpression + ")$")
destExpression = r"(?:(M|D|MD|A|AM|AD|AMD)=)?"
jumpExpression = r"(?:;(JGT|JEQ|JGE|JLT|JNE|JLE|JMP))?"
compExpression = (r"(0|1|-1|D|A|!D|!A|-D|-A|D\+1|A\+1|D-1|A-1|D\+A|D-A|A-D|D&A|D\|A|"
                  r"M|!M|-M|M\+1|M-1|D\+M|D-M|M-D|D&M|D\|M)")
C_CommandExpression = re.compile(r"^%s%s%s$" % (destExpression, compExpression, jumpExpression))
L_CommandExpression = re.compile(r"^\((" + symbolExpression + ")\)$")

compArray = {   "0": "0101010",
			    "1": "0111111",
			   "-1": "0111010",
			    "D": "0001100",
			    "A": "0110000",
			   "!D": "0001101",
			   "!A": "0110001",
			   "-D": "0001111",
			  "D+1": "0011111",
			  "A+1": "0110111",
			  "D-1": "0001110",
			  "A-1": "0110010",
			  "D+A": "0000010",
			  "D-A": "0010011",
			  "A-D": "0000111",
			  "D&A": "0000000",
			  "D|A": "0010101",
			    "M": "1110000",
			   "!M": "1110001",
			   "-M": "1110011",
			  "M+1": "1110111",
			  "M-1": "1110010",
			  "D+M": "1000010",
			  "D-M": "1010011",
			  "M-D": "1000111",
			  "D&M": "1000000",
			  "D|M": "1010101"
}

destArray = {    "": "000",
			    "M": "001",
			    "D": "010",
			   "MD": "011",
			    "A": "100",
			   "AM": "101",
			   "AD": "110",
			  "AMD": "111"
}

jumpArray = {    "": "000",
			  "JGT": "001",
			  "JEQ": "010",
			  "JGE": "011",
			  "JLT": "100",
			  "JNE": "101",
			  "JLE": "110",
			  "JMP": "111"
}

symbolTable = {   "SP": 0,
				 "LCL": 1,
				 "ARG": 2,
				"THIS": 3,
				"THAT": 4,
			  "SCREEN": 16384,
				 "KBD": 24576,
				  "R0": 0,
				  "R1": 1,
				  "R2": 2,
				  "R3": 3,
				  "R4": 4,
				  "R5": 5,
				  "R6": 6,
				  "R7": 7,
				  "R8": 8,
				  "R9": 9,
				 "R10": 10,
				 "R11": 11,
				 "R12": 12,
				 "R13": 13,
				 "R14": 14,
				 "R15": 15
}
      
    
def SymbolTable(inputProgram):
# First pass through the input assembly program
# Populates the symbol table
  romAddress = 0
  for line in inputProgram:
    matchA = re.match(A_CommandExpression, RemoveComments(line).strip())
    matchC = re.match(C_CommandExpression, RemoveComments(line).strip())
    matchL = re.match(L_CommandExpression, RemoveComments(line).strip())
    if matchL:
      symbolTable[matchL.group(1)] = romAddress
    elif matchA or matchC:
      romAddress += 1
      
  ramAddress = 16 
  for line in inputProgram:
    matchSymbol = re.match(A_SymbolExpression, RemoveComments(line).strip())
    if matchSymbol:
      symbol = matchSymbol.group(1)
      if symbol not in symbolTable:
        symbolTable[symbol] = ramAddress
        ramAddress += 1

def Parser(inputProgram):
# Second pass through the input assembly program
# Makes all symbol replacements and line deletions
# Returns simplified program
  modProgram = []
  for line in inputProgram:
    matchA = re.match(A_CommandExpression, RemoveComments(line).strip())
    matchC = re.match(C_CommandExpression, RemoveComments(line).strip())
    if matchA:
      if matchA.group(1).isdigit():
        modProgram.append("@" + matchA.group(1))
      else:
        modProgram.append("@" + str(symbolTable[matchA.group(1)]))
    elif matchC:
      modProgram.append(matchC.group(0))
  return modProgram

def Code(line):
# Converts simplified program lines into binary
  returnLine = ""
  matchA = re.match(A_CommandExpression, RemoveComments(line).strip())
  matchC = re.match(C_CommandExpression, RemoveComments(line).strip())
  if matchA:
    number = int(matchA.group(1))
    for i in range(15):
      returnLine = str(number % 2) + returnLine
      number = number / 2
    return "0" + returnLine
  elif matchC:
    dest = matchC.group(1) if matchC.group(1) else ""
    comp = matchC.group(2)
    jump = matchC.group(3) if matchC.group(3) else ""
    returnLine = "111%s%s%s" % (compArray[comp],destArray[dest],jumpArray[jump])
    return returnLine	
  else:
    return False

def RemoveComments(line):
#Looks for a comment and returns everything preceding it
  try:
  	return line[:line.index("//")]
  except ValueError:
    return line
      
def main():
# Brings all the modules together
  asmInput = sys.argv[1]
  assemblyFile = open(asmInput, "r")
  inputProgram = assemblyFile.readlines()
  SymbolTable(inputProgram)
  modProgram = Parser(inputProgram)
  programLines = map(Code, modProgram)
  hackFile = open(asmInput[:-4] + ".hack", "w")
  hackFile.write(os.linesep.join(programLines))

if __name__ == "__main__":
  main()
