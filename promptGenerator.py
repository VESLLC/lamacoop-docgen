# lamacoop-docgen - Python scripts for automating code and docs with LLMs
# Copyright (C) 2025 VES LLC
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# For inquiries, please contact by email:
#   info@ves.solutions
#
# Or if you prefer, by paper mail:
#   VES LLC
#   6180 Guardian Gtwy, Ste 102
#   Aberdeen Proving Ground, MD 21005

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
