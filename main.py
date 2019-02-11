#!/usr/bin/env python

# Copyright 2016 Google Inc.
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

# [START imports]
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import os
import urllib
import json
import logging
import calendar

from google.appengine.api import users
from google.appengine.ext import ndb

import datetime
import jinja2
import webapp2
import MySQLdb
from keys import *

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape', 'jinja2.ext.do'],
    autoescape=True)
# [END imports]

UTCoffset = 7


# /* ------------------ Object Classes --------------------- */
def isfloat(value):
  try:
    float(value)
    return True
  except:
    return False

def now(offset = 7):
  return datetime.datetime.now() -  datetime.timedelta(hours = offset)

class Session():      
  def __init__(self, user = None, request = None, getdb = True, getAdminTable = True):
    self.user = user
    self.request = request
    self.loginurl = ""
    self.logintext = ""
    self.adminpassword = ""
    self.authorizedusers = []
    if getdb:
      self.db = self.connectDB()
      if getAdminTable:
        self.getAdminTable()
        self.admin = self.getAdmin()
    self.getURL()
  
  def getURL(self):
    if self.admin:
      self.loginurl = users.create_logout_url(self.request.uri)
      self.logintext = 'Logout'
    elif self.user:
      self.loginurl = users.create_logout_url(self.request.uri)
      self.logintext = 'Logout of ' + self.user.email()
    else:
      try:
        self.loginurl = users.create_login_url(self.request.uri)
        self.logintext = 'Login'
      except:
        pass

  def getAdmin(self):
    if self.user:
      if self.user.email() in self.authorizedusers:
        self.user = None
        return True
    return False

  def connectDB(self):
    if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/'):
      db = MySQLdb.connect(
        unix_socket='/cloudsql/{}:{}:{}'.format(
            CLOUDSQL_PROJECT,
            CLOUDSQL_REGION,
            CLOUDSQL_INSTANCE),
        host = CLOUDSQL_HOST, 
        db = CLOUDSQL_DB, 
        user = CLOUDSQL_USER, 
        passwd = CLOUDSQL_PASSWD)
    else:
      db = MySQLdb.connect(
        host = "localhost", 
        db = CLOUDSQL_DB, 
        user = CLOUDSQL_USER, 
        passwd = CLOUDSQL_PASSWD)
    return db

  def getAdminTable(self):
    c = self.db.cursor()
    
    c.execute("SELECT type, value FROM admin")
    rows = c.fetchall()
    c.close()
    
    for row in rows:
      if row[0] == "password":
        self.adminpassword = row[1]
      elif row[0] == "authorized_user":
        self.authorizedusers.append(row[1])

class CategoryID():
  def __init__(self, id=None, tablename = None):
    self.tablename = tablename
    self.id = id
    self.category = None
    self.display = None

  def find(self, db, id, tablename):
    c = db.cursor()
    self.id = id
    self.tablename = tablename
    c.execute("SELECT COUNT(*) FROM " + self.tablename + " WHERE id = %s", (self.id,))
    count = c.fetchall()[0][0]
    c.close()
    if count == 0:
      return
    elif count == 1:
      self.get(db = db)

    return
  
  def get(self, db):
    # This should only be called by self.find which does all of the error checking
    c = db.cursor()
    c.execute("SELECT id, " + self.tablename + ", display FROM " + self.tablename + " WHERE id = %s", (self.id,))

    c.close()
    self.fill(c.fetchall()[0])
    
  def fill(self, row):
    # This should only be called by self.get or getCategories which do all of the error checking
    if row[0]:
      self.id = row[0]
    if row[1]:
      self.category = row[1]
    if row[2]:
      self.display = row[2]

class Household():
  def __init__(self, id=None):
    self.id = id
    self.address1 = None
    self.address2 = None
    self.city = None
    self.state = None
    self.zip = None
    self.phone = None
    self.email = None
    self.email2 = None
    self.googleid = None
    self.income = None
    self.picturewaiver = None   #tinyint(1)
    self.lanl = None            #tinyint(1)
    self.library = None         #tinyint(1)
    self.sponsor = None         #date
    self.fix = None             #tinyint(1)
    self.created = None    #datetime
    self.modified = None         #datetime
    self.patrons = []  
    self.communicationids = []
    self.tooold = False
  
  def find(self, db, id = None, user = None, email = None, update = False):
    c = db.cursor()
    if id:
      c.execute("SELECT COUNT(*) FROM household WHERE id = %s", (id,))
      count = c.fetchall()[0][0]
      if count == 1:
        self.get(id = id, db = db, update = update)
        c.close()
        return

    if user:
      c.execute("SELECT COUNT(*) FROM household WHERE googleid = %s", (user.user_id(),))
      count = c.fetchall()[0][0]
      if count == 1:
        self.get(googleid = user.user_id(), db = db, update = update)
        c.close()
        return

      c.execute("SELECT COUNT(*) FROM household WHERE email = %s", (user.email(),))
      count = c.fetchall()[0][0]
      if count == 1:
        self.get(email = user.email(), db = db, update = update)
        c.close()
        return
      
      c.execute("SELECT COUNT(*) FROM household WHERE email2 = %s", (user.email(),))
      count = c.fetchall()[0][0]
      if count == 1:
        self.get(email2 = user.email(), db = db, update = update)
        c.close()
        return

    if email:
      c.execute("SELECT COUNT(*) FROM household WHERE email = %s", (email,))
      count = c.fetchall()[0][0]
      if count == 1:
        self.get(email = email, db = db, update = update)
        c.close()
        return
        
      c.execute("SELECT COUNT(*) FROM household WHERE email2 = %s", (email,))
      count = c.fetchall()[0][0]
      if count == 1:
        self.get(email2 = email, db = db, update = update)
        c.close()
        return

  def get(self, db, id = None, googleid = None, email = None, email2 = None, update = False):
    # This should only be called by fetchHousehold which does all of the error checking
    
    c = db.cursor()

    if id:
      c.execute("SELECT id, address1, address2, city, state, zip, phone, email, email2, googleid, income, picturewaiver, lanl, library, sponsor, fix, CAST(created AS DATE), CAST(modified AS DATE) FROM household WHERE id = %s", (id,))
    elif googleid:
      c.execute("SELECT id, address1, address2, city, state, zip, phone, email, email2, googleid, income, picturewaiver, lanl, library, sponsor, fix, CAST(created AS DATE), CAST(modified AS DATE) FROM household WHERE googleid = %s", (googleid,))
    elif email:
      c.execute("SELECT id, address1, address2, city, state, zip, phone, email, email2, googleid, income, picturewaiver, lanl, library, sponsor, fix, CAST(created AS DATE), CAST(modified AS DATE) FROM household WHERE email = %s", (email,))
    elif email2:
      c.execute("SELECT id, address1, address2, city, state, zip, phone, email, email2, googleid, income, picturewaiver, lanl, library, sponsor, fix, CAST(created AS DATE), CAST(modified AS DATE) FROM household WHERE email2 = %s", (email2,))

    self.fill(c.fetchall()[0])
    c.close()
    if not update:
      self.getPatrons(db = db)
      self.getCommunicationIDs(db = db)
    return
    
  def fill(self, row, update = False):

    self.id = row[0]
    if row[1]:
      self.address1 = row[1]
    if row[2]:
      self.address2 = row[2]
    if row[3]:
      self.city = row[3]
    if row[4]:
      self.state = row[4]
    if row[5]:
      self.zip = row[5]
    if row[6]:
      self.phone = row[6]
    if row[7]:
      self.email = row[7]
    if row[8]:
      self.email2 = row[8]
    if row[9]:
      self.googleid = row[9]
    if row[10]:
      self.income = row[10]
    if row[11]:
      self.picturewaiver = row[11]
    if row[12]:
      self.lanl = row[12]
    if row[13]:
      self.library = row[13]
    if row[14]:
      self.sponsor = row[14]
    if row[15]:
      self.fix = row[15]
    if row[16]:
      self.created = row[16]
    if row[17]:
      self.modified = row[17]
    
    if not self.modified:
      if self.created < now().date() - datetime.timedelta(365):
        self.tooold = True
      if self.created < datetime.date(2016, 10, 1):
        self.tooold = True
    elif self.modified < now().date() - datetime.timedelta(365):
      self.tooold = True
    
    return

  def put(self, db):
    c = db.cursor()
    
    with db:
      if self.id:
        c.execute("INSERT INTO household \
            (id, address1, address2, city, state, zip, phone, email, email2, googleid, income, picturewaiver, lanl, library, sponsor, fix) \
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)\
            ON DUPLICATE KEY UPDATE \
            modified = NOW(), address1 = VALUES(address1), address2 = VALUES(address2), city = VALUES(city), state = VALUES(state), zip = VALUES(zip), phone = VALUES(phone), email = VALUES(email), email2 = VALUES(email2), googleid = VALUES(googleid), income = VALUES(income), picturewaiver = VALUES(picturewaiver), lanl = VALUES(lanl), library = VALUES(library), sponsor = VALUES(sponsor), fix = VALUES(fix) ", \
            (self.id, self.address1, self.address2, self.city, self.state, self.zip, self.phone, self.email, self.email2, self.googleid, self.income, self.picturewaiver, self.lanl, self.library, self.sponsor, self.fix))
      else:
        c.execute("INSERT INTO household \
            (address1, address2, city, state, zip, phone, email, email2, googleid, income, picturewaiver, lanl, library, sponsor, fix) \
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", \
            (self.address1, self.address2, self.city, self.state, self.zip, self.phone, self.email, self.email2, self.googleid, self.income, self.picturewaiver, self.lanl, self.library, self.sponsor, self.fix))
            
        c.execute("select last_insert_id()")
        self.id  = c.fetchall()[0][0]
    
    c.close()
    return
  
  def update(self, request, db, user = None, response = None):
    
    id = request.get('id')
    email = request.get('email')
    email2 = request.get('email2')
    
    if id:
      self.find(db = db, id = id, update = True)
    if not self.id and user:
      self.find(db = db, user = user, update = True)
    if not self.id and email:
      self.find(db = db, email = email, update = True)
    if not self.id and email2:
      self.find(db = db, email = email2, update = True)
        
    self.address1 = request.get('address1')
    self.address2 = request.get('address2')
    self.city = request.get('city')
    self.state = request.get('state')
    self.zip = request.get('zip')
    self.phone = request.get('phone')
    self.email = email if email else None
    self.email2 = email2 if email2 else None
    self.income = request.get('income')
    self.picturewaiver = request.get('photo') if request.get('photo').isdigit() else 0
    self.lanl = request.get('lanl') if request.get('lanl').isdigit() else 0
    
    if request.get('adminpatron'):
      self.fix = 1 if request.get('fix') else False
      self.library = 1 if request.get('library') else False
      self.sponsor = request.get('sponsor') if request.get('sponsor') else None
      if request.get('addpatron'):
        c = db.cursor()
        c.execute("SELECT COUNT(*) FROM patron WHERE id = %s", (request.get('addpatron'),))
        count = c.fetchall()[0][0]
        if count == 1:
          with db:
            c.execute("INSERT IGNORE INTO patronhash (patronid, householdid) VALUES (%s, %s)", (str(request.get('addpatron')), self.id))
        c.close()
        
    else:
      self.fix = False
    
    if user:      
      self.googleid = user.user_id()
    elif not self.googleid and self.email:
      try:
        tempuser = users.User(email = self.email)
        if tempuser.user_id():
          self.googleid = tempuser.user_id()
      except:
        pass
    
    self.put(db)
    self.updatePatrons(db = db, request = request, response = response)
    self.updateCommunications(db = db, request = request, response = response)
      
    return
  
  def getPatrons(self, db):
    c = db.cursor()
    
    c.execute("SELECT patronid FROM patronhash WHERE householdid = %s", (self.id,))
    patronids = c.fetchall()
    c.close()
    for patronid in patronids:
      patron = Patron()
      patron.find(db = db, id = patronid[0])
      self.patrons.append(patron)
    
    return
    
  def updatePatrons(self, db, request, response = None):
    patronids = request.get_all('patronid')
    firsts = request.get_all('first')
    lasts = request.get_all('last')
    birthyears = request.get_all('birthyear')
    genders = request.get_all('gender')
    ethnicities = request.get_all('ethnicity')
    deletes = request.get_all('delete')
    
    
    for index, patronid in enumerate(patronids):
      patron = Patron()
      if patronid and deletes[index] == "True":
        patron.find(db = db, id = patronid)
        patron.delete(db = db, householdid = self.id)
        continue
      elif patronid:
        patron.id = patronid
      elif firsts[index] in ["None", ""] and lasts[index] in ["None", ""]:
        continue
      elif not patronid and deletes[index] == "True":
        continue
      
      patron.first = "" if firsts[index] == "None" else firsts[index]
      patron.last = "" if lasts[index] == "None" else lasts[index]
      patron.birthyear = birthyears[index] if birthyears[index].isdigit() else 0
      patron.gender = genders[index] if genders[index].isdigit() else 0
      patron.ethnicity = ethnicities[index] if ethnicities[index].isdigit() else 0
      
      patron.put(db = db, householdid = self.id)
      self.patrons.append(patron)
      
    return
    
  def getCommunicationIDs(self, db):
    c = db.cursor()
    
    c.execute("SELECT communicationid FROM communicationhash WHERE householdid = %s", (self.id,))
    communicationids = c.fetchall()
    c.close()
    for communicationid in communicationids:
      self.communicationids.append(communicationid[0])
    
    return
    
  def updateCommunications(self, db, request, response = None):
    communications = getCommunications(db)
    
    for communication in communications:
      if communication.display:
        if request.get('communication' + str(communication.id) ):
          communication.addHousehold(db = db, householdid = self.id)
          self.communicationids.append(communication.id)
        else:
          communication.deleteHousehold(db = db, householdid = self.id)
      
      
    return
    
