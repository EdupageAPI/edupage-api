import json
from io import TextIOWrapper

from edupage_api.exceptions import FailedToUploadFileException
from edupage_api.module import EdupageModule, Module, ModuleHelper


class EduCloudFile:
    def __init__(self, cloud_id: str, extension: str, file_type: str, file: str, name: str):
        self.cloud_id = cloud_id
        self.extension = extension
        self.type = file_type
        self.file = file
        self.name = name

    def get_url(self, edupage: EdupageModule):
        return f"https://{edupage.subdomain}.edupage.org{self.name}"

    @staticmethod
    def parse(data: dict):
        return EduCloudFile(
            data.get("cloudid"),
            data.get("extension"),
            data.get("type"),
            data.get("file"),
            data.get("name")
        )


class Cloud(Module):
    @ModuleHelper.logged_in
    def upload_file(self, fd: TextIOWrapper) -> EduCloudFile:
        request_url = f"https://{self.edupage.subdomain}.edupage.org/timeline/?akcia=uploadAtt"

        files = {"att": fd}

        response = self.edupage.session.post(request_url, files=files).content.decode()

        try:
            response_json = json.loads(response)
            if response_json.get("status") != "ok":
                raise FailedToUploadFileException("Edupage returned a failing status")

            metadata = response_json.get("data")
            return EduCloudFile.parse(metadata)
        except json.JSONDecodeError:
            raise FailedToUploadFileException("Failed to decode json response")
