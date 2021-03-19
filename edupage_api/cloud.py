import random, string, json
from requests_toolbelt import MultipartEncoder
from edupage_api.exceptions import FailedToUploadFileException


class EduCloudFile:
    def __init__(self, uri, name, ftype, cloudid):
        self.uri = uri
        self.name = name
        self.type = ftype
        self.cloudid = cloudid


class EduCloud:
    @staticmethod
    def upload_file(edupage, fd):
        request_url = "https://" + edupage.school + ".edupage.org/timeline/?akcia=uploadAtt"

        files = {"att": fd}

        response = edupage.session.post(request_url,
                                        files=files).response.content.decode()

        try:
            response_json = json.loads(response)
            if response_json.get("status") != "ok":
                raise FailedToUploadFileException()

            metadata = response_json.get("data")
            return EduCloudFile(metadata.get("file"), metadata.get("name"),
                                metadata.get("type"), metadata.get("cloudid"))
        except:
            raise FailedToUploadFileException()