class Patron():
  def __init__(self, id=None):
    self.id = id
    self.first = None
    self.last = None
    self.birthyear = None
    self.gender = None
    self.ethnicity = None
  
  def find(self, db, id = None):
    c = db.cursor()
    if id:
      self.id = id
      c.execute("SELECT COUNT(*) FROM patron WHERE id = %s", (self.id,))
      count = c.fetchall()[0][0]
      c.close()
      if count == 1:
        self.get(id = self.id, db = db)
        return
  
  def get(self, db, id = None):
    # This should only be called by fetchHousehold which does all of the error checking
    
    c = db.cursor()

    if id:
      c.execute("SELECT id, first, last, birthyear, gender, ethnicity FROM patron WHERE id = %s", (id,))

    self.fill(c.fetchall()[0])
    c.close()

    return

  def fill(self, row):
    # This is called by get or by getPatrons

    self.id = str(row[0])
    if row[1]:
      self.first = str(row[1])
    if row[2]:
      self.last = str(row[2])
    if row[3]:
      self.birthyear = str(row[3])
    if row[4]:
      self.gender = str(row[4])
    if row[5]:
      self.ethnicity = str(row[5])

    return

  def put(self, db, householdid = None):
    c = db.cursor()
    
    with db:
      if self.id:
        c.execute("REPLACE INTO patron (id, first, last, birthyear, gender, ethnicity) VALUES (%s, %s, %s, %s, %s, %s)", (self.id, self.first, self.last, self.birthyear, self.gender, self.ethnicity))
      else:
        c.execute("INSERT INTO patron (id, first, last, birthyear, gender, ethnicity) VALUES (%s, %s, %s, %s, %s, %s)", (self.id, self.first, self.last, self.birthyear, self.gender, self.ethnicity))
        c.execute("select last_insert_id()")
        self.id  = c.fetchall()[0][0]
    c.close()
        
    if householdid:
      self.addHousehold(db = db, householdid = householdid)
    
    return
  
  def addHousehold(self, db, householdid):
    c = db.cursor()
    with db:
      c.execute("INSERT IGNORE INTO patronhash (patronid, householdid) VALUES (%s, %s)", (str(self.id), householdid))
    c.close()
    
  def getHouseholds(self, db):
    c = db.cursor()
    with db:
      c.execute("SELECT householdid FROM patronhash WHERE patronid = %s", (str(self.id), ))
    
    households = []
    hids = c.fetchall()
    c.close()
    for household in hids:
      households.append(str(household[0]))
    
    return households

  def delete(self, db, householdid = None):
    c = db.cursor()
    with db:
      c.execute("DELETE FROM patronhash WHERE patronid = %s AND householdid = %s", (str(self.id), householdid))
    c.close()
    return
    
  def dict(self, db):
    dict = {}
    dict['id'] = self.id
    dict['first'] = unicode(self.first, errors='ignore') if self.first else ""
    dict['last'] = unicode(self.last, errors='ignore') if self.last else ""
    dict['birthyear'] = self.birthyear
    dict['gender'] = self.gender
    dict['ethnicity'] = self.ethnicity
    dict['households'] = self.getHouseholds(db = db)
    
    return dict
  
class Communication():
  def __init__(self, id=None):
    self.id = id
    self.name = None
    self.description = None
    self.display = None
  
  def find(self, db, id = None):
    c = db.cursor()
    if id:
      self.id = id
      c.execute("SELECT COUNT(*) FROM communication WHERE id = %s", (self.id,))
      count = c.fetchall()[0][0]
      c.close()
      if count == 1:
        self.get(id = self.id, db = db)
        return
  
  def get(self, db, id = None):
    # This should only be called by fetchHousehold which does all of the error checking
    
    c = db.cursor()

    if id:
      c.execute("SELECT id, name, description, display FROM communication WHERE id = %s", (id,))

    c.close()
    self.fill(c.fetchall()[0])
    
  def fill(self, row):
    self.id = row[0]
    if row[1]:
      self.name = row[1]
    if row[2]:
      self.description = row[2]
    if row[3]:
      self.display = row[3]
    return

  def put(self, db, householdid = None):
    c = db.cursor()
    
    with db:
      if self.id:
        c.execute("REPLACE INTO communication (id, name, description, display) VALUES (%s, %s, %s, %s)", (self.id, self.name, self.description, self.display))
      else:
        c.execute("INSERT INTO communication (id, name, description, display) VALUES (%s, %s, %s, %s)", (self.id, self.name, self.description, self.display))
        c.execute("select last_insert_id()")
        self.id  = c.fetchall()[0][0]
    c.close()    
    if householdid:
      self.addHousehold(db = db, householdid = householdid)
    
    return
      
  def addHousehold(self, db, householdid):
    c = db.cursor()
    with db:
      c.execute("INSERT IGNORE INTO communicationhash (communicationid, householdid) VALUES (%s, %s)", (str(self.id), str(householdid)))
      print "INSERT IGNORE INTO communicationhash (communicationid, householdid) VALUES (" + str(self.id) + ", " + str(householdid) + ")"
    c.close()
    
  def deleteHousehold(self, db, householdid = None):
    c = db.cursor()
    with db:
      c.execute("DELETE FROM communicationhash WHERE communicationid = %s AND householdid = %s", (str(self.id), householdid))
    c.close()
    return

