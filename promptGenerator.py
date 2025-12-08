import re

def generate(function: str, promptText: str) -> str:
    specialCharacters: str = "*&@"
    prompt: str = "/**\n" 
    code = function 
    codeArguments: list = re.split(r'[\(\)]+', code)
    functionArguments: list = codeArguments[1].split(",")
    numArguments: int = len(functionArguments)

    functionName: str = codeArguments[0].split(" ")[-1]
    if any(c in specialCharacters for c in functionName):
        functionName = functionName[1:]
    prompt = prompt + "* " + functionName + " - description of the function\n"
    for argument in functionArguments:
        argument: list = argument.split(" ")
        argument: str = argument[len(argument)-1] 
        # print("Argument: ", argument, i, "CommentLine: ", commentLines[i])

        '''
        Acts to check if there are any matching characters between 
        specialCharacters and the argument string, trying to remove markers
        from function arguments
        '''
        if any(c in specialCharacters for c in argument):
            argument = argument[1:]
        prompt = prompt + "* @" + argument + ": description of the argument\n"
    prompt = prompt + "*\n* Functions Expectations:\n* -\n* -\n* -\n* -\n*" \
                     " -\n* -\n* -\n* -\n* -\n* -\n*/\n"
    prompt = prompt + promptText 
    
    # The current implementation adds the code to the prompt already
    # prompt = prompt + function
    return prompt
