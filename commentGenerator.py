# Standard Libraries
import shutil
import os
import re
from itertools import pairwise
import argparse
import hashlib

#Third-Party Libraries
from tree_sitter import Language, Parser, Query
from lamacoopDocgen import extractFunctions
import tree_sitter_c

# Local Libraries
from lamacoopDocgen import removeComments

'''
This function uses a Tree Sitter query to grab the complete function definition
The function definition consists of the form as follows:
    
Function Signature:
    bool ftrace_pids_enabled(struct ftrace_ops *ops)
    {

Function Definition:
    ftrace_pids_enabled(struct ftrace_ops *ops)

The function accepts a string containing the code which is believed to have a 
function definition, generates a tree off of that string, and uses the query
to find the function definition.

     _ is a wildcard and * states that we want all occurances following that
form. 

    This information is placed in a dictionary with the key being the node 
type (function_definition)
and the occurance number acting as a differentiator for multiple occurances,

    This function assumes a single occurance of a definition in the provided
code with all other occurances ignored.
''' 

def functionDefinition(code: str) -> str:
    # Build and load the C grammar
    C_LANGUAGE = Language(tree_sitter_c.language())

    parser = Parser(C_LANGUAGE)

    # Parse the input C code
    source_bytes = code.encode('utf8')
    tree = parser.parse(source_bytes)
    root_node = tree.root_node

    query = Query(
        C_LANGUAGE,
        """
        (function_definition
        declarator: (_)*  @function_definition)
        """,
    )

    captures = query.captures(tree.root_node)
    try:
        return str(captures["function_definition"][0].text.decode('utf8'))
    except KeyError:
        # print("incorrect function type")
        raise 

'''
This function strips specifically the name from the function dclaration
We use it lower to produce a dictionary of function names and their comment 
files
i.e:
Function Definition:
    static inline void *alloc_tramp(unsigned long size)

Function Name:
    alloc_tramp

    This uses the same query format as above, with the main change being
node type and the variable (previously _ now identifier)

    The variable is an accessable part of the grammer from the given
tree sitter api, in this case the identifier specifies the functions name
as we intend and the declarator acts as the definition as shown above.
'''
def functionName(functionDefinition:str) -> str:
    # Build and load the C grammar
    C_LANGUAGE = Language(tree_sitter_c.language())

    parser = Parser(C_LANGUAGE)

    # Parse the input C code
    source_bytes = functionDefinition.encode('utf8')
    tree = parser.parse(source_bytes)
    root_node = tree.root_node

    query = Query(
        C_LANGUAGE,
        """
        (function_declarator
        declarator: (identifier) @name)
        """,
    )
    
    captures = query.captures(tree.root_node)
    try:
        return str(captures["name"][0].text.decode('utf8'))
    except KeyError:
        # print("incorrect function type, functionName")
        raise

'''
    For this project, first lines are used to flag a potential function
for documentation, the below simply accepts a function in an assumed 
\n line seperated form and returns the first line for code readability
'''
def extractFirstLine(function: str) -> str:
    lines: list = function.split("\n")
    return lines[0] 

'''
    The number of forward braces are used to certify the exsistance of a 
complete code block, as in congunction with the number of backward
braces we can make sure we have matching braces and that a function is 
complete
'''
def numForwardBracket(lines: list) -> int:
    numForward: int = 0
    for line in lines:
        if "{" in line:
            numForward = numForward + 1 
    return numForward

'''
    See numForwardBracket
'''
def numBackwardBracket(lines: list) -> int:
    numBackward: int = 0
    for line in lines:
        if "}" in line:
            numBackward = numBackward + 1 
    return numBackward

'''
    Acts simply to accept the lineCache list and to pass the code block
to functionName, once again for readability

    In theory a similar check, with the additional helper function as in
functionName, could be completed on any particular item, which could allow
for a strongly typed complete documentation generation program.
'''
def checkForFunction(lines: list) -> str:
    code: str = ""
    for line in lines:
        code = code + line
    try:
        return str(functionName(code))
    except KeyError as err:
        # print("Issue with lines: ", lines, {err})
        raise

'''
    Accepts a string which is assumed to be lines seperated by \n,
and extracts the lines which begin with an *, as well as certifying that
each line is left aligned and is terminated.

Operations this function completes:
    - Extracts all lines with a * as first character
    - Left aligns all valid * lines
    - Certifies the termination of the block by checking for termination
      and adding a */ if necessary
'''
def verifyCommentText(commentText: str) -> str:
    lines: list = commentText.split("\n")
    comment = ""
    for line in lines:
        line = line.strip()
        if line and (line[0] == "*" or "/**" in line):
            comment = comment + line + "\n"
    comment = comment[:-1]
    lines = comment.split("\n")
    if "*/" in lines[-1]:
        return comment + "\n"
    else:
        return comment + "\n*/\n"

