import os


class uploadfile:
    def __init__(self, name, type=None, size=None, not_allowed_msg=""):
        self.name = name
        self.type = type
        self.size = size
        self.not_allowed_msg = not_allowed_msg
        self.url = "data/%s" % name
        # self.thumbnail_url = "thumbnail/%s" % name
        self.delete_url = "delete/%s" % name
        self.delete_type = "DELETE"

    def get_file(self):

        print("in get file upload_file.py")
        # POST an normal file
        if self.not_allowed_msg == "":
            return {
                "name": self.name,
                "type": self.type,
                "size": self.size,
                "url": self.url,
                "deleteUrl": self.delete_url,
                "deleteType": self.delete_type,
            }

        # File type is not allowed
        else:
            return {
                "error": self.not_allowed_msg,
                "name": self.name,
                "type": self.type,
                "size": self.size,
            }
