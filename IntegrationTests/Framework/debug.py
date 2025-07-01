def debug(message, DEBUG):
    """
    Take a string as a mesasage and output if DEBUG is true
    """
    if (DEBUG is True):
        print(message)

def debugList(messageList, DEBUG, prefix="", postfix=""):
    """
    Take a list of messages and output if DEBUG is true, with a prefix and a postfix
    """
    if (DEBUG is True):
        for message in messageList:
            print(prefix+str(message)+postfix)