'''
    Accepts a list of file lines which have been determined to begin with a 
flagged line and terminated with a matching }.

    Checks for a comment block file with a name of form;

    hashlib.sha256((("Linux" + fileName + str(code))).encode())

following the hashing convention set out for this project which was intended
to be contained within the comments themselves such as;

    echo -nE “${Project}${File_Path}${Instance}${Code}” | sha256sum

Project is linux, 

File_Path should be the full file path; however, 
time is running short on this project as of present, 

Instance had yet to be fully understood, likely the DO-178C compliance form

Code is the complete code, in this case it has been stripped and \n have been 
replaced with "" to produce reproducible hashes, as the original developer
found producing reproducible hashes a somewhat difficult venture

    If a comment block file is found it is inserted prior to the code itself
as this is where comment blocks are placed in the Linux Kernel

    Missing files are printed to standard out for verification, as it can be
difficult to resolve why a function was not placed within a given file
'''
def writeCacheToFile(lineCache: list, fileName: str):
    code = ""
    for line in lineCache:
        code = code + line.replace("\n", "").strip()
    functionHash = hashlib.sha256((("Linux" + fileName + str(code))).encode())
    functionHash = functionHash.hexdigest()
    
    try:
        with open("Functions/" + functionHash + "-ai.c", 'r') as aiFile:
            commentText = aiFile.read() + "\n"
            aiFile.close()
        commentText = verifyCommentText(commentText)
    except IOError:
        print("File:", functionHash + "-ai.c")
        commentText = ""
    except TypeError:
        commentText = ""
    except KeyError:
        commentText = ""
    with open("result/" + fileName, 'a') as commentFile:
        commentFile.write(commentText) 
        for line in lineCache:
            commentFile.write(line)
        commentFile.close()

'''
    This function acts as the main code for the program, taking all of the
above steps and producing a new file which then can be patched with
git diff --no-index ./source/ftrace.c ./result/ftrace.c > ftracedoc.patch

    The purpose of the lineCache is to fix the issue introduced by line
by line parsing, a function cannot be easily identified in a single line
therefore a list of subsequent lines is used for identification
'''
def parse(fileName: str):
    with open("source/" + fileName, 'r') as file:
        code = file.read()
    functions: list = extractFunctions(code)
    firstLines: list = [] 
    lineCache: list = []
    caching: bool = False

    for function in functions:
        firstLines.append(extractFirstLine(function))

    with open("source/" + fileName, 'r') as file:
        # opens ftrace.c and splits by line
        for line in file:

            '''
              We check to see if a line contains a } as this may be the end 
              of a function, but only if the braces match
            '''
            if caching and "}" in line:
                lineCache.append(line)
                if numForwardBracket(lineCache) == numBackwardBracket(lineCache):
                    writeCacheToFile(lineCache, fileName)
                    lineCache.clear()
                    caching = False
                    continue
                continue

            '''
            We have found a flag of a potential function, which then goes under
            review with the cache and writeCacheToFile
            '''
            if line.strip() in firstLines:
                if len(lineCache) == 0:
                    lineCache.append(line)
                    caching = True
                    continue

            if caching:
                lineCache.append(line)
            if not caching:
                with open("result/" + fileName, 'a') as commentFile:
                    commentFile.write(line)
    
    # TODO: This should be in the scope of main. Ran out of time. 
    try:
        assert(verifyCommentedFile(fileName, removeComments(str(code))))
    except AssertionError:
        print(f"Error verifying AI genned file. See file for any errors when assembling together.")

def verifyCommentedFile(fileName : str, codeInMem : str) -> bool:
    """
        Verifies that the new file created from docGen does not change program functionality
    """

    with open(f"result/{fileName}", 'r') as file:
        generatedFile = file.read()
    generatedFile= removeComments(generatedFile)
    
    generatedFile = ''.join(generatedFile.split())
    codeInMem = ''.join(codeInMem.split())

    # print(f"Code in Memory: {codeInMem[10:]}\nCode in Generated File: {generatedFile[10:]}")

    return codeInMem == generatedFile


def main():
    parser = argparse.ArgumentParser(
        prog='commentGenerator',
        description='',
        epilog='')


    parser.add_argument('filename')           # The file you want to chunk
    args = parser.parse_args()

    fileName = args.filename
    with open("result/" + fileName, 'w') as file:
        file.write("")
        file.close()
    parse(str(fileName))

if __name__ == "__main__":
    main()
