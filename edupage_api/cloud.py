import json
from dataclasses import dataclass
from io import TextIOWrapper

from edupage_api.exceptions import FailedToUploadFileException
from edupage_api.module import EdupageModule, Module, ModuleHelper


@dataclass
class EduCloudFile:
    cloud_id: str
    extension: str
    file_type: str
    file: str
    name: str

    def get_url(self, edupage: EdupageModule):
        """Get url of given `EduCloudFile`.

        Args:
            edupage (EdupageModule): `Edupage` object.

        Returns:
            str: Direct URL to file.
        """

        return f"https://{edupage.subdomain}.edupage.org{self.file}"

    @staticmethod
    def parse(data: dict):
        """Parse `EduCloudFile` data.

        Args:
            data (dict): Data to parse.

        Returns:
            EduCloudFile: `EduCloudFile` object.
        """

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
        """Upload file to EduPage cloud.

        The file will be hosted forever (and for free) on EduPage's servers. The file is tied to
        your user account, but anybody with a link can view it.

        **Warning!** EduPage limits file size to 50 MB and the file can have only some extensions.
        You can find all supported file extensions on this
        [Edupage help site](https://help.edupage.org/?p=u1/u113/u132/u362/u467).

        If you are willing to upload some files, you will probably have to increase the request
        timeout.

        ```
        >>> with open("image.jpg", "rb") as f:
        ...     edupage.cloud_upload(f)
        <edupage_api.cloud.EduCloudFile object at 0x10b107550>
        ```

        Args:
            fd (TextIOWrapper): File you want to upload.

        Raises:
            FailedToUploadFileException: There was a problem with uploading your file.

        Returns:
            EduCloudFile: `EduCloudFile` object.
        """

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
