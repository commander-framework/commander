import json
from server import app
from werkzeug.exceptions import InternalServerError, NotFound


class CommanderError(Exception):
    """ Base class for all exceptions in this module. """
    pass


class CAPyError(CommanderError):
    """ Exception raised for errors while interacting with the CAPy API. """
    pass


class GitHubError(CommanderError):
    """ Exception raised for errors while interacting with GitHub. """
    pass


@app.errorhandler(InternalServerError)
def handle_500(error):
    """ Return JSON instead of HTML for 500 errors. """
    response = error.get_response()
    response.data = json.dumps({
        "code": error.code,
        "name": error.name,
        "description": error.description})
    response.content_type = "application/json"
    return response


@app.errorhandler(NotFound)
def handle_404(error):
    """ Return JSON instead of HTML for 404 errors. """
    response = error.get_response()
    response.data = json.dumps({
        "code": error.code,
        "name": error.name,
        "description": error.description})
    response.content_type = "application/json"
    return response