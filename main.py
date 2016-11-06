#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import littlefield 
import datetime
from google.appengine.ext import ndb

MAIN_PAGE_HTML = """\
<html>
  <body>
    <form action="/register" method="post">
        Group (1 or 2)<br>
        <input type="text" name="institution"/><br><br>
        Team name<br>
        <input type="text" name="login"/><br><br>
        Password<br>
        <input type="password" name="password"/><br><br>
        Google Sheet URL<br>
        <input type="text" name="worksheet"/><br><br>
        <input type="submit" value="Submit">
    </form>
  </body>
</html>
"""

class Group(ndb.Model):
    """Sub model for representing an author."""
    institution = ndb.StringProperty()
    login = ndb.StringProperty()
    password = ndb.StringProperty()
    worksheet = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)
    last_update = ndb.DateTimeProperty(auto_now=True)

class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write(MAIN_PAGE_HTML)


class LittleFieldHandler(webapp2.RequestHandler):
    def get(self):
        query = Group.query()
        for group in query:
            try:
                littlefield.update(group.institution,group.login,group.password,group.worksheet)
                group.put() 
            except:
                print "Error for group " + group.login
                continue

def get_group(offset):
    groups = Group.query().order(Group.login)
    i = 0
    for group in groups:
        try:
            i += 1
            if i % 5 == offset:
                littlefield.update(group.institution,group.login,group.password,group.worksheet)
                group.put() 
        except:
            print "Error for group " + group.login
            continue

class LittleField1Handler(webapp2.RequestHandler):
    def get(self):
        get_group(0)
        
class LittleField2Handler(webapp2.RequestHandler):
    def get(self):
        get_group(1)

class LittleField3Handler(webapp2.RequestHandler):
    def get(self):
        get_group(2)

class LittleField4Handler(webapp2.RequestHandler):
    def get(self):
        get_group(3)

class LittleField5Handler(webapp2.RequestHandler):
    def get(self):
        get_group(4)

class RegisterHandler(webapp2.RequestHandler):
    def post(self):
        try:
            institution = self.request.get('institution')
            login = self.request.get('login')
            password = self.request.get('password')
            worksheet = self.request.get('worksheet')
            
            is_in_db = False
            for group in Group.query():
                if group.login == login and group.institution == institution:
                    self.response.write('<html><body>Already registered with this Google Sheet<br>'+group.worksheet+'</body></html>')
                    is_in_db = True
            if not is_in_db:
                littlefield.update(institution,login,password,worksheet)
                group = Group(
                    institution = institution,
                    login = login,
                    password = password,
                    worksheet = worksheet
                    )
                group.put()
                self.response.write('<html><body>Completed. Check your Google Sheet<br>'+worksheet+'</body></html>')

        except:
            self.response.write('<html><body>Error. Incorrect Fields</body></html>')

        

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/littlefield/1', LittleField1Handler),
    ('/littlefield/2', LittleField2Handler),
    ('/littlefield/3', LittleField3Handler),
    ('/littlefield/4', LittleField4Handler),
    ('/littlefield/5', LittleField5Handler),
    ('/littlefield', LittleFieldHandler),
    ('/register', RegisterHandler)
], debug=True)
