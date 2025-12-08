# Standard Libraries
import unittest

# Local Libraries
from lamacoopDocgen import validateResponse, removeComments 
from commentGenerator import verifyCommentedFile

with open('ftrace.c', 'r') as file:
    orgFile = file.read()
orgFile = removeComments(orgFile)

class testAIValidation(unittest.TestCase):
    def test_verifyCommentedFile(self):
        self.assertTrue(verifyCommentedFile('ftrace.c', orgFile))
    def test_validateResponse(self):
        inputComment = """/* event_enable_read - read from a trace event file to retrieve 
                its status.* @filp: file pointer associated with the target 
                trace event;* @ubuf: user space buffer where the event status 
                is copied to;* @cnt: number of bytes to be copied to the user 
                space buffer;* @ppos: the current position in the buffer.** 
                This is a way for user space executables to retrieve the 
                status of a* specific event** Function's expectations:* - This
                function shall lock the global event_mutex before performing 
                any* operation on the target event file and unlock it after 
                all operations on*   the target event file have completed;* - 
                This function shall retrieve the status flags from the file 
                associated*   with the target event;* - This function shall 
                format the string to report the event status to user*   space:*
                   - The first character of the string to be copied to user 
                space shall be*     set to "1" if the enabled flag is set AND 
                the soft_disabled flag is not*     set, else it shall be set 
                to "0";*   - The second character of the string to be copied to
                user space shall be*     set to "*" if either the soft_disabled
                flag or the soft_mode flag is*     set, else it shall be set to
                "\n";*   - The third character of the string to be copied to 
                user space shall b*     set to "\n" if either the soft_disabled
                flag or the soft_mode flag is*     set, else it shall be set to
                "0";*   - Any other character in the string to be copied to 
                user space shall be*     set to "0";* - This function shall 
                check if the requested cnt bytes are equal or greater*   than 
                the length of the string to be copied to user space (else a*   
                corrupted event status could be reported);* - This function 
                shall invoke simple_read_from_buffer() to perform the copy*   
                of the kernel space string to ubuf.** Returns the number of 
                copied bytes on success, -ENODEV if the event file* cannot be 
                retrieved from the input filp, -EINVAL if cnt is less than the*
                length of the string to be copied to ubuf, any error returned 
                by* simple_read_from_buffer*/""".replace('\n',' ')
        orgFunc = """event_enable_read(struct file *filp, char __user 
           *ubuf, size_t cnt,		  loff_t *ppos){	struct trace_event_file *file;	
           unsigned long flags;	char buf[4] = "0";	mutex_lock(&event_mutex);	
           file = event_file_file(filp);	if (likely(file))		
           flags = file->flags;	mutex_unlock(&event_mutex);	if (!file)		return 
           -ENODEV;	if (flags & EVENT_FILE_FL_ENABLED &&	    !(flags & 
           EVENT_FILE_FL_SOFT_DISABLED))		strcpy(buf, "1");	if 
           (flags & EVENT_FILE_FL_SOFT_DISABLED ||	    flags & 
           EVENT_FILE_FL_SOFT_MODE)		strcat(buf, "*");	strcat(buf, "\n");	
           return simple_read_from_buffer(ubuf, cnt, ppos, buf, strlen(buf));}"
           """.replace('\n','')
        
        self.assertTrue(validateResponse(inputComment, orgFunc))

if __name__ == '__main__':
    unittest.main()
