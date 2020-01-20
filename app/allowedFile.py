import re


IGNORED_FILES = set([".gitignore"])
ALLOWED_MIME_TYPES = ["application/octet-stream", "text", "text/x-log"]


def allowedFileExtension(filename):
    # regex for nginx access logs:
    regex = r"\W*(access.log.[1-9]|[1-8][0-9]|9[0-9]|100)\W*"

    if re.search(regex, filename) or filename == "access.log":
        return True
    else:
        return False


def last_2chars(x):
    return x[-2:]


def allowedFileType(mime_type):
    if ALLOWED_MIME_TYPES and not mime_type in ALLOWED_MIME_TYPES:
        return False
