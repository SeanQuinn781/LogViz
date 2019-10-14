import re

ALLOWED_EXTENSIONS = ['log', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15']
IGNORED_FILES = set(['.gitignore'])
ALLOWED_MIME_TYPES = ['application/octet-stream','text','text/x-log']

def last_2chars(x):
    return (x[-2:])


def allowedFileType(mime_type):
    if ALLOWED_MIME_TYPES and not mime_type in ALLOWED_MIME_TYPES:
        print(mime_type)
        return False


def allowedFileExtension(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

