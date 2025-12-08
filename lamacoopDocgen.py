"""
Basic chunker with AI support. Currently only parses out functions. 
ollama requires python 3.8 or later, our Rocky machines have python3.11 installed.
Install packages with $ python3.11 -m pip install <packages>
Need to tunnel to the ollama server with a command like: 
$ ssh -L 11434:localhost:11434 lamina-ws1.int.ves.solutions
"""

# Standard Libraries
import argparse
import re
import os
import datetime
import yaml
from pathlib import Path
import time
from itertools import count
from multiprocessing import Process
import hashlib

# Third-party Libraries
from tree_sitter import Language, Parser
import tree_sitter_c
from ollama import chat
from ollama import ChatResponse

# Local Libraries
from promptGenerator import generate
from verifyAIOutput import *

TIME = datetime.datetime.now()
MODEL = "devstral"
TEMPERATURE = 0.4
PARALLELPROMPTS = 16
SECONDSTIMEOUT = 60
NUMRETRIES = 2

def chunkString(text: str, maxTokens: int) -> list[str]:
    """
    Dumb and blind chunker. Splits text into list of words, builds a list up
    to the set limit, and goes until it runs out of words.
    """
    words = text.split()
    chunks = []
    currentChunk = []
    currentTokens = 0

    for word in words:
        currentTokens += len(word.split())
        if currentTokens <= maxTokens:
            currentChunk.append(word)
        else:
            chunks.append(' '.join(currentChunk))
            currentChunk = [word]
            currentTokens = len(word.split())

    # Append the last chunk
    if currentChunk:
        chunks.append(' '.join(currentChunk))

    return chunks


def extractFunctions(c_code: str) -> list[str]:
    """
    Function mostly courtesy of ChatGPT, 
    modified to use prebuilt language definitions
    """
    # Build and load the C grammar
    C_LANGUAGE = Language(tree_sitter_c.language())

    parser = Parser(C_LANGUAGE)

    # Parse the input C code
    source_bytes = c_code.encode('utf8')
    tree = parser.parse(source_bytes)
    root_node = tree.root_node

    functions = []

    # Recursively search for function_definition nodes
    def collect_functions(node):
        if node.type == 'function_definition':
            start_byte = node.start_byte
            end_byte = node.end_byte
            func_code = source_bytes[start_byte:end_byte].decode('utf8')
            functions.append(func_code)
        for child in node.children:
            collect_functions(child)

    collect_functions(root_node)
    return functions


def removeComments(code: str) -> str:
    """
    Another ChatGPT special. Uses a regex to remove C-style comments.
    """
    pattern = re.compile(
        r'//.*?$|/\*.*?\*/',
        re.DOTALL | re.MULTILINE
    )
    return re.sub(pattern, '', code)



def callAI(prompt: str,code: str, verbose: bool) -> str:
    """
    Query OLLAMA with your prompt and the code block
    """
    content: str = prompt + "\n" + code
    if verbose:
        print("***full query:")
        print(content)

    with open("./promptContext.yaml", 'r') as f:
        context: dict = yaml.safe_load(f)

    messages: list = [{'role': 'system', 'content': \
"You are a computer programmer who makes comments, write in a c block \
comment style. Format instructions are very important, always produce a \
complete comment block beginning with a **/ and ending with */ on their own lines"},]

    Responses: dict = context['Responses']
    Prompts: dict = context['Prompts']

    responseKeys: list = list(Responses.keys())
    promptKeys: list = list(Prompts.keys())

    for prompt in promptKeys:
        messages.append({'role': 'user', 'content': Prompts[prompt]},)
    for response in Responses:
        messages.append({'role': 'assistant', 'content' : Responses[response]},)

    messages.append({'role': 'user', 'content': content})

    try:
        response: ChatResponse = chat(model=MODEL, messages=messages, 
        options={
                 'temperature': TEMPERATURE, 
                 'OLLAMA_NUM_PARALLEL': PARALLELPROMPTS, 
                 'timeout': SECONDSTIMEOUT, 
                 'max_retries': NUMRETRIES
                })
        return response.message.content
    except Exception as e:
        if(verbose):
            print("Prompt for:", code, "Failed for:", e)
        else:
            print("Prompt failed:", e)

def promptFuncs(funcs: list) -> None:
    """
    Take list of functions and optionally print them or write them to files.
    Once complete the function prompts the AI and writes the result to files as
    with the list of functions 
    """

    def functionName(functionDeclaration:str) -> str:
        specialCharacters: str = "*&@"
        codeArguments: list = re.split(r'[\(\)]+', functionDeclaration)
        functionName: str = codeArguments[0].split(" ")[-1]
        if any(c in specialCharacters for c in functionName):
            functionName = functionName[1:]
        functionName = functionName.split("\n")[-1]
        return functionName

    currentFunc = 0
    for func in funcs:
        lines = func.split("\n")
        function = ""
        for line in lines:
            function = function + line.strip()
        functionHash = hashlib.sha256((("Linux" + sourceFile + str(function))).encode())
        functionHash = functionHash.hexdigest()
        currentFunc += 1
        currentPrompt = generate(func, prompt)
        if verbose:
            print("---------------------------------------------------")
            print("Prompting func: ", currentFunc)
        if write:
            origFile = "./newFunctions/" + str(TIME) + "/" + functionHash + "-orig.c"
            os.makedirs(os.path.dirname(origFile), exist_ok=True)
            if verbose: print("Writing original function to ", origFile)
            with open(origFile, 'w') as file:
                file.write(func)

        if verbose: 
            print("Using prompt: ", currentPrompt)
            response = callAI(currentPrompt,func,verbose)
            print("response:")
            print(response)
        if write:
            modFile = "./newFunctions/" + str(TIME) + "/" + functionHash + "-ai.c"
            print("Writing modified function to ", modFile)
            with open(modFile, 'w') as file:
                try:
                    file.write(response)
                except Exception as e:
                    print("Write failed for function:", str(currentFunc), "because of:", e)

        if verbose: print("++++++++++++++++++++++++++++++++++++++++++++++++++++")


