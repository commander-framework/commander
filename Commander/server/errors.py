class CommanderError(Exception):
    """ Base class for all exceptions in this module. """
    pass

class CAPyError(CommanderError):
    """ Exception raised for errors while interacting with the CAPy API. """
    pass

class GitHubError(CommanderError):
    """ Exception raised for errors while interacting with GitHub. """
    pass