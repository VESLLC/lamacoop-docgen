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

import unittest
from lamacoopDocgen import chunkString, extractFunctions, removeComments, callAI
from promptGenerator import generate

class testDocgen(unittest.TestCase):

    def test_chunkString_basic(self):
        text = "This is a simple test of the chunking function"
        max_tokens = 4
        expected = [
            "This is a simple",
            "test of the chunking",
            "function"
        ]
        result = chunkString(text, max_tokens)
        self.assertEqual(result, expected)

    def test_chunkString_exact_fit(self):
        text = "One two three four"
        max_tokens = 4
        expected = ["One two three four"]
        result = chunkString(text, max_tokens)
        self.assertEqual(result, expected)

    def test_chunkString_single_words(self):
        text = "A B C D"
        max_tokens = 1
        expected = ["A", "B", "C", "D"]
        result = chunkString(text, max_tokens)
        self.assertEqual(result, expected)
    def test_removeComments(self):
        code = """
        // Single line comment
        int x = 0; /* Inline comment */
        /*
            Multi-line
            comment
        */
        int y = 1;
        """
        expected = '\n        \n        int x = 0; \n        \n        int y = 1;\n        '
        result = removeComments(code)
        self.assertEqual(result, expected)
    def test_extractFunctions(self):
        c_code = """
        #include <stdio.h>

        void hello() {
            printf("Hello, world!");
        }

        int add(int a, int b) {
            return a + b;
        }
        """

        functions = extractFunctions(c_code)
        self.assertEqual(len(functions), 2)
        self.assertTrue('void hello()' in functions[0])
        self.assertTrue('int add(int a, int b)' in functions[1])
    def test_callAI(self):
        promptFile = """
Fill in the above block comment with information from the following code 
For Function's expectations: provide several lines of explanation for how every combination of arguments will affect the output start each explanation with a " -"
MAKE SURE TO ALWAYS PRODUCE A C BLOCK COMMENT, only produce one block comment
                     """
        code = """
static const char *ftrace_call_replace(unsigned long ip, unsigned long addr)
{
	return text_gen_insn(CALL_INSN_OPCODE, (void *)ip, (void *)addr);
}
               """
        prompt = generate(code, promptFile)
        expected = "ftrace_call_replace - "
        response = callAI(prompt,code,False) 
        # print(response)
        self.assertTrue(expected in response)

if __name__ == '__main__':
    unittest.main()

