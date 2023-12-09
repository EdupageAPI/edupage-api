from edupage_api import Edupage
from edupage_api.utils import RequestUtil

from pprint import pprint

import json

edupage = Edupage()
edupage.login("username", "password", "subdomain")

start = ".etestPlanBrowser("
end = ");"

print(edupage.get_user_id())
user_id = edupage.get_user_id()

gpid_call_url = f"https://{edupage.subdomain}.edupage.org/dashboard/eb.php?mode=ttday"
gpid_response = edupage.session.get(gpid_call_url)

# with open('d.html', "wb+") as f:
#     f.write(gpid_response.content)

gpid = gpid_response.text.split("gpid=")[1].split("&")[0]
gsh = gpid_response.text.split("gsh=")[1].split("\"")[0]

next_gpid = int(gpid) + 1

url = f"https://{edupage.subdomain}.edupage.org/gcall"

curriculum_response = edupage.session.post(
    url, 
    data=RequestUtil.encode_form_data({
        "gpid": f"{next_gpid}",
        "gsh": gsh,
        "action": "loadData",
        "user": edupage.get_user_id(),
        "changes": "{}",
        "date": "2023-12-07",
        "dateto": "2023-12-07",
        "_LJSL": "4096"
    }),
    headers={
        "Content-Type": "application/x-www-form-urlencoded"
    }
)

response_start = edupage.get_user_id() + "\","
response_end = ",[]);"

# with open("d.html", "wb+") as f:
    # f.write(curriculum_response.content)

# print(curriculum_response.text)
curriculum_json = curriculum_response.text.split(response_start)[1].split(response_end)[0]

with open("d.json", "wb+") as f:
    f.write(curriculum_json.encode())


j = json.loads(curriculum_json)

plan = j["dates"]["2023-12-07"]["plan"]
pprint(plan[0])


