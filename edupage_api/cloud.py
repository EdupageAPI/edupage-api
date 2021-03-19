import random, string, json
from requests_toolbelt import MultipartEncoder

class EduCloudFile:
    def __init__(self, uri, name, ftype, cloudid):
        self.uri = uri
        self.name = name
        self.type = ftype
        self.cloudid = cloudid
        

class EduCloud:
    @staticmethod
    def upload_file(edupage, data, filename, ftype):
        request_url = "https://" + edupage.school + ".edupage.org/timeline?akcia=uploadAtt"

        fields = {
            "file": (f"'{filename}'", data, ftype),
            "file_id": "0"
        }

        boundary = "----WebKitFormBoundary" + ''.join(random.sample(string.ascii_letters + string.digits, 16))
        mfile = MultipartEncoder(fields = fields, boundary = boundary)

        headers = {
            "Connection": "keep-alive",
            "Content-Type": mfile.content_type,
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }



        response = edupage.session.post(request_url, headers=headers, data=mfile)
        try:
            json.loads(response.content.decode())
            print("Success!")
        except:
            print("Failed:(")