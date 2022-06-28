from server import log


def missing(request, headers=None, data=None):
    """ Return error message about missing paramaters if there are any """
    missingHeaders = []
    missingData = []
    if headers:
        for header in headers:
            if header not in request.headers:
                log.debug(f"'{header}' not found in request headers: {request.headers}")
                missingHeaders.append(header)
    if data:
        for field in data:
            if field not in request.json:
                log.debug(f"'{field}' not found in request data: {request.json}")
                missingData.append(field)
    if not missingHeaders and not missingData:
        return None
    errMsg = "request is missing the following parameters: "
    if missingHeaders:
        errMsg += "headers=['"
        errMsg += "', '".join(missingHeaders)
        errMsg += "']"
    if missingHeaders and missingData:
        errMsg += ", "
    if missingData:
        errMsg += "data=['"
        errMsg += "', '".join(missingData)
        errMsg += "']"
    return errMsg


def missingJobForm(request, data=None):
    """ Return error message about missing paramaters if there are any """
    missingData = []
    if data:
        for field in data:
            if field not in request.form and field not in request.files:
                log.debug(f"'{field}' not found in request data: {request.form}")
                missingData.append(field)
    if not missingData:
        return None
    errMsg = "request is missing the following parameters: data=['"
    errMsg += "', '".join(missingData)
    errMsg += "']"
    return errMsg


def missingJobFields(jobJson):
    """ Return error message about missing job fields if there are any """
    requiredFields = ["executor", "filename", "description", "os"]
    missingFields = []
    for field in requiredFields:
        if field not in jobJson:
            missingFields.append(field)
    if not missingFields:
        return None
    errMsg = "the job in the request is missing the following fields: ['"
    errMsg += "', '".join(missingFields)
    errMsg += "']"
    return errMsg
