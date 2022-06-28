import json
from server import app, log
from simple_websocket import ConnectionClosed
from werkzeug.exceptions import InternalServerError, NotFound, BadRequest, MethodNotAllowed


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
    log.error(response.data)
    response.content_type = "application/json"
    return response, 500


@app.errorhandler(MethodNotAllowed)
def handle_405(error):
    """ Return JSON instead of HTML for 405 errors. """
    response = error.get_response()
    response.data = json.dumps({
        "code": error.code,
        "name": error.name,
        "description": error.description})
    log.debug(response.data)
    response.content_type = "application/json"
    return response, 405


@app.errorhandler(NotFound)
def handle_404(error):
    """ Return JSON instead of HTML for 404 errors. """
    response = error.get_response()
    response.data = json.dumps({
        "code": error.code,
        "name": error.name,
        "description": error.description})
    response.content_type = "application/json"
    return response, 404


@app.errorhandler(BadRequest)
def handle_400(error):
    """ Return JSON instead of HTML for 400 errors. """
    response = error.get_response()
    response.data = json.dumps({
        "code": error.code,
        "name": error.name,
        "description": error.description})
    log.debug(response.data)
    response.content_type = "application/json"
    return response, 400

@app.errorhandler(ConnectionClosed)
def handle_connection_closed(error):
    """ Log unexpected websocket connection closed errors. """
    log.error(error)
    return "", 205