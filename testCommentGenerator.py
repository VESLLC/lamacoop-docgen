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
import os.path

from commentGenerator import functionName, parse
function = """
void ftrace_arch_code_modify_prepare(void)
__acquires(&text_mutex)
{
    /*
    * Need to grab text_mutex to prevent a race from module loading
    * and live kernel patching from changing the text permissions while
    * ftrace has it set to "read/write".
    */
    mutex_lock(&text_mutex);
    ftrace_poke_late = 1;
}
"""
class testCommentGenerator(unittest.TestCase):

    #functionDeclaration, hangingPart
    #functionName
    def test_functionName(self):
        expected = "ftrace_arch_code_modify_prepare" 
        result = functionName(function)
        self.assertEqual(result, expected)

    #No Return
    def test_parse(self):
        parse("ftrace.c")
        self.assertTrue(os.path.isfile("./result/ftrace.c"))

if __name__ == '__main__':
    unittest.main()