class Event():
  def __init__(self, id=None):
    self.id = id              # int(11)
    self.name = ""            # varchar(100)
    self.description = ""     # text
    self.instructor = ""     # varchar(40)
    self.cost = 0             # varchar(10)
    self.highlight = False    # tinyint(1)
    self.archive = False      # tinyint(1)
    self.alwaysshow = False      # tinyint(1)
    self.sessions = []  
    self.instances = []
    self.recurrences = []
    self.sessionidhash = {}   # self.sessionidhash['oldid'] = newid
  
  def find(self, db, id = None, update=False):
    c = db.cursor()
    if id:
      c.execute("SELECT COUNT(*) FROM event WHERE id = %s", (id,))
      count = c.fetchall()[0][0]
      if count == 1:
        self.get(id = id, db = db, update = update)
        c.close()
        return

  def get(self, db, id, update = False):
    # This should only be called by fetchHousehold which does all of the error checking
    
    c = db.cursor()
    c.execute("SELECT id, name, description, instructor, cost, highlight, archive, alwaysshow FROM event WHERE id = %s", (id,))

    self.fill(c.fetchall()[0])
    c.close()
    if not update:
      self.getSessions(db = db)
      self.getInstances(db = db)
      self.getRecurrences(db = db)
    return
    
  def fill(self, row):
    self.id = row[0]
    if row[1]:
      self.name = row[1]
    if row[2]:
      self.description = row[2]
    if row[3]:
      self.instructor = row[3]
    if row[4]:
      self.cost = row[4]
    if row[5]:
      self.highlight = row[5]
    if row[6]:
      self.archive = row[6]
    if row[7]:
      self.alwaysshow = row[7]
    
    return

  def put(self, db):
    c = db.cursor()
    
    with db:
      if self.id:
        c.execute("REPLACE INTO event (id, name, description, instructor, cost, highlight, archive, alwaysshow) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (self.id, self.name, self.description, self.instructor, self.cost, self.highlight, self.archive, self.alwaysshow))
      else:
        c.execute("INSERT INTO event (name, description, instructor, cost, highlight, archive, alwaysshow) VALUES (%s, %s, %s, %s, %s, %s, %s)", (self.name, self.description, self.instructor, self.cost, self.highlight, self.archive, self.alwaysshow))
        c.execute("select last_insert_id()")
        self.id  = c.fetchall()[0][0]
    
    c.close()
    return
  
  def update(self, request, db, user = None, response = None):
    
    id = request.get('id')
    
    if id:
      self.find(db = db, id = id, update = True)
    
    self.name = request.get('name')
    self.description = request.get('description')
    self.instructor = request.get('instructor')
    self.cost = request.get('cost') if isfloat(request.get('cost')) else 0
    self.highlight = 1 if request.get('highlight') else 0
    self.archive = 1 if request.get('archive') else 0
    self.alwaysshow = 1 if request.get('alwaysshow') else 0
    
    self.put(db)
    self.updateSessions(db = db, request = request, response = response)
    self.updateInstances(db = db, request = request, response = response)
    self.updateRecurrences(db = db, request = request, response = response)
      
    return
  
  def getSessions(self, db):
    c = db.cursor()
    
    c.execute("SELECT id, eventid, name, instructor, location, cost, notes, archive, cancel FROM eventsession WHERE eventid = %s", (self.id,))
    rows = c.fetchall()
    c.close()
    for row in rows:
      session = EventSession()
      session.fill(row)
      self.sessions.append(session)
    
    return

  def getInstances(self, db):
    c = db.cursor()
    
    c.execute("SELECT id, sessionid, eventid, name, date, starttime, endtime, instructor, cost, notes, deleted, cancel FROM eventinstance WHERE eventid = %s", (self.id,))
    rows = c.fetchall()
    c.close()
    for row in rows:
      instance = EventInstance()
      instance.fill(row)
      self.instances.append(instance)
    
    return
    
  def getRecurrences(self, db):
    c = db.cursor()
    
    c.execute("SELECT id, sessionid, eventid, name, style, dayofweek, weekofmonth, startdate, enddate, starttime, endtime FROM eventrecurrence WHERE eventid = %s", (self.id,))
    rows = c.fetchall()
    c.close()
    for row in rows:
      recurrence = EventRecurrence()
      recurrence.fill(row)
      self.recurrences.append(recurrence)
    
    return

  def updateSessions(self, db, request, response = None):
    sessionids = request.get_all('sessionid')
    names = request.get_all('sname')
    instructors = request.get_all('sinstructor')
    locations = request.get_all('slocation')
    costs = request.get_all('scost')
    notess = request.get_all('snotes')
    
    
    for index, sessionid in enumerate(sessionids):
      session = EventSession()
      if sessionid.isdigit():
        session.id = sessionid
      
      session.eventid = self.id
      session.name = names[index] if names[index] else ""
      session.instructor = instructors[index] if instructors[index] else ""
      session.location = locations[index] if locations[index] else ""
      session.cost = costs[index] if isfloat(costs[index]) else 0
      session.notes = notess[index] if notess[index] else ""
      
      session.put(db = db)
      self.sessions.append(session)
      self.sessionidhash[sessionid] = session.id
      
    return

  def updateInstances(self, db, request, response = None):
    instanceids = request.get_all('instanceid')
    sessionids = request.get_all('isessionid')
    names = request.get_all('iname')
    dates = request.get_all('idate')
    starttimes = request.get_all('istarttime')
    endtimes = request.get_all('iendtime')
    instructors = request.get_all('iinstructor')
    costs = request.get_all('icost')
    notess = request.get_all('inotes')
    cancels = request.get_all('icancel')
    
    
    for index, instanceid in enumerate(instanceids):
      instance = EventInstance()
      if instanceid:
        instance.id = instanceid
      elif dates[index] in ["None", ""]:
        continue
      
      instance.eventid = self.id
      instance.sessionid = self.sessionidhash[sessionids[index]] if sessionids[index] else None
      instance.name = names[index] if names[index] else ""
      instance.date = dates[index] if dates[index] else ""
      instance.starttime = starttimes[index] if starttimes[index] else ""
      instance.endtime = endtimes[index] if endtimes[index] else ""
      instance.instructor = instructors[index] if instructors[index] else ""
      instance.cost = costs[index] if isfloat(costs[index]) else 0
      instance.notes = notess[index] if notess[index] else ""
      instance.cancel = cancels[index]
      
      instance.put(db = db)
      self.instances.append(instance)
      
    return
    
  def updateRecurrences(self, db, request, response = None):
    index = 1
    applyrindex = request.get('applyrindex')
    logging.info("applyrindex: " + applyrindex)
    while (request.get_all('rname' + str(index))):
      recurrence = EventRecurrence()
      rname = request.get('rname' + str(index))
      rid = request.get('rid' + str(index))
      rsession = request.get('rsession' + str(index))
      rstyle = request.get('rstyle' + str(index))
      rweekofmonth = request.get_all('rweekofmonth' + str(index))
      rdayofweek = request.get_all('rdayofweek' + str(index))
      rstartdate = request.get('rstartdate' + str(index))
      renddate = request.get('renddate' + str(index))
      rstarttime = request.get('rstarttime' + str(index))
      rendtime = request.get('rendtime' + str(index))
      
      recurrence.id = rid
      recurrence.eventid = self.id if self.id else None
      recurrence.name = rname
      recurrence.sessionid = rsession if rsession else None
      recurrence.style = rstyle
      for wom in rweekofmonth:
        recurrence.weekofmonth.append(wom[4:-len(str(index))])
      for dow in rdayofweek:
        recurrence.dayofweek.append(dow[4:-len(str(index))])
      recurrence.startdate = rstartdate if rstartdate else None
      recurrence.enddate = renddate if renddate else None
      recurrence.starttime = rstarttime if rstarttime else None
      recurrence.endtime = rendtime if rendtime else None
      recurrence.put(db)
      logging.info("applyrindex: " + str(applyrindex))
      logging.info("index: " + str(index))
      if str(applyrindex) == str(index):
        if now().strftime("%Y-%m-%d") >= recurrence.startdate:
          startdate = now()
        else:
          year, month, day = recurrence.startdate.split("-")
          startdate = datetime.datetime(int(year), int(month), int(day))
        adddays = calendar.monthrange(now().year, now().month)[1] - now().day + calendar.monthrange(now().year, now().month + 1)[1]
        enddate = now() + datetime.timedelta(days=adddays)
        recurrence.populate(db = db, start = startdate, end = enddate)
      
      index = index + 1
      
    return
    
  def dict(self, db):
    dict = {}
    dict['id'] = self.id
    dict['name'] = unicode(self.name, errors='ignore') 
    dict['description'] = unicode(self.description, errors='ignore') 
    dict['instructor'] = unicode(self.instructor, errors='ignore') 
    dict['cost'] = unicode(self.cost, errors='ignore')
    dict['highlight'] = self.highlight
    dict['archive'] = self.archive
    dict['alwaysshow'] = self.alwaysshow
    dict['instances'] = []
    dict['sessions'] = []
    dict['recurrences'] = []
    
    for session in self.sessions:
      dict['sessions'].append(session.dict(db=db))
    
    for instance in self.instances:
      dict['instances'].append(instance.dict(db=db))
    
    for recurrence in self.recurrences:
      dict['recurrences'].append(recurrence.dict(db=db))
    
    return dict
  
class EventSession():
  def __init__(self, id=None):
    self.id = id          # int(11)
    self.eventid = ""     # int(11)
    self.name = ""        # varchar(40)
    self.instructor = ""  # varchar(40)
    self.location = ""    # varchar(50)
    self.cost = ""        # varchar(10)
    self.notes = ""       # text
    self.archive = False  # tinyint(1)
    self.cancel = False   # tinyint(1)
  
  def find(self, db, id = None):
    c = db.cursor()
    if id:
      c.execute("SELECT COUNT(*) FROM eventsession WHERE id = %s", (id,))
      count = c.fetchall()[0][0]
      if count == 1:
        self.get(id = id, db = db)
        c.close()
        return

  def get(self, db, id):
    # This should only be called by fetchHousehold which does all of the error checking
    
    c = db.cursor()
    c.execute("SELECT id, eventid, name, instructor, location, cost, notes, archive, cancel FROM eventsession WHERE id = %s", (id,))

    self.fill(c.fetchall()[0])
    c.close()
    
  def fill(self, row):
    self.id = row[0]
    if row[1]:
      self.eventid = row[1]
    if row[2]:
      self.name = row[2]
    if row[3]:
      self.instructor = row[3]
    if row[4]:
      self.location = row[4]
    if row[5]:
      self.cost = row[5]
    if row[6]:
      self.notes = row[6]
    if row[7]:
      self.archive = row[7]
    if row[8]:
      self.cancel = row[8]
    
    return

  def put(self, db):
    c = db.cursor()
    
    with db:
      if self.id:
        c.execute("REPLACE INTO eventsession (id, eventid, name, instructor, location, cost, notes, archive, cancel) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (self.id, self.eventid, self.name, self.instructor, self.location, self.cost, self.notes, self.archive, self.cancel))
      else:
        c.execute("INSERT INTO eventsession (eventid, name, instructor, location, cost, notes, archive, cancel) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (self.eventid, self.name, self.instructor, self.location, self.cost, self.notes, self.archive, self.cancel))
        c.execute("select last_insert_id()")
        self.id  = c.fetchall()[0][0]
    
    c.close()
    return
  
  def dict(self, db):
    dict = {}
    dict['id'] = self.id
    dict['eventid'] = self.eventid
    dict['name'] = self.name
    dict['instructor'] = self.instructor
    dict['location'] = self.location
    dict['cost'] = self.cost
    dict['notes'] = self.notes
    dict['archive'] = self.archive
    dict['cancel'] = self.cancel
    
    return dict
  
class EventInstance():
  def __init__(self, id=None):
    self.id = id          # int(11)
    self.sessionid = id   # int(11)
    self.eventid = id     # int(11)
    self.name = ""        # varchar(50)
    self.date = None        # date
    self.starttime = ""   # time
    self.endtime = ""     # time
    self.instructor = ""  # varchar(40)
    self.cost = None        # varchar(10)
    self.notes = ""       # text
    self.deleted = False  # tinyint(1)
    self.cancel = False   # tinyint(1)
  
  def find(self, db, id = None):
    c = db.cursor()
    if id:
      c.execute("SELECT COUNT(*) FROM eventinstance WHERE id = %s", (id,))
      count = c.fetchall()[0][0]
      if count == 1:
        self.get(id = id, db = db)
        c.close()
        return

  def get(self, db, id):
    # This should only be called by fetchHousehold which does all of the error checking
    
    c = db.cursor()
    c.execute("SELECT id, sessionid, eventid, name, date, starttime, endtime, instructor, cost, notes, deleted, cancel FROM eventinstance WHERE id = %s", (id,))

    self.fill(c.fetchall()[0])
    c.close()
    
  def fill(self, row):
    self.id = row[0]
    if row[1]:
      self.sessionid = row[1]
    if row[2]:
      self.eventid = row[2]
    if row[3]:
      self.name = row[3]
    if row[4]:
      self.date = row[4]
    if row[5]:
      self.starttime = str(row[5])
      if len(self.starttime)==7:
        self.starttime = "0" + self.starttime
    if row[6]:
      self.endtime = str(row[6])
      if len(self.endtime)==7:
        self.endtime = "0" + self.endtime
    if row[7]:
      self.instructor = row[7]
    if row[8]:
      self.cost = row[8]
    if row[9]:
      self.notes = row[9]
    if row[10]:
      self.deleted = row[10]
    if row[11]:
      self.cancel = row[11]
    
    return

  def put(self, db):
    c = db.cursor()
    
    with db:
      if self.id:
        c.execute("REPLACE INTO eventinstance (id, sessionid, eventid, name, date, starttime, endtime, instructor, cost, notes, deleted, cancel) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (self.id, self.sessionid, self.eventid, self.name, self.date, self.starttime, self.endtime, self.instructor, self.cost, self.notes, self.deleted, self.cancel))
      else:
        logging.info("TRYING")
        c.execute("INSERT INTO eventinstance (sessionid, eventid, name, date, starttime, endtime, instructor, cost, notes, deleted, cancel) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (self.sessionid, self.eventid, self.name, self.date, self.starttime, self.endtime, self.instructor, self.cost, self.notes, self.deleted, self.cancel))
        c.execute("select last_insert_id()")
        self.id  = c.fetchall()[0][0]
    
    c.close()
    return
  
  def dict(self, db):
    dict = {}
    dict['id'] = self.id
    dict['sessionid'] = self.sessionid if self.sessionid else ""
    dict['eventid'] = self.eventid
    dict['name'] = self.name
    dict['date'] = self.date.isoformat() if self.date else ""
    dict['starttime'] = str(self.starttime)
    dict['endtime'] = str(self.endtime)
    dict['instructor'] = self.instructor
    dict['cost'] = self.cost
    dict['notes'] = self.notes
    dict['deleted'] = self.deleted
    dict['cancel'] = self.cancel
    
    return dict
  
class Visit():
  def __init__(self, id=None):
    self.id = id          # int(11)
    self.date = ""        # date
    self.householdid = "" # int(11)
    self.patronids = []     # int(11)
    self.eventids = []      # int(11)
    self.patronnames = {}
    self.eventnames = {}
    self.instanceids = {}
    self.picturewaiver = ""
  
  def find(self, db, id = None):
    c = db.cursor()
    if id:
      c.execute("SELECT COUNT(*) FROM visitdate WHERE id = %s", (id,))
      count = c.fetchall()[0][0]
      if count == 1:
        self.get(id = id, db = db)
        c.close()
        return

  def get(self, db, id):
    # This should only be called by fetchHousehold which does all of the error checking
    
    c = db.cursor()
    c.execute("SELECT id, date, householdid FROM visitdate WHERE id = %s", (id,))

    self.fill(row = c.fetchall()[0])
    self.fillPatronids(db)
    self.fillEventids(db)
    c.close()
    
  def fill(self, row):
    self.id = row[0]
    if row[1]:
      self.date = row[1]
    if row[2] or row[2] == 0:
      self.householdid = row[2]
    return

  def fillPatronids(self, db):
    c = db.cursor()
    c.execute("SELECT patronid FROM visitpatron WHERE visitid = %s", (self.id,))
    for row in c.fetchall():
      self.patronids.append(row[0])
    c.close()
    
  def fillPictureWaiver(self, db):
    if not self.householdid:
      return
    c = db.cursor()
    c.execute("SELECT picturewaiver FROM household WHERE id = %s", (self.householdid,))
    try:
      self.picturewaiver = c.fetchall()[0][0]
    except:
      self.picturewaiver = 0
    c.close()
    
  def fillEventids(self, db):
    c = db.cursor()
    c.execute("SELECT eventid FROM visitevent WHERE visitid = %s", (self.id,))
    for row in c.fetchall():
      self.eventids.append(row[0])
    c.close()
    
  def put(self, db):
    c = db.cursor()
    
    with db:
      c.execute("DELETE FROM visitpatron WHERE visitid = %s", (self.id,))
      c.execute("DELETE FROM visitevent WHERE visitid = %s", (self.id,))
      
      if self.id:
        c.execute("REPLACE INTO visitdate (id, date, householdid) VALUES (%s, %s, %s)", (self.id, self.date, self.householdid))
      else:
        c.execute("REPLACE INTO visitdate (date, householdid) VALUES (%s, %s)", (self.date, self.householdid))
        c.execute("select last_insert_id()")
        self.id  = c.fetchall()[0][0]
        
      for id in self.patronids:
        c.execute("REPLACE INTO visitpatron (visitid, patronid) VALUES (%s, %s)", (self.id, id))
    
      for pair in self.eventids:
        c.execute("REPLACE INTO visitevent (visitid, eventid, instanceid) VALUES (%s, %s, %s)", (self.id, pair[0], pair[1]))

    c.close()
    return
 
  def update(self, db, request, response):
    if request.get('deletevisit'):
      self.id = request.get('visitid')
      self.delete(db)
      return

    inputs = request.POST.items() 
        
    for input in inputs:
      if input[0] == "date":
        self.date = input[1]
      if input[0] == "visitid":
        self.id = input[1]
      if input[0] == "householdid":
        self.householdid = input[1]
      elif input[0][:6] == "patron" and input[0] != "patronsuggest":
        self.patronids.append(input[0][6:])
      elif input[0][:5] == "event" and input[0] != "eventsuggest":
        instanceid = request.get('instance' + input[0][5:]) if request.get('instance' + input[0][5:]) else 0 
        self.eventids.append([input[0][5:], instanceid])
        
    if not self.householdid:
      self.householdid = 0
    
    self.put(db)    
 
  def delete(self, db):
    c = db.cursor()
    with db:
      c.execute("DELETE FROM visitpatron WHERE visitid = %s", (str(self.id), ))
      c.execute("DELETE FROM visitevent WHERE visitid = %s", (str(self.id), ))
      c.execute("DELETE FROM visitdate WHERE id = %s", (str(self.id), ))
    c.close()
    return

  def dict(self):
    dict = {}
    dict['vid'] = int(self.id)
    dict['hid'] = int(self.householdid)
    dict['date'] = unicode(self.date.isoformat(), errors='ignore')
    dict['patronids'] = self.patronids
    dict['eventids'] = self.eventids
    dict['patronnames'] = self.patronnames
    dict['eventnames'] =  self.eventnames
    dict['instanceids'] = self.instanceids
    dict['picturewaiver'] = self.picturewaiver
    
    return dict
  
class VisitEvent():
  def __init__(self, id=None):
    self.eventid = id         
    self.instanceid = "" 
    self.name = "" 
    self.date = ""  
    self.sessionid = ""          
    self.highlight = False  
  
class Volunteer():
  def __init__(self, id=None):
    self.id = id          # int(11)
    self.date = ""        # date
    self.patronid = "" # int(11)
    self.patronname = ""
    self.volunteerjobid = ""
    self.volunteerjobname = ""
    self.starttime = ""
    self.endtime = ""
  
  def find(self, db, id = None):
    c = db.cursor()
    if id:
      c.execute("SELECT COUNT(*) FROM volunteer WHERE id = %s", (id,))
      count = c.fetchall()[0][0]
      if count == 1:
        self.get(id = id, db = db)
        c.close()
        return

  def get(self, db, id):
    # This should only be called by fetchHousehold which does all of the error checking
    
    c = db.cursor()
    c.execute("SELECT id, date, patronid FROM volunteer WHERE id = %s", (id,))

    self.fill(row = c.fetchall()[0])
    self.fillPatronids(db)
    self.fillEventids(db)
    c.close()
    
  def fill(self, row):
    self.id = row[0]
    if row[1]:
      self.date = row[1]
    if row[2] or row[2] == 0:
      self.householdid = row[2]
    return

  def fillPatronids(self, db):
    c = db.cursor()
    c.execute("SELECT patronid FROM visitpatron WHERE visitid = %s", (self.id,))
    for row in c.fetchall():
      self.patronids.append(row[0])
    c.close()
    
  def fillEventids(self, db):
    c = db.cursor()
    c.execute("SELECT eventid FROM visitevent WHERE visitid = %s", (self.id,))
    for row in c.fetchall():
      self.eventids.append(row[0])
    c.close()
    
  def put(self, db):
    c = db.cursor()
    
    with db:
      c.execute("DELETE FROM visitpatron WHERE visitid = %s", (self.id,))
      c.execute("DELETE FROM visitevent WHERE visitid = %s", (self.id,))
      
      if self.id:
        c.execute("REPLACE INTO visitdate (id, date, householdid) VALUES (%s, %s, %s)", (self.id, self.date, self.householdid))
      else:
        c.execute("REPLACE INTO visitdate (date, householdid) VALUES (%s, %s)", (self.date, self.householdid))
        c.execute("select last_insert_id()")
        self.id  = c.fetchall()[0][0]
        
      for id in self.patronids:
        c.execute("REPLACE INTO visitpatron (visitid, patronid) VALUES (%s, %s)", (self.id, id))
    
      for pair in self.eventids:
        c.execute("REPLACE INTO visitevent (visitid, eventid, instanceid) VALUES (%s, %s, %s)", (self.id, pair[0], pair[1]))

    c.close()
    return
 
  def update(self, db, request, response):
    if request.get('deletevisit'):
      self.id = request.get('visitid')
      self.delete(db)
      return

    inputs = request.POST.items() 
        
    for input in inputs:
      if input[0] == "date":
        self.date = input[1]
      if input[0] == "visitid":
        self.id = input[1]
      if input[0] == "householdid":
        self.householdid = input[1]
      elif input[0][:6] == "patron" and input[0] != "patronsuggest":
        self.patronids.append(input[0][6:])
      elif input[0][:5] == "event" and input[0] != "eventsuggest":
        instanceid = request.get('instance' + input[0][5:]) if request.get('instance' + input[0][5:]) else 0 
        self.eventids.append([input[0][5:], instanceid])
        
    if not self.householdid:
      self.householdid = 0
    
    self.put(db)    
 
  def delete(self, db):
    c = db.cursor()
    with db:
      c.execute("DELETE FROM visitpatron WHERE visitid = %s", (str(self.id), ))
      c.execute("DELETE FROM visitevent WHERE visitid = %s", (str(self.id), ))
      c.execute("DELETE FROM visitdate WHERE id = %s", (str(self.id), ))
    c.close()
    return

  def dict(self):
    dict = {}
    dict['vid'] = int(self.id)
    dict['hid'] = int(self.householdid)
    dict['date'] = unicode(self.date.isoformat(), errors='ignore')
    dict['patronids'] = self.patronids
    dict['eventids'] = self.eventids
    dict['patronnames'] = self.patronnames
    dict['eventnames'] =  self.eventnames
    dict['instanceids'] = self.instanceids
    
    return dict
  
class VolunteerJob():
  def __init__(self, id=None):
    self.id = id         
    self.name = "" 
    self.description = ""  
    self.hourlyrate = ""          
  
class InstanceSignIn():
  def __init__(self, id=None):
    self.instanceid = id          # int(11)
    self.eventid = None     # int(11)
    self.visitid = None
    self.name = ""        # varchar(50)
    self.date = ""        # date
    self.patrons = []
  
  def find(self, db, id = None):
    c = db.cursor()
    if id:
      c.execute("SELECT COUNT(*) FROM eventinstance WHERE id = %s", (id,))
      count = c.fetchall()[0][0]
      if count == 1:
        self.get(id = id, db = db)
        c.close()
        return

  def get(self, db, id):
    # This should only be called by fetchHousehold which does all of the error checking
    
    c = db.cursor()
    c.execute("SELECT eventinstance.id, eventinstance.sessionid, eventinstance.eventid, eventinstance.name, eventinstance.date, eventsession.name, event.name FROM event, eventsession, eventinstance WHERE event.id = eventinstance.eventid and (eventsession.id = eventinstance.sessionid or eventinstance.sessionid is NULL) and eventinstance.id = %s", (id,))

    self.fill(c.fetchall()[0], db)
    c.close()
        
  def fill(self, row, db):
    self.instanceid = row[0]
    if row[1]:
      self.sessionid = row[1]
    if row[2]:
      self.eventid = row[2]
    if row[4]:
      self.date = row[4]
    if row[6]:
      self.name = row[6]
    if row[3] or row[5]:
      self.name = self.name + " ("
      if row[5] and row[1] and self.sessionid != "NULL":
       self.name = self.name + row[5]
       if row[3]:
         self.name = self.name + ": "
      if row[3]:
        self.name = self.name + row[3]
      self.name = self.name + ")"
    
    self.getPatrons(db)
    return

  def getPatrons(self, db):
    c = db.cursor()
    
    if self.instanceid:
      c.execute("SELECT visitpatron.patronid, visitevent.visitid FROM visitdate, visitevent, visitpatron WHERE visitdate.id = visitevent.visitid AND visitevent.visitid = visitpatron.visitid AND visitdate.householdid = 0 AND visitevent.instanceid = %s", (self.instanceid,))

    for row in c.fetchall():
      patron = Patron()
      patron.get(db = db, id = row[0])
      if patron.id:
        self.patrons.append(patron)
      self.visitid = row[1]
    
    self.patrons = sorted(self.patrons, key=lambda patron: patron.last)
      
    c.close()
        
class EventRecurrence():
  def __init__(self, id=None):
    self.id = id            # int(11)
    self.sessionid = None   # int(11)
    self.eventid = None     # int(11)
    self.name = ""        # varchar(50)
    self.style = None       # varchar
    self.dayofweek = []     # int(11)
    self.weekofmonth = []   # tinyint(11)
    self.startdate = ""     # date
    self.enddate = ""       # date
    self.starttime = ""     # time
    self.endtime = ""       # time
  
  def find(self, db, id = None):
    c = db.cursor()
    if id:
      c.execute("SELECT COUNT(*) FROM eventrecurrence WHERE id = %s", (id,))
      count = c.fetchall()[0][0]
      if count == 1:
        self.get(id = id, db = db)
        c.close()
        return

  def get(self, db, id):
    # This should only be called by find which does all of the error checking
    
    c = db.cursor()
    c.execute("SELECT id, sessionid, eventid, name, style, dayofweek, weekofmonth, startdate, enddate, starttime, endtime FROM eventrecurrence WHERE id = %s", (id,))

    self.fill(c.fetchall()[0])
    c.close()
    
  def fill(self, row):
    self.id = row[0]
    if row[1]:
      self.sessionid = row[1]
    if row[2]:
      self.eventid = row[2]
    if row[3]:
      self.name = row[3]
    if row[4]:
      self.style = row[4]
    if row[5]:
      self.dayofweek = row[5].split(" ")
    if row[6]:
      self.weekofmonth = row[6].split(" ")
    if row[7]:
      self.startdate = row[7]
    if row[8]:
      self.enddate = row[8]
    if row[9]:
      self.starttime = str(row[9])
      if len(self.starttime)==7:
        self.starttime = "0" + self.starttime
    if row[10]:
      self.endtime = str(row[10])
      if len(self.endtime)==7:
        self.endtime = "0" + self.endtime
    
    return

  def put(self, db):
    c = db.cursor()
    dayofweek = ' '.join(self.dayofweek)
    weekofmonth = ' '.join(self.weekofmonth)
    
    with db:
      if self.id:
        c.execute("REPLACE INTO eventrecurrence (id, sessionid, eventid, name, style, dayofweek, weekofmonth, startdate, enddate, starttime, endtime) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (self.id, self.sessionid, self.eventid, self.name, self.style, dayofweek, weekofmonth, self.startdate, self.enddate, self.starttime, self.endtime))
      else:
        c.execute("INSERT INTO eventrecurrence (sessionid, eventid, name, style, dayofweek, weekofmonth, startdate, enddate, starttime, endtime) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (self.sessionid, self.eventid, self.name, self.style, dayofweek, weekofmonth, self.startdate, self.enddate, self.starttime, self.endtime))
        c.execute("select last_insert_id()")
        self.id  = c.fetchall()[0][0]
    
    c.close()
    return
  
  def populate(self, db = "", start = "", end = ""):
    # if the enddate has passed already then delete
    # default start is a month from now
    # default end is a month after start
    # if the end date is after the recurrence end date, then use the recurrence end date
    # if the end date is before the startdate then return
    if self.enddate and self.enddate < now().strftime("%Y-%m-%d"):
      self.delete()
      return
    if not start:
      adddays = calendar.monthrange(now().year, now().month)[1]
      start = datetime.datetime(int(now().year), int(now().month), int(now().day)) + datetime.timedelta(days=adddays)
    if not end:
      adddays = calendar.monthrange(start.year, start.month)[1]
      end = start + datetime.timedelta(days=adddays)
    if self.enddate and self.enddate < end.strftime("%Y-%m-%d"):
      year, month, day = self.enddate.split("-")
      end = datetime.datetime(int(year), int(month), int(day))
    if end < start:
      return
      
    logging.info("startdate = " + start.strftime("%Y-%m-%d"))
    logging.info("enddate = " + end.strftime("%Y-%m-%d"))
    
    day = start
    while day <= end:
      wom = (day.day - 1)//7 + 1
      if (str(day.isoweekday()) in self.dayofweek or (day.isoweekday() == 7 and "0" in self.dayofweek)) and (self.style == "weekly" or str(wom) in self.weekofmonth):
        logging.info(day)
        logging.info(wom)
        logging.info(day.weekday())
        instance = EventInstance()

        instance.eventid = self.eventid
        instance.sessionid = self.sessionid if self.sessionid else None
        instance.date = day
        instance.starttime = self.starttime if self.starttime else ""
        instance.endtime = self.endtime if self.endtime else ""
    
        instance.put(db = db)
      day += datetime.timedelta(days=1)
    

    return

  def dict(self, db):
    dict = {}
    dict['id'] = self.id
    dict['sessionid'] = self.sessionid if self.sessionid else ""
    dict['eventid'] = self.eventid
    dict['name'] = self.name
    dict['style'] = self.style
    dict['dayofweek'] = ' '.join(self.dayofweek)
    dict['weekofmonth'] = ' '.join(self.weekofmonth)
    dict['startdate'] = self.startdate.isoformat() if self.startdate else ""
    dict['enddate'] = self.enddate.isoformat() if self.enddate else ""
    dict['starttime'] = str(self.starttime)
    dict['endtime'] = str(self.endtime)
    
    return dict

  def delete(self, db):
    return
  
# /* ------------------ Bulk Gets --------------------- */

def getCategories(db, tablename):
  categories = []
  c = db.cursor()
  c.execute("SELECT id, " + tablename + ", display FROM " + tablename + " ORDER BY id")
  
  rows = c.fetchall()
  c.close()
  
  for row in rows:
    category = CategoryID()
    category.fill(row)
    categories.append(category)
  
  return categories

def getHouseholds(db, asdict = False, modifydate = False):
  c = db.cursor()
  if modifydate:
    c.execute("SELECT id, CAST(modified AS DATE), CAST(created AS DATE) FROM household WHERE CAST(modified AS DATE) = %s OR CAST(created AS DATE) = %s", (modifydate, modifydate))
  else:
    c.execute("SELECT id, CAST(modified AS DATE), CAST(created AS DATE) FROM household")
  householdrows = c.fetchall()
  
  c.execute("SELECT householdid, patronid FROM patronhash")
  patronhashrows = c.fetchall()

  
  patrons = getPatrons(db)
  
  householddict = {}
  for row in householdrows:
    id = row[0]
    householddict[id] = Household()
    householddict[id].id = id
    householddict[id].modified = row[1]
    householddict[id].created = row[2]
  
  patronhashdict = {}
  for row in patronhashrows:
    householdid = row[0]
    patronid = row[1]
    if householdid in householddict:
      if patronid in patronhashdict:
        patronhashdict[patronid].append(householdid)
      else:
        patronhashdict[patronid] = [householdid, ]
    
  for patron in patrons:
    if patron.id in patronhashdict:
      for householdid in patronhashdict[patron.id]:
        householddict[householdid].patrons.append(patron)
  
  return householddict
  
def getPatrons(db, asdict = False, inhouse = False):
    c = db.cursor()
    
    patrons = []
    if inhouse:
      c.execute("SELECT DISTINCT patron.id, patron.first, patron.last, patron.birthyear, patron.gender, patron.ethnicity FROM patron, patronhash WHERE patron.id = patronhash.patronid")
    else:
      c.execute("SELECT DISTINCT patron.id, patron.first, patron.last, patron.birthyear, patron.gender, patron.ethnicity FROM patron")
    rows = c.fetchall()
    c.close()

    for row in rows:
      patron = Patron()
      patron.fill(row)
      if asdict:
        patrons.append(patron.dict(db = db))
      else:
        patrons.append(patron)
    
    return patrons
    
def getEvents(db, asdict = False, date = None, duration = datetime.timedelta(days = 0)):
    c = db.cursor()
    
    events = []
    c.execute("SELECT id, name, description, instructor, cost, highlight, archive, alwaysshow FROM event")

    rows = c.fetchall()
    c.close()

    for row in rows:
      event = Event()
      event.fill(row)
      event.getInstances(db = db)
      event.getSessions(db = db)
      event.getRecurrences(db = db)
      if date:
        show = False
        tempinstances = []
        for instance in event.instances:
          if date <= instance.date <= date + duration:
            show = True
            tempinstances.append(instance)
        event.instances = tempinstances
      else:
        show = True
      if show and asdict:
        events.append(event.dict(db = db))

      elif show:
        events.append(event)
    
    return events
    
def getCommunications(db, resp = None):
    c = db.cursor()
    
    communications = []

    c.execute("SELECT id, name, description, display FROM communication")
    rows = c.fetchall()
    c.close()
    for row in rows:
      communication = Communication()
      communication.fill(row)
      communications.append(communication)
    
    return communications

def getPatronLookup(db):
    c = db.cursor()
    
    patronlookup = []
    c.execute("SELECT DISTINCT patron.first, patron.last, patronhash.householdid, patron.id FROM patron, patronhash WHERE patron.id = patronhash.patronid")

    rows = c.fetchall()
    c.close()

    for row in rows:
      entry = [row[0] + " " + row[1], int(row[2]), int(row[3])]
      patronlookup.append(entry)
    
    return patronlookup

def getEventArray(session, visitdate = now().date):
    c = session.db.cursor()
    
    eventarray = []
    c.execute("SELECT DISTINCT id, name FROM event")
    session.getAdminTable()
  
    rows = c.fetchall()

    for row in rows:
      if row[1] in session.staticevents:
        event = VisitEvent()
        event.id = int(row[0])
        event.name = row[1]
        event.highlight = True
        eventarray.append(event)

    for row in rows:
      if row[1] in session.staticevents:
        continue
      event = VisitEvent()
      event.id = int(row[0])
      event.name = row[1]
      c.execute("SELECT DISTINCT date, id, name FROM eventinstance WHERE eventid = %s", (event.id,))
      instances = c.fetchall() 
      for instance in instances:
        event.date = instance[0]
        if str(instance[0]) == visitdate.strftime("%Y-%m-%d"):
          event.highlight = True
          event.instanceid = instance[1]
          event.instancename = instance[2]

      eventarray.append(event)
      
    c.close()
    
    return eventarray

def getVisits(db, asdict = False, date = None):
  c = db.cursor()
  if date:
    c.execute("SELECT id, date, householdid FROM visitdate WHERE date = %s", (date,))
  else:
    c.execute("SELECT id, date, householdid FROM visitdate")
  visitdaterows = c.fetchall()
  
  c.execute("SELECT visitpatron.visitid, visitpatron.patronid, patron.first, patron.last FROM visitpatron, patron WHERE patron.id = visitpatron.patronid")
  visitpatronrows = c.fetchall()
  
  c.execute("SELECT visitevent.visitid, visitevent.eventid, visitevent.instanceid, event.name FROM visitevent, event WHERE event.id = visitevent.eventid")
  visiteventrows = c.fetchall()
  
  visitdict = {}
  for row in visitdaterows:
    id = int(row[0])
    visitdict[id] = Visit()
    visitdict[id].fill(row)
    visitdict[id].fillPictureWaiver(db)
  for row in visiteventrows:
    id = int(row[0])
    eventid = int(row[1])
    if id in visitdict:
      visitdict[id].eventids.append(eventid)
      visitdict[id].eventnames[eventid] = row[3]
      visitdict[id].instanceids[eventid] = []
  for row in visiteventrows:
    id = int(row[0])
    eventid = int(row[1]) 
    if row[2] and id in visitdict: 
      visitdict[id].instanceids[eventid].append(row[2])
  for row in visitpatronrows:
    id = int(row[0])
    patronid = int(row[1])
    if id in visitdict:
      visitdict[id].patronids.append(patronid)
      visitdict[id].patronnames[patronid] = unicode(row[2] + " " + row[3], errors='ignore')
  
  visitarray = []  
  for visit in visitdict:
    if asdict:
      visitarray.append(visitdict[visit].dict())
    else:
      visitarray.append(visitdict[visit])

  c.close()
  return visitarray    
    
# /* ------------------ Request Handlers --------------------- */

class LoginPage(webapp2.RequestHandler):
  def get(self):
    session = Session(users.get_current_user(), self.request)

    template_values = {'session': session}
  
    if session.user or session.admin:
      self.redirect('/')
      return
    else:
      template = JINJA_ENVIRONMENT.get_template('login.html')
      self.response.write(template.render(template_values))
      return

class MainPage(webapp2.RequestHandler):
  def get(self):
    session = Session(users.get_current_user(), self.request)
  
    template_values = {
      'session': session,
      'events': getEvents(db = session.db, asdict = False, date = now().date(), duration = datetime.timedelta(days = 7)),
    }
    
    if session.admin:
      admin_template_values = {
        'visits': getVisits(db = session.db, asdict = True, date = now().date()),
        'households': getHouseholds(db = session.db, asdict = False, modifydate = now().date()),        
      }
      template_values.update(admin_template_values)

    template = JINJA_ENVIRONMENT.get_template('index.html')
    self.response.write(template.render(template_values))

class NotAuthorized(webapp2.RequestHandler):
  def get(self):
    session = Session(users.get_current_user(), self.request)
  
    template_values = {'session': session}

    template = JINJA_ENVIRONMENT.get_template('notauthorized.html')
    self.response.write(template.render(template_values))

class Register(webapp2.RequestHandler):
  def get(self):
    session = Session(users.get_current_user(), self.request)

    if not session.user and not session.admin:
      self.redirect('/login')
      return
      
    household = Household()
    if session.admin and self.request.get('householdid'):
      household.find(db = session.db, id = self.request.get('householdid'))
    elif not session.admin:
      household.find(db = session.db, user = session.user)
      if not household.email:
        household.email = session.user.email()
       
    template_values = {
        'household': household,
        'session': session,
        'communications': getCommunications(db = session.db, resp = self.response),
        'incomes': getCategories(db = session.db, tablename = "income"),
        'ethnicities': getCategories(db = session.db, tablename = "ethnicity"),
        'genders': getCategories(db = session.db, tablename = "gender"),
        'currentyear': datetime.datetime.now().year,
        'yesnos': getCategories(db = session.db, tablename = "yesno"),
    }
    
    session.db.close()

    if self.request.path == '/adminhousehold' and session.admin:
      template = JINJA_ENVIRONMENT.get_template('adminregistrationform.html')
    elif self.request.path == '/visithousehold':
      template = JINJA_ENVIRONMENT.get_template('visitregistrationform.html')
    elif self.request.path == '/register':
      template = JINJA_ENVIRONMENT.get_template('registrationform.html')
    else:
      template = JINJA_ENVIRONMENT.get_template('notauthorized.html')
      
    self.response.write(template.render(template_values))

class SubmitRegister(webapp2.RequestHandler):
  def post(self):
    session = Session(users.get_current_user(), self.request)
    household = Household()
    patrons = []
    adminpatron = self.request.get('adminpatron')
    fromvisitlog = self.request.get('fromvisitlog')

    if session.admin:
      if adminpatron:
        household.update(db = session.db, request = self.request, response = self.response)
      else:
        household.update(db = session.db, request = self.request, response = self.response)        
    elif session.user:
      household.update(db = session.db, request = self.request, user = user, response = self.response)
    else:
      session.db.close()
      self.redirect('/login')
      return
      
    
    template_values = {
        'session': session,
        'household': household,
        'communications': getCommunications(db = session.db, resp = self.response),
        'incomes': getCategories(db = session.db, tablename = "income"),
        'ethnicities': getCategories(db = session.db, tablename = "ethnicity"),
        'genders': getCategories(db = session.db, tablename = "gender"),
        'yesnos': getCategories(db = session.db, tablename = "yesno"),
    }

    session.db.close()

    if adminpatron:
      self.redirect('/adminpatrons')
    if fromvisitlog:
      self.redirect('/visitlog?householdid=' + str(household.id))
    else:
      template = JINJA_ENVIRONMENT.get_template('registrationresponse.html')
      self.response.write(template.render(template_values))

class VisitLog(webapp2.RequestHandler):
  def get(self):
    self.handle()
    
  def post(self):
    self.handle()
  
  def handle(self):
    session = Session(users.get_current_user(), self.request)

    if not session.user and not session.admin:
      self.redirect('/login')
      return
    
    visit = Visit()
    visit.date = now().date()

    if self.request.get('volunteer'):
      volunteer = True
      action = "/volunteerlog"
      active_page = "volunteer"
    else:
      volunteer = False
      action = "/visitlog"
      active_page = "visit"
            
    household = Household()
    if session.admin and self.request.get('visitid'):
      visit = Visit()
      visit.get(db = session.db, id = self.request.get('visitid'))
      household.find(db = session.db, id = visit.householdid)
    elif session.admin and self.request.get('householdid'):
      household.find(db = session.db, id = self.request.get('householdid'))
    elif not session.admin:
      household.find(db = session.db, user = session.user)
      if not household.id:
        session.db.close()
        template = JINJA_ENVIRONMENT.get_template('pleaseregister.html')
        self.response.write(template.render({'session': session}))
        return
    else:
      patronlookup = getPatronLookup(session.db)
      session.db.close()
      template = JINJA_ENVIRONMENT.get_template('visitlogstart.html')
      self.response.write(template.render({'session': session, "patronlookup": patronlookup, 'now': now(), 'action': action, 'active_page': active_page}))
      return
    
    template_values = {
        'household': household,
        'session': session,
        'date': visit.date.strftime("%Y-%m-%d"), 
        'today': now().strftime("%Y-%m-%d"),
        'visit': visit
    }
    session.db.close()

    if self.request.path == '/adminvisit' and session.admin:
      template = JINJA_ENVIRONMENT.get_template('adminvisitlog.html')
    elif self.request.path == '/visitlog':
      template = JINJA_ENVIRONMENT.get_template('visitlog.html')
    else:
      template = JINJA_ENVIRONMENT.get_template('notauthorized.html')
    self.response.write(template.render(template_values))

class SubmitVisit(webapp2.RequestHandler):
  def post(self):
    session = Session(users.get_current_user(), self.request)
    visit = Visit()
    visit.update(db = session.db, request = self.request, response = self.response)
    session.db.close()
    if self.request.path == '/adminsubmitvisit' and session.admin:
      self.redirect("/adminvisits")
    elif self.request.path == '/submitvisit':
      self.redirect("/visitlog")
    else:
      self.redirect("/notauthorized")
    return

class VolunteerLog(webapp2.RequestHandler):
  def get(self):
    self.handle()
    
  def post(self):
    self.handle()
  
  def handle(self):
    session = Session(users.get_current_user(), self.request)

    if not session.user and not session.admin:
      self.redirect('/login')
      return
    
    visit = Visit()
    visit.date = now().date()

    if self.request.get('volunteer'):
      volunteer = True
      action = "/volunteerlog"
      active_page = "volunteer"
    else:
      volunteer = False
      action = "/visitlog"
      active_page = "visit"
            
    household = Household()
    if session.admin and self.request.get('visitid'):
      visit = Visit()
      visit.get(db = session.db, id = self.request.get('visitid'))
      household.find(db = session.db, id = visit.householdid)
    elif session.admin and self.request.get('householdid'):
      household.find(db = session.db, id = self.request.get('householdid'))
    elif not session.admin:
      household.find(db = session.db, user = session.user)
      if not household.id:
        session.db.close()
        template = JINJA_ENVIRONMENT.get_template('pleaseregister.html')
        self.response.write(template.render({'session': session}))
        return
    else:
      patronlookup = getPatronLookup(session.db)
      session.db.close()
      template = JINJA_ENVIRONMENT.get_template('visitlogstart.html')
      self.response.write(template.render({'session': session, "patronlookup": patronlookup, 'now': now(), 'action': action, 'active_page': active_page}))
      return
    
    template_values = {
        'household': household,
        'session': session,
        'date': visit.date.strftime("%Y-%m-%d"), 
        'today': now().strftime("%Y-%m-%d"),
        'visit': visit
    }
    session.db.close()

    if self.request.path == '/adminvisit' and session.admin:
      template = JINJA_ENVIRONMENT.get_template('adminvisitlog.html')
    elif self.request.path == '/visitlog':
      template = JINJA_ENVIRONMENT.get_template('visitlog.html')
    else:
      template = JINJA_ENVIRONMENT.get_template('notauthorized.html')
    self.response.write(template.render(template_values))

class AdminAddEvent(webapp2.RequestHandler):
  def get(self):
    session = Session(users.get_current_user(), self.request)

    if not session.admin:
      self.redirect('/notauthorized')
      return
      
    event = Event()
    nostandalone = True
    if self.request.get('eventid'):
      event.find(db = session.db, id = self.request.get('eventid'))
      for instance in event.instances:
        if not instance.sessionid:
          nostandalone = False
          break
       
    template_values = {
        'event': event,
        'session': session,
        'nostandalone': nostandalone,
    }
    
    session.db.close()

    template = JINJA_ENVIRONMENT.get_template('adminaddevent.html')
    
    self.response.write(template.render(template_values))
    
class AdminHome(webapp2.RequestHandler):
  def get(self):
    self.handle()
    
  def post(self):
    self.handle()
    
  def handle(self):
    session = Session(user = users.get_current_user(), request = self.request, getAdminTable = True)

    if not session.admin:
      self.redirect('/notauthorized')
      return
      
    template_values = {
        'session': session,
        'visits': getVisits(db = session.db, asdict = True, date = now().date()),
        'households': getHouseholds(db = session.db, asdict = False, modifydate = now().date()),
        'events': getEvents(db = session.db, asdict = False, date = now().date()),
    }

    template = JINJA_ENVIRONMENT.get_template('adminhome.html')

    self.response.write(template.render(template_values)) 
    session.db.close()
    return     

class Admin(webapp2.RequestHandler):
  def get(self, extra = ""):
    self.handle(extra)
    
  def post(self, extra = ""):
    self.handle(extra)
    
  def handle(self, extra):
    session = Session(user = users.get_current_user(), request = self.request, getAdminTable = True)
    
    template_values = {
        'session': session,
    }

    if not session.admin:
      self.redirect('/notauthorized')
      session.db.close()
      return
    elif extra == 'patrons':
      template = JINJA_ENVIRONMENT.get_template('adminpatrons.html')      
    elif extra == 'events':
      template_values['reload'] = self.request.get('reload')
      template = JINJA_ENVIRONMENT.get_template('adminevents.html')      
    elif extra == 'visits':
      template = JINJA_ENVIRONMENT.get_template('adminvisits.html')      
    elif extra == 'login':
      template = JINJA_ENVIRONMENT.get_template('adminlogin.html')
    elif extra == 'submitevent':
      event = Event()
      event.update(db = session.db, request = self.request, response = self.response)
      session.db.close()
      if self.request.get('reload'):
        self.redirect('/adminevents?reload=' + self.request.get('reload'))
      else:
        self.redirect('/adminevents')
      return
    elif extra == 'verifylogin':
      if self.request.get('password') and self.request.get('password') == session.adminpassword:
        self.redirect('/adminhome')
        session.db.close()
        return
      else:
        self.redirect('/adminlogin')
        session.db.close()
        return
    else:
       template = JINJA_ENVIRONMENT.get_template('adminnotthere.html')

    self.response.write(template.render(template_values)) 
    session.db.close()
    return     
                
class EventSignin(webapp2.RequestHandler):
  def get(self):
    self.handle()
    
  def post(self):
    self.handle()
    
  def handle(self):
    session = Session(user = users.get_current_user(), request = self.request, getAdminTable = True)
    
    if not session.admin:
      self.redirect('/notauthorized')
      session.db.close()
      return
    
    instancesignin = InstanceSignIn()
    instancesignin.find(db = session.db, id = self.request.get('iid'))

    template_values = {
        'session': session,
        'instancesignin': instancesignin,
        'patronlookup': getPatronLookup(session.db),
    }

    template = JINJA_ENVIRONMENT.get_template('eventsignin.html')
    self.response.write(template.render(template_values)) 
    session.db.close()
    return     
                
class SubmitEventSignin(webapp2.RequestHandler):
  def post(self):
    session = Session(users.get_current_user(), self.request)
    if session.admin:
      visit = Visit()
      visit.update(db = session.db, request = self.request, response = self.response)
      session.db.close()
    else:
      self.redirect('/notauthorized')
      session.db.close()
      return
          
    self.redirect('/adminhome')

class updateRecurrences(webapp2.RequestHandler):
  def get(self, extra = ""):
    self.handle(extra)
    
  def post(self, extra = ""):
    self.handle(extra)
    
  def handle(self, extra):
    session = Session(user = users.get_current_user(), request = self.request, getAdminTable = True)

    if not session.admin:
      self.redirect('/notauthorized')
      session.db.close()
      logging.info("NOT ADMIN!!!!")
      return

    db = session.db
    c = db.cursor()
    
    c.execute("SELECT id, sessionid, eventid, name, style, dayofweek, weekofmonth, startdate, enddate, starttime, endtime FROM eventrecurrence")

    rows = c.fetchall()
    c.close()

    for row in rows:
      recurrence = EventRecurrence()
      recurrence.fill(row)
      recurrence.populate(db = db)
      logging.info(recurrence.name)
        
# /* ------------------ JS Request Handlers --------------------- */

class PatronsJSON(webapp2.RequestHandler):
  def get(self):
    session = Session()
    patronsdict = getPatrons(db = session.db, asdict = True, inhouse = False)
    session.db.close()
    self.response.headers['Content-Type'] = 'application/json'
    str = unicode(str, errors='replace')
    self.response.out.write(unicode(json.dumps(patronsdict, indent = 2, encoding='utf8'), errors='replace'))
    
class EventsJSON(webapp2.RequestHandler):
  def get(self):
    session = Session()
    eventsdict = getEvents(db = session.db, asdict = True)
    session.db.close()
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(json.dumps(eventsdict, indent = 2))
    
class VisitsJSON(webapp2.RequestHandler):
  def get(self):
    session = Session()
    visitsdict = getVisits(db = session.db, asdict = True)
    session.db.close()
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(json.dumps(visitsdict, indent = 2))
    

# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/login', LoginPage),
    ('/notauthorized', NotAuthorized),
    ('/register', Register),
    ('/submitregister', SubmitRegister),
    ('/visitlog', VisitLog),
    ('/visithousehold', Register),
    ('/volunteerlog', VolunteerLog),
    ('/submitvisit', SubmitVisit),
    ('/adminsubmitvisit', SubmitVisit),
    ('/adminhousehold', Register),
    ('/adminaddevent', AdminAddEvent),
    ('/adminvisit', VisitLog),
    ('/adminhome', AdminHome),
    ('/admin(\w+)', Admin),
    ('/updaterecurrences', updateRecurrences),
    ('/eventsignin', EventSignin),
    ('/submiteventsignin', SubmitEventSignin),
    ('/getpatrons.json', PatronsJSON),
    ('/getevents.json', EventsJSON),
    ('/getvisits.json', VisitsJSON),
], debug=True)
# [END app]
