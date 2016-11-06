import requests
import re
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

oauth2client_json={
  "type": "service_account",
  "project_id": "littlefield-1285",
  "private_key_id": os.environ['PRIVATE_KEY_ID'],
  "private_key": os.environ['PRIVATE_KEY'],
  "client_email": "littlefield@littlefield-1285.iam.gserviceaccount.com",
  "client_id": "105146904148472769431",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://accounts.google.com/o/oauth2/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/littlefield%40littlefield-1285.iam.gserviceaccount.com"
}

def auth(session, institution, login, password):
    url = "http://sim.responsive.net/Littlefield/CheckAccess"
    data = {
        "institution":"tamayo" + str(institution),
        "ismobile":"false",
        "id":login,
        "password":password
    }
    r = session.post(url, data=data)
    return r.cookies["JSESSIONID"]

def print_to_document(datas, worksheet):
    #connecting to the spreadsheet
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(oauth2client_json, scope)
    gc = gspread.authorize(credentials)
    wks = gc.open_by_url(worksheet).sheet1
    #Updating data
    width = len(datas)
    height = len(datas[0])
    cell_list = wks.range('A1:' + chr(64+width) + str(height))
    for line,i in zip(datas,range(len(datas))):
        for value,j in zip(line,range(len(line))):
            cell_list[j*width+i].value = value
    # Update in batch
    wks.update_cells(cell_list)

def number(string_number):
    a = float(string_number)
    b = int(a)
    return b if a == b else a

def get_data(session, auth_cookie, data_label, fifty_only):
    #connecting to the web service
    different_requests = ["JOBOUT", "JOBT", "JOBREV"]
    url = "http://sim.responsive.net/Littlefield/Plotk?data="+data_label+"&x=all" if data_label in different_requests else "http://sim.responsive.net/Littlefield/Plot1?data="+data_label+"&plottech=html5"
    cookies = {"JSESSIONID" : auth_cookie}
    r = session.get(url, cookies=cookies)
    #parsing data
    if data_label in different_requests:
        #regex = "name=\"data[123]\" value=\"(.*?)\""
        regex = "{label: '[123]', points: '(.*?)'}"
        m = re.findall(regex, r.text)
        m = [[number(i) for i in data.split()] for data in m]
        current_day = m[-2]
        if fifty_only:
            ans = [data[1::2][-50:] for data in m]
        else:
            ans = [data[1::2] for data in m]
    else:
        regex = "{label: 'data', points: '(.*?)'}"
        m = re.search(regex, r.text)
        data_string = m.group(1)
        data = [number(i) for i in data_string.split()]
        X = [int(x) for x in data[0::2]]
        Y = data[1::2]
        if len(X) != X[-1]: #if there are several y points with the same x
            ans = ["" for i in range(X[-1])]
            for x,y in zip(X,Y):
                ans[x-1] = str(y) if ans[x-1] == "" else ans[x-1] + '&' + str(y) 
            Y = ans
        current_day = X[-1]
        if fifty_only:
            ans = [Y[-50:]]
        else:
            ans = [Y]
    return ans

def update(institution, login, password, worksheet):
    #init
    fifty_only = False
    session = requests.Session()
    auth_cookie = auth(session, institution, login, password)
    data_labels = [
        "JOBIN", "JOBQ",
        "INV",
        "S1Q", "S1UTIL", "S2Q", "S2UTIL", "S3Q", "S3UTIL",
        "CASH",
        "JOBOUT", "JOBT", "JOBREV"
    ]
    data_titles = [
        "Job arrivals", "Queued jobs",
        "Inventory",
        "S1 queue", "S1 utilisation", "S2 queue", "S2 utilisation", "S3 queue", "S3 utilisation", 
        "Cash",
        "Number of completed jobs", "Average job lead time", "Average revenue per job"
    ]
    #fill datas array
    datas = []
    
    for label,title in zip(data_labels,data_titles):
        try:
            data = get_data(session, auth_cookie, label, fifty_only)
        except Exception as ex:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print message
        if label in ["JOBOUT", "JOBT", "JOBREV"]:
            for d,i in zip(data,range(1,4)):
                datas.append([label+" ("+str(i)+")", title+" ("+str(i)+")"]+d)
        else:
            datas.append([label,title]+data[0])
    
    two_hours_from_now = datetime.now()# + timedelta(hours=2)
    timestamp = "Last update: " + '{:%H:%M:%S}'.format(two_hours_from_now)
    datas.insert(0,[timestamp,"Day"] + [str(i+1) for i in range(len(datas[0])-2)])
    print "Got data for group " + login
    #write to google sheet 
    try:
        print_to_document(datas, worksheet)
    except Exception as ex:
        template = "An exception of type {0} occured. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        print message
    print "Updated group " + login