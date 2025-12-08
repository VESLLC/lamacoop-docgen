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