def promptDumb(chunks: list) -> None:
    """
    Take list of chunks and optionally print them or write them to file(s)
    Once complete the function prompts the AI and writes the result to files as
    with the list of functions 
    """
    currentChunk = 0
    for chunk in chunks:
        currentChunk += 1
        currentPrompt = generate(chunk, prompt)
        if verbose: 
            print("---------------------------------------------------")
            print("Prompting Chunk: ", currentChunk)
            print(chunk)
        if write:
            origFile = "./newChunks/" + str(TIME) + "/" + str(currentChunk) + "-orig.c"
            os.makedirs(os.path.dirname(origFile), exist_ok=True)
            if verbose: print("Writing original chunk to ", origFile)
            with open(origFile, 'w') as file:
                file.write(chunk)
            
        if verbose: 
            print("Using prompt: ", currentPrompt)
            response = callAI(currentPrompt,chunk,verbose)
            print("response:")
            print(response)
        if write:
            modFile = "./newChunks/" + str(TIME) + "/" + str(currentChunk) + "-ai.c"
            print("Writing modified chunk to ", modFile)
            with open(modFile, 'w') as file:
                file.write(response)
        if verbose:
            print("++++++++++++++++++++++++++++++++++++++++++++++++++++")

def getVerifierArgs(aiResponse : str, orgFunc : str) -> dict:
    """
        Retrieves data from LLM-generated responses to be used by the verifyAIOutput suite. 

        Takes in an LLM-generated response and the corresponding function from the original code
        to withdraw the fields used in the verifyAIOutput methods. Goal is to compartmentalize 
        withdrawl process and return a dict that can be reused in the future. 
    """
    commentLines : list = aiResponse.strip().split("*")
    commentTitle : str = commentLines[1]
    splitFunc : list = re.split(r'[\(\)]+', orgFunc)
    funcHeader : str = splitFunc[0]
    funcArgs : list = splitFunc[1].split(",")
    funcExpectations : list = aiResponse.split("-")

    verifierArgs : dict = dict(zip(["commentTitle", "funcHeader", "funcArgs", "funcExpectations"], 
                               [commentTitle, funcHeader, funcArgs, funcExpectations]))
    return verifierArgs

def validateResponse(aiResponse : str, orgFunc : str) -> bool:
    '''
        Validate AI responses

        Uses verifyAIOutput.py and tree-sitter to verify that AI generated responses
        follow the standards for our documentation. Fires after receiving a response
        from the ollama API.
    '''

    verifierArgs : list = getVerifierArgs(aiResponse, orgFunc)

    try:
        assert(checkCommentFormatting(aiResponse[:2], aiResponse[-2:]))
    except AssertionError:
        print(f"Error when verifying AI output on function {verifierArgs['funcHeader']}")
        print(f"The LLM generated a comment without proper header or footer")

    try:
        assert(checkFunctionHeader(verifierArgs['funcHeader'], verifierArgs['commentTitle']))
        assert(ArgumentComments(verifierArgs['funcArgs'], aiResponse.split('*')))
        assert(CommentLength(verifierArgs['funcExpectations'], verifierArgs['funcArgs']))
    except AssertionError as e:
        print(f"Error when verifying AI output on function {verifierArgs['funcHeader']}")
        print(f"AI Response: {aiResponse}")
        exit()
        
    return True

def main():
    """
    Begin Argparse stuff
    """

    parser = argparse.ArgumentParser(
        prog='lamacoop-docgen.py',
        description='',
        epilog='')


    parser.add_argument('filename')           # The file you want to chunk

    parser.add_argument('promptfile')         # The prompt you want to use

    parser.add_argument(
        '-c',
        '--chunksize',
        type=int,
        default=2000,
        help="Chunk size, default is 2000")

    parser.add_argument(
        '-d',
        '--dumb',
        action='store_true',
        help="Use the dumb chunker instead of the smart function chunker")

    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help="Verbose mode, print everything we are doing")  # on/off flag

    parser.add_argument(
        '-w',
        '--write',
        action='store_true',
        help="Write modified and unmodified functions to files")

    parser.add_argument(
        '-k',
        '--keepcomments',
        action='store_true',
        help="Don't remove comments from source code before passing them to the AI")

    args = parser.parse_args()

    chunkSize = args.chunksize

    global verbose 
    verbose = args.verbose

    verbose = True  # Forcing this to be true for now

    global write 
    write = args.write

    keepComments = args.keepcomments

    dumbChunker = args.dumb

    textFile = args.filename

    promptFile = args.promptfile


    """
    End Argparse stuff
    """

    """
    Globally open files
    """

    with open(textFile, 'r') as file:
        fileContent = file.read()
        
    with open(promptFile, 'r') as promptfile:
        promptContent = promptfile.read()

    global sourceFile
    sourceFile = textFile

    global text
    text = str(fileContent)

    global prompt
    prompt = str(promptContent)

    # Remove comments before chunking (default)
    if not keepComments:
        textNoComments = removeComments(text)
        code = removeComments(text)
    else:
        code = text

    if dumbChunker:
        print("Using dumb chunking, chunk size: ", chunkSize)
        chunks = chunkString(code, chunkSize)
        print("Total Chunks: ", len(chunks))
        promptDumb(chunks)

    else:
        print("Using smart chunking.")
        funcs = extractFunctions(code)
        print(len(funcs), " functions extracted")
        promptFuncs(funcs)



if __name__ == "__main__":
    main()
