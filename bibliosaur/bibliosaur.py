#!/usr/bin/python

import sys

sys.path.append('/var/www/www.bibliosaur.com/scripts/')

import cgi
import datetime
import time
import urllib
import urllib2
import webapp2
import bottlenose
import jinja2
import os
import re
import xmlparser
import json
import logging
import logging.config
import Cookie
import sqlite3
import random
import keys
import pickle
import threading
import smtplib
from email.mime.text import MIMEText
from operator import itemgetter, attrgetter, methodcaller

# -------------- Definitions and Environment ---------------

toplevelurl = keys.toplevelurl
topleveldirectory = keys.topleveldirectory
db = keys.db
version = keys.version

jinja_environment = jinja2.Environment(loader = jinja2.FileSystemLoader(topleveldirectory))
logger = logging.getLogger()
hdlr = logging.FileHandler(topleveldirectory + '/bibliosaur.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.DEBUG)

DEBUG = True

UNREALISTICPRICE = int(7777777777777777)

GOOGLE_CLIENT_ID = keys.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = keys.GOOGLE_CLIENT_SECRET

AMAZON_ACCESS_KEY_ID = keys.AMAZON_ACCESS_KEY_ID
AMAZON_SECRET_KEY = keys.AMAZON_SECRET_KEY
AMAZON_ASSOC_TAG = keys.AMAZON_ASSOC_TAG

GOODREADS_ACCESS_KEY_ID = keys.GOODREADS_ACCESS_KEY_ID
GOODREADS_SECRET_KEY = keys.GOODREADS_SECRET_KEY

LINKSHARE_TOKEN = keys.LINKSHARE_TOKEN
LINKSHARE_ID = keys.LINKSHARE_ID
BN_TOKEN = keys.BN_TOKEN

GOOGLE_EMAIL = keys.GOOGLE_EMAIL
GOOGLE_PASSWORD = keys.GOOGLE_PASSWORD

possibleformats = ["hardcover", "paperback", "librarybinding", "kindle", "epub", "audiobook"]
predefinedlabels = ["mybooks", "archived"];
unwantedbindings = ["vhs tape", "audio cassette", "cassette", "unknown binding", "poche", "capa mole", "john jakes library of historical fiction", 
                    "brossura", "gebundene ausgabe", "taschenbuch", "large print", "signed", "inbunden", 
                    "20x13", "australian edition", "audio cd library binding", "unbound", "tapa blanda con solapas", "broschiert", 
                    "print", "boxed set", "pocket sf", "leather bound", "imitation leather", "misc. supplies", "pamphlet", "cards", 
                    "accessory", "loose leaf", "apparel", "poster", "digital"]
paperbackbindings = ["pocket ", "pocket", "softback", "paperback", "pocket", "perfect paperback", "mass market paperback", "mass market", "trade paperback", 
                     "paperback bunko", "spiral bound", "print on demand (paperback)", "spiral-bound"]
hardcoverbindings = ["hardcover", "trade hardcover", "hardback", "tankobon hardcover", "textbook binding", "board book"]
librarybindings = ["library binding", "turtleback", "library", "library edition", "school & library binding"]
ebookbindings = ["ebook", "nook book", "nook ebook", "adobe digital editions"]
kindlebindings = ["kindle", "kindle edition", "kindle edition with audio/video"]
audiobookbindings = ["audio", "preloaded digital audio player", "audiocd", "downloadable audiobook", 
                     "playaway", "cd", "digital audio", "playaway audiobook", "mp3 cd", "audible audio", "audio book", "audio cd", 
                     "audiobook", "mp3 book", "audible audio edition", "cd-rom", "dvd audio"]
                     
headers = {'User-agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'}

# -------------------- Authentication ----------------------------

class google_login(webapp2.RequestHandler):
    def get(self):
		token_request_uri = "https://accounts.google.com/o/oauth2/auth"
		response_type = "code"
		redirect_uri = toplevelurl + "/login/google/auth"
		scope = "https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email"
		url = "{token_request_uri}?response_type={response_type}&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}".format(
			token_request_uri = token_request_uri,
			response_type = response_type,
			client_id = GOOGLE_CLIENT_ID,
			redirect_uri = redirect_uri,
			scope = scope)
		return self.redirect(url)
    
class google_authenticate(webapp2.RequestHandler):
    def handle_exception(self, exception, debug):
		logging.warning("login failed: " + str(exception))
		return self.redirect(toplevelurl)
    def get(self):
		try:
		  code = self.request.get_all('code')
		except:
		  logging.error("Login failed:  'code' not available")
		  return self.redirect(toplevelurl)

		url = 'https://accounts.google.com/o/oauth2/token'
		redirect_uri = toplevelurl + "/login/google/auth"
		values = {'code' : code[0], 
			      'redirect_uri' : redirect_uri,
			      'client_id' : GOOGLE_CLIENT_ID,
			      'client_secret' : GOOGLE_CLIENT_SECRET,
			      'grant_type' : 'authorization_code'}
		data = urllib.urlencode(values)
		headers={'content-type':'application/x-www-form-urlencoded'}
		req = urllib2.Request(url, data, headers)
		response = urllib2.urlopen(req).read()
		token_data = json.JSONDecoder().decode(response)
		response = urllib2.urlopen("https://www.googleapis.com/oauth2/v1/userinfo?access_token={accessToken}".format(accessToken=token_data['access_token'])).read()
		#this gets the google profile!!
		google_profile = json.JSONDecoder().decode(response)
		#log the user in-->
		#HERE YOU LOG THE USER IN, OR ANYTHING ELSE YOU WANT
		#THEN REDIRECT TO PROTECTED PAGE
		session = Session()
		session.user.fetchUser(googleemail = google_profile['email'])
		cookie = session.login()
		
		self.response.set_cookie(key = cookie['key'], value = cookie['value'], expires = cookie['expires'])		
		return self.redirect(toplevelurl)

class logout(webapp2.RequestHandler):
    def get(self):		
		conn = sqlite3.connect(topleveldirectory + "/" + db)
		c = conn.cursor()

		session = LoadSession(self.request.cookies, connection = conn)
		
		with conn:
		  c.execute("INSERT or REPLACE INTO session (id, userid, expire) VALUES (?, ?, ?)", (session.id, session.user.id, datetime.datetime.now()))
		
		conn.close()
		
		self.response.set_cookie(key = 'sessionid', value = session.id, expires = datetime.datetime.now())
		return self.redirect(toplevelurl)

# -------------------------- Session and User Data -------------------------------

def LoadSession(cookies, connection = None):
  session = Session()
  sessionid = ""
  
  try: 
    sessionid = cookies.get('sessionid')
  except:
    pass  
  
  if sessionid:
    session.load(id=sessionid, connection = connection)

  return session
  
class Session():
  def __init__(self, id = None):
    self.id = id
    self.user = User()
  
  def load(self, id, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    c.execute("select count(*) from session where id = ?", (id,))
    count = c.fetchall()[0][0]
    
    if count == 0:
      pass
    elif count == 1:
      c.execute("select id, userid, expire from session where id = ?", (id,))
      result = c.fetchall()[0]
      if (result[2]) > str(datetime.datetime.now()):
        self.id = result[0]
        self.user.fetchUser(id = result[1])
    else:
      logging.error("USER ERROR:  More than one user with gmail: " + self.googleemail)
    
    if not connection:
      conn.close()
    return
  
  def login(self, connection = None):
    self.id = self.user.preferredemail.split('@')[0] + str(random.getrandbits(128))
    cookie = {}
    cookie['key'] = "sessionid"
    cookie['value'] = self.id
    cookie['expires'] = datetime.datetime.now() + datetime.timedelta(days=7) 
    
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
      
    with conn:
      c.execute("INSERT or REPLACE INTO session (id, userid, expire) VALUES (?, ?, ?)", (self.id, self.user.id, cookie['expires']))
    
    if not connection:
      conn.close()
    
    return cookie
  
  def logout(self):
    return
    
class User():
  def __init__(self, id=None):
    self.id = id
    self.preferredemail = None
    self.googleemail = None
    self.notificationwaittime = 7
    self.defaultformats = []
    self.defaultprice = 0
    self.preferredsort = None
    self.ascending = False
    self.labels =[]
  
  def fetchUser(self, id = None, googleemail = None, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()

    if googleemail:
      self.googleemail = str(googleemail)
      c.execute("select count(*) from users where googleemail = ?", (self.googleemail,))
      count = c.fetchall()[0][0]
      if count == 0:
        self.put(connection = conn)
      elif count == 1:
        self.get(googleemail = self.googleemail, connection = conn)
      else:
        logging.error("USER ERROR:  More than one user with gmail: " + self.googleemail)
    if id:
      self.id = id
      c.execute("select count(*) from users where id = ?", (self.id,))
      count = c.fetchall()[0][0]
      if count == 0:
        self.put(connection = conn)
      elif count == 1:
        self.get(id = self.id, connection = conn)
      else:
        logging.error("USER ERROR:  More than one user with id: " + self.id)

    if not connection:
      conn.close()
    
    return
  
  def get(self, id = None, googleemail = None, connection = None):
    er = False
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()

    if id:
      c.execute("select count(*) from users where id = ?", (id,))
      count = c.fetchall()[0][0]
      if count == 1:
        c.execute("select id, preferredemail, googleemail, notificationwaittime, defaultformats, defaultprice, preferredsort, ascending, labels  from users where id = ?", (id,))
      else:
        logging.error("USER ERROR:  user not found: " + id)
        er = True
    elif googleemail:
      c.execute("select count(*) from users where googleemail = ?", (googleemail,))
      count = c.fetchall()[0][0]
      if count == 1:
        c.execute("select id, preferredemail, googleemail, notificationwaittime, defaultformats, defaultprice, preferredsort, ascending, labels  from users where googleemail = ?", (googleemail,))
      else:
        self.googleemail = googleemail
        self.put()
        er = True

    if not er:
      user = c.fetchall()[0]
      self.id = user[0]
      if user[1]:
        self.preferredemail = user[1]
      if user[2]:
        self.googleemail = user[2]
      if user[3]:
        self.notificationwaittime = user[3]
      if user[4]:
        self.defaultformats = pickle.loads(str(user[4]))
      if user[5]:
        self.defaultprice = user[5]
      if user[6]:
        self.preferredsort = user[6]
      if user[7]:
        self.ascending = user[7]
      if user[8]:
        self.labels = pickle.loads(str(user[8]))
    if not connection:
      conn.close()
    
    return

  def put(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    
    c = conn.cursor()
    
    if not self.preferredemail:
      self.preferredemail = self.googleemail
    with conn:
      c.execute("REPLACE INTO users (id, preferredemail, googleemail, notificationwaittime, defaultformats, defaultprice, preferredsort, ascending, labels) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (self.id, self.preferredemail, self.googleemail, self.notificationwaittime, pickle.dumps(self.defaultformats), self.defaultprice, self.preferredsort, self.ascending, pickle.dumps(self.labels)))
    c.execute("select id from users where googleemail = ?", (self.googleemail,))
    result = c.fetchall()
    self.id = result[0][0]
    
    if not connection:
      conn.close()    
      
    return
  
  def update(self, request, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    self.preferredemail = request.get('preferredemail')
    price = request.get('defaultprice')
    try:
      self.defaultprice = int(float(price) * 100)
    except ValueError:
      self.defaultprice = None
    self.defaultformats = request.get_all('format')
    self.notificationwaittime = int(request.get('wait'))
    self.preferredsort = request.get('sortorder')
    if (request.get_all('ascdesc')[0] == "ascending"):
      self.ascending = True
    else:
      self.ascending = False

    labels = set()
    tabs = set()
    self.labels = []
    self.tabs = []
    for i in range(20):
      label = str(request.get('label' + str(i)))
      if (label):
        labels.add(label)
    for label in labels:
      self.labels.append(label)
    self.labels.sort() 
    
    if not self.preferredemail:
      self.preferredemail = self.googleemail
    with conn:
      c.execute("REPLACE INTO users (id, preferredemail, googleemail, notificationwaittime, defaultformats, defaultprice, preferredsort, ascending, labels) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (self.id, self.preferredemail, self.googleemail, self.notificationwaittime, pickle.dumps(self.defaultformats), self.defaultprice, self.preferredsort, self.ascending, pickle.dumps(self.labels)))

    if not connection:
      conn.close()    
      
    return
  
  def delete(self):
    return

# --------------------- Book Data ----------------------------

class Author():
  id = None
  goodreadsid = ""
  name = ""
  lastupdatedbooks = ""
  
  def get(self, goodreadsid = None, id = None, bookgoodreadsid = None, connection = None, addauthor = False):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    if goodreadsid:
      c.execute("select count(*) from authors where goodreadsid = ?", (goodreadsid,))
    elif id:
      c.execute("select count(*) from authors where id = ?", (id,))

    try:
      count = c.fetchall()[0][0]
    except:
      count = 0
    if count == 1:
      if goodreadsid:
        c.execute("select id, goodreadsid, name, lastupdatedbooks from authors where goodreadsid = ?", (goodreadsid,))
      elif id:
        c.execute("select id, goodreadsid, name, lastupdatedbooks from authors where id = ?", (id,))
      author = c.fetchall()[0]
      
      self.id = author[0]
      if author[1]:
        self.goodreadsid = str(author[1])
      if author[2]:
        self.name = author[2]
      if author[3]:
        self.lastupdatedbooks = author[3]

    if not(self.id and self.goodreadsid and self.name):
      if not addauthor:
        return False
      elif self.goodreadsid:
        self.fix(connection = connection)
      elif goodreadsid:
        self.goodreadsid = goodreadsid
        self.fix(connection = connection)
      elif bookgoodreadsid:
        self.findgoodreadsid(connection = connection, bookgoodreadsid = bookgoodreadsid)
        self.fix(connection = connection)
      else:
        return False
      
    if not connection:
      conn.close()
    
    return True

  def put(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()

    with conn:
      if self.id:
        c.execute("REPLACE INTO authors (id, goodreadsid, name, lastupdatedbooks) VALUES (?, ?, ?, ?)", (self.id, self.goodreadsid, self.name, self.lastupdatedbooks))
      else:
        c.execute("SELECT count(*) FROM authors WHERE goodreadsid = ?", (self.goodreadsid,))
        try:
          count = c.fetchall()[0][0]
        except:
          count = 0
        if count > 0:
          c.execute("SELECT id FROM authors WHERE goodreadsid = ?", (self.goodreadsid,))
          result = c.fetchall()
          self.id = result[0][0]
          c.execute("REPLACE INTO authors (id, goodreadsid, name, lastupdatedbooks) VALUES (?, ?, ?, ?)", (self.id, self.goodreadsid, self.name, self.lastupdatedbooks))
        else:
          c.execute("REPLACE INTO authors (goodreadsid, name, lastupdatedbooks) VALUES (?, ?, ?)", (self.goodreadsid, self.name, self.lastupdatedbooks))
          c.execute("SELECT id FROM authors WHERE goodreadsid = ?", (self.goodreadsid,))
          result = c.fetchall()
          self.id = result[0][0]
        print "Author ID = " + str(self.id)
    
    if not connection:
      conn.close()

  def fix(self, connection = None):
    print "fixing author"
    error = False
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
      
    url = "https://www.goodreads.com/author/show.xml?id=" + str(self.goodreadsid) + "&key=" + GOODREADS_ACCESS_KEY_ID

    try:
      u = urllib.urlopen(url)
      response = u.read()
      results = xmlparser.xml2obj(response)
      self.name = results.author.name
    except:
      print url
      self.name = "Author Missing:  Please contact lis@bibliosaur.com"
    
    self.put()
    if not connection:
      conn.close()

  def findgoodreadsid(self, connection = None, bookgoodreadsid = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
      
    editionurl = "http://www.goodreads.com/work/editions/" + str(bookgoodreadsid)
    content = urllib.urlopen(editionurl).read()
    
    try:
      goodreadsid = re.split('/author/show/', content)[1]
      goodreadsid = re.split('\.', goodreadsid)[0]
      print self.name + "has GRid " + goodreadsid
    except:
#       Do a better job of finding the author in case of error here
      goodreadsid = 0
      logging.error("FIX BOOK: " + str(self.goodreadsid))
        
    if not self.goodreadsid:
      self.goodreadsid = goodreadsid

    if not connection:
      conn.close()

  def delete(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    with conn:
      c.execute("DELETE FROM authors WHERE id = ?", (self.id,))
    
    if not connection:
      conn.close()
  
  def addtoqueue(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    with conn:
      c.execute("REPLACE INTO authorupdatequeue (authorid) VALUES (?)", (self.id,))
    
    if not connection:
      conn.close()
  
  def updateBooks(self, connection = None, force = False):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()

    currenttime = datetime.datetime.now()
    timeforupdate = datetime.timedelta(days=10) 
  
    # Possibly fix this to delete if author is not tracked
    c.execute("select count(*) from userauthors where authorid = ?", (self.id,))
    count = c.fetchall()[0][0]
    if count == 0:
      timeforupdate = datetime.timedelta(days=35) 
      
    if force or not (self.lastupdatedbooks) or not (str(self.lastupdatedbooks) > str(currenttime - timeforupdate)):
      print str(self.lastupdatedbooks)
      print str(currenttime - timeforupdate)
      self.insertBooks(connection = conn)
      self.lastupdatedbooks = str(currenttime)
      self.put()
    else:
      print "-- up to date"
    
    if not connection:
      conn.close()
  
  def insertBooks(self, connection = None, force = False):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()

    currenttime = datetime.datetime.now()

    url = "https://www.goodreads.com/author/list/" + str(self.goodreadsid) + "?format=xml&key=" + GOODREADS_ACCESS_KEY_ID
    u = urllib.urlopen(url)
    response = u.read()
    results = xmlparser.xml2obj(response)
    
    books = []
  
    try:    
      for item in results.author.books.book:
        goodreadsbookid = str(item.id.data)
        if goodreadsbookid:
          book = Book()
          book.getWorkFromBookID(connection = conn, goodreadsbookid=goodreadsbookid)
          if not book.get(goodreadsid = book.goodreadsid, connection = conn, addbook = False):
            book.title  = item.title
            book.author = self.name
            book.authorid = self.id
            book.small_img_url = item.small_image_url
            book.date = currenttime
            book.put(connection = conn)
            print "--" + book.title
          books.append(book)
    except AttributeError as er:
      pass
    
    
    if not connection:
      conn.close()
  
  def lastName(self):
    try: 
      return self.name.split()[-1]
    except:
      return self.name

  def dict(self):
    authordict = {}
    authordict['id'] = self.id
    authordict['goodreadsid'] = self.goodreadsid
    authordict['lastupdatedbooks'] = self.lastupdatedbooks
    authordict['name'] = self.name
    authordict['lastName'] = self.lastName()
    return authordict

class Book():
  id = None
  goodreadsid = ""
  goodreadseditionsid = ""
  title = ""
  author = ""
  authorid = ""
  small_img_url = ""
  date = datetime.datetime.now()
  lastupdatedprices = ""
  lastupdatededitions = ""
  editions = []
  prices = {} # {format:(price, url)}
  needsput = False 
  
  def get(self, goodreadsid = goodreadsid, id = id, connection = None, addbook = False):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    if goodreadsid:
      c.execute("SELECT count(*) FROM books WHERE goodreadsid = ?", (goodreadsid,))
    elif id:
      c.execute("SELECT count(*) FROM books WHERE id = ?", (id,))
    count = c.fetchall()[0][0]
    if count == 1:
      if goodreadsid:
        c.execute("SELECT id, goodreadsid, title, authorid, small_img_url, date, lastupdatedprices, lastupdatededitions, editions, prices, author from books where goodreadsid = ?", (goodreadsid,))
      elif id:
        c.execute("SELECT id, goodreadsid, title, authorid, small_img_url, date, lastupdatedprices, lastupdatededitions, editions, prices, author from books where id = ?", (id,))
      book = c.fetchall()[0]
      self.id = book[0]
      if book[1]:
        self.goodreadsid = str(book[1])
      if book[2]:
        self.title = book[2]
      if book[3]:
        self.authorid = book[3]
      if book[4]:
        self.small_img_url = book[4]
      if book[5]:
        self.date = book[5]
      if book[6]:
        self.lastupdatedprices = book[6]
      if book[7]:
        self.lastupdatededitions = book[7]
      if book[8]:
        self.editions = pickle.loads(str(book[8]))
      if book[9]:
        self.prices = pickle.loads(str(book[9]))
      if book[10]:
        self.author = book[10]
    elif not addbook:
      return False

    if addbook and not self.goodreadsid:
      self.goodreadsid = goodreadsid
      self.fix()
    elif addbook and not (self.authorid and self.title):
      self.fix()
    elif not self.authorid:
      self.fix()
      print "AUTHOR ID: " + str(self.authorid)
      
    if not connection:
      conn.close()
    
    return True

  def put(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()

    with conn:
      if self.id:
        c.execute("REPLACE INTO books (id, goodreadsid, title, author, authorid, small_img_url, date, lastupdatedprices, lastupdatededitions, editions, prices) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (self.id, self.goodreadsid, self.title, self.author, self.authorid, self.small_img_url, self.date, self.lastupdatedprices, self.lastupdatededitions, pickle.dumps(self.editions), pickle.dumps(self.prices)))
      else:
        c.execute("SELECT count(*) FROM books WHERE goodreadsid = ?", (self.goodreadsid,))
        try:
          count = c.fetchall()[0][0]
        except:
          count = 0
        if count > 0:
          c.execute("SELECT id FROM books WHERE goodreadsid = ?", (self.goodreadsid,))
          result = c.fetchall()
          self.id = result[0][0]
          c.execute("REPLACE INTO books (id, goodreadsid, title, author, authorid, small_img_url, date, lastupdatedprices, lastupdatededitions, editions, prices) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (self.id, self.goodreadsid, self.title, self.author, self.authorid, self.small_img_url, self.date, self.lastupdatedprices, self.lastupdatededitions, pickle.dumps(self.editions), pickle.dumps(self.prices)))
        else:
          c.execute("REPLACE INTO books (goodreadsid, title, author, authorid, small_img_url, date, lastupdatedprices, lastupdatededitions, editions, prices) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (self.goodreadsid, self.title, self.author, self.authorid, self.small_img_url, self.date, self.lastupdatedprices, self.lastupdatededitions, pickle.dumps(self.editions), pickle.dumps(self.prices)))
          c.execute("SELECT id FROM books WHERE goodreadsid = ?", (self.goodreadsid,))
          result = c.fetchall()
          self.id = result[0][0]
    
    if not connection:
      conn.close()

  def fix(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
      
    editionurl = "http://www.goodreads.com/work/editions/" + str(self.goodreadsid)
    content = urllib.urlopen(editionurl).read()
    
    try:
      pagetitle = re.split('<title>', content)[1]
      pagetitle = re.split('</title>', pagetitle)[0]
      pagetitle = re.split('Editions of ', pagetitle)[1]
      titleauthor = re.split('( by )', pagetitle)
      
      author = unicode(titleauthor.pop(), errors='ignore')
      titleauthor.pop()
      title = unicode("".join(titleauthor), errors='ignore')
    except:
      title = "Title Missing:  Please contact lis@bibliosaur.com"        
      author = "Author Missing:  Please contact lis@bibliosaur.com"
      logging.error("FIX BOOK: " + str(self.goodreadsid))
    
    try:
      goodreadsauthorid = re.split('/author/show/', content)[1]
      goodreadsauthorid = re.split('\.', goodreadsauthorid)[0]
    except:
#       Do a better job of finding the author in case of error here
      goodreadsauthorid = 0
      logging.error("FIX BOOK: " + str(self.goodreadsid))
    
    try:
      image = re.split('leftAlignedImage', content)[1]
      image = re.split('src=', image)[1]
      image = re.split('\"', image)[1]
      small_img_url = image
    except:
      small_img_url = "http://www.goodreads.com/assets/nocover/60x80.png"
    
    if not self.author:
      self.author = author
    if not self.authorid:
      author = Author()
      author.get(goodreadsid = goodreadsauthorid, connection = conn, addauthor = True)
      self.authorid = author.id
    if not self.title:
      self.title = title
    if not self.small_img_url:
      self.small_img_url = small_img_url
    
    self.put()

    if not connection:
      conn.close()

  def delete(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    with conn:
      c.execute("DELETE FROM books WHERE id = ?", (self.id,))
    
    if not connection:
      conn.close()
  
  def addtoqueue(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    with conn:
      c.execute("REPLACE INTO bookupdatequeue (bookid) VALUES (?)", (self.id,))
    
    if not connection:
      conn.close()
  
  def updatePrices(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    self.prices = {}
    self.put(connection = conn)
        
    if DEBUG:
      print " Updating Price"
    for isbn in self.editions:
      edition = Edition()
      if not edition.get(isbn = str(isbn), connection = conn):
        self.editions.remove(isbn)
        continue
      if DEBUG:
        print "  " + edition.isbn
      try:
        edition.updatePrice(connection = conn)
      except Exception as inst:
        if DEBUG:
          print type(inst)     # the exception instance
          print inst.args      # arguments stored in .args
          print inst           # __str__ allows args to printed directly
        
      if edition.format not in self.prices:
        self.prices[edition.format] = (UNREALISTICPRICE, "")
         
      if int(edition.lowestprice) < int(self.prices[edition.format][0]):
        self.prices[edition.format] = (edition.lowestprice, edition.lowestpriceurl)
        # this gets put() in the calling function
    
    self.put(connection = conn)
    
    if not connection:
      conn.close()
  
  def updateEditions(self, connection = None, force = False):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()

    currenttime = datetime.datetime.now()
    timeforeditionupdate = datetime.timedelta(days=2) 
    timeforpriceupdate = datetime.timedelta(hours=8)
  
    c.execute("select count(*) from userbooks where bookid = ?", (self.id,))
    count = c.fetchall()[0][0]
    if count == 0:
      c.execute("select count(*) from userauthors where authorid = ?", (self.authorid,))
      if count == 0:
        self.delete()
        return
#     Fix this to give lower priority if the author is tracked and but book is ignored
      timeforeditionupdate = datetime.timedelta(days=30) 
      timeforpriceupdate = datetime.timedelta(days=5)
      
    if force or not (self.lastupdatededitions) or not (str(self.lastupdatededitions) > str(currenttime - timeforeditionupdate)):
      self.insertEditions(connection = conn)
      self.lastupdatededitions = currenttime
      self.lastupdatedprices = currenttime - 2*timeforpriceupdate # we need to make sure we update prices since we updated the editions
      # this gets put() in the next if statement

    if force or not (self.lastupdatedprices) or not (str(self.lastupdatedprices) > str(currenttime - timeforpriceupdate)):
      self.updatePrices(connection = conn)
      self.lastupdatedprices = currenttime
      self.put()
    
    if not connection:
      conn.close()
  
  def insertEditions(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()

    self.editions = []
    if DEBUG:
      print " inserting editions"
    self.insertGoodreadsEditions(connection = conn)
    if DEBUG:
      print "  inserting Goodreads editions"
      print "    count: " + str(len(self.editions))
    self.insertAmazonEditions(connection = conn)
    if DEBUG:
      print "  inserting Amazon editions"
      print "    count: " + str(len(self.editions))
    self.editions = list(set(self.editions))
    if DEBUG:
      print "  final count: " + str(len(self.editions))
    self.put(connection = conn)
  
    if not connection:
      conn.close()

  def insertGoodreadsEditions(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()

    editionurl = "http://www.goodreads.com/work/editions/" + self.goodreadsid
    content = urllib.urlopen(editionurl).read()
    splitcontent = content.split('\n')
  
    isbnlast = True
  
    for line in splitcontent:
      format = re.findall('\s+([\w\s]+), \d+ pages', line)
      isbn = re.findall('^\s*(\d\d\d\d\d\d\d\d\d\d)\s*$', line)
      asin = re.findall('^\s*([\d\w][\d\w][\d\w][\d\w][\d\w][\d\w][\d\w][\d\w][\d\w][\d\w])\s*$', line)
      kindle = re.findall('(Kindle Edition)', line)
    
      try:
        format[0] = str(format[0]).lower()
        if format[0] in paperbackbindings:
          lastformat = "paperback"
        elif format[0] in kindlebindings:
          lastformat = "kindle"
        elif format[0] in ebookbindings:
          lastformat = "epub"
        elif format[0] in librarybindings:
          lastformat = "librarybinding"
        elif format[0] in hardcoverbindings:
          lastformat = "hardcover"
        elif format[0] in audiobookbindings:
          lastformat = "audiobook"
        elif format[0] not in unwantedbindings:
          logging.info("UNHANDLED FORMAT: " + str(format[0]))
          continue
        else:
          continue
        isbnlast = False
      except IndexError:
        pass
       
      try:
        if (kindle[0] == "Kindle Edition"):
          lastformat = "kindle"
          isbnlast = False
      except IndexError:
        pass
        
      try:
        isbn = str(isbn[0])
        if not isbnlast:
          edition = Edition()
          edition.isbn = isbn
          edition.format = lastformat
          edition.bookid = self.id
          edition.put(connection = conn)
          self.editions.append(edition.isbn)
          isbnlast = True
      except IndexError:
        pass
    
      try:
        isbn = str(asin[0])
        if not isbnlast:
          edition = Edition()
          edition.isbn = isbn
          edition.format = lastformat
          edition.bookid = self.id
          edition.put(connection = conn)
          self.editions.append(isbn)
          isbnlast = True
      except IndexError:
        pass
    
    self.put(connection = conn)
    
    if not connection:
      conn.close()
  
  def insertAmazonEditions(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()

    gotit = False
    for isbn in self.editions:
      for attempt in range(3):
        try:
          associateinfo = bottlenose.Amazon(AMAZON_ACCESS_KEY_ID, AMAZON_SECRET_KEY, AMAZON_ASSOC_TAG)
          response = associateinfo.ItemLookup(ItemId=isbn, ResponseGroup="AlternateVersions", MerchantId = "Amazon")
          bookinfo = xmlparser.xml2obj(response)
        
          for item in bookinfo.Items.Item.AlternateVersions.AlternateVersion:
            format = str(item.Binding).lower()
            if format in paperbackbindings:
              format = "paperback"
            elif format in kindlebindings:
              format = "kindle"
            elif format in ebookbindings:
              format = "epub"
            elif format in librarybindings:
              format = "librarybinding"
            elif format in hardcoverbindings:
              format = "hardcover"
            elif format in audiobookbindings:
              format = "audiobook"
            elif format not in unwantedbindings:
              logging.info("UNHANDLED FORMAT: " + format)
              format = ""
              continue
            else:
              continue
          
            edition = Edition()
            edition.isbn = str(item.ASIN)
            edition.format = format
            edition.bookid = self.id
            edition.put(connection = conn)
            self.editions.append(edition.isbn)
          
          gotit = True
          break
        except urllib2.HTTPError:
          if DEBUG:
            print "sleeping"
          time.sleep(5 * (attempt+1))
        except (AttributeError, TypeError):
          break
        except Exception as inst:
          logging.error("INSERT AMAZON EDITIONS ERROR: isbn = " + str(isbn))
          logging.error(type(inst))     # the exception instance
          logging.error(inst.args)      # arguments stored in .args
          logging.error(inst)           # __str__ allows args to printed directly
          break
      
      if gotit:
        break
  
    if not connection:
      conn.close()
  
  def getWorkFromBookID(self, connection = None, goodreadsbookid = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
      
    bookurl = "https://www.goodreads.com/book/show/" + str(goodreadsbookid)
    content = urllib.urlopen(bookurl).read()

    try:
      workid = re.split('https://www.goodreads.com/work/editions/', content)[1]
      workid = re.split('-', workid)[0]
      self.goodreadsid = workid
    except:
      logging.error("FIX BOOKID: " + str(goodreadsbookid))
      
  def dict(self):
    bookdict = {}
    bookdict['id'] = self.id
    bookdict['goodreadsid'] = self.goodreadsid
    bookdict['title'] = self.title
    bookdict['authorid'] = self.authorid
    bookdict['small_img_url'] = self.small_img_url
    bookdict['date'] = self.date
    return bookdict

class Edition():
  isbn = "" # or ASIN, et al
  format = ""
  lowestprice = UNREALISTICPRICE
  lowestpriceurl = ""
  bookid = None

  def put(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    self.isbn = str(self.isbn)
    while len(self.isbn) < 10:
      self.isbn = "0" + self.isbn

    with conn:
      c.execute("REPLACE INTO editions (isbn, lowestprice, lowestpriceurl, format, bookid) VALUES (?, ?, ?, ?, ?)", (self.isbn, self.lowestprice, self.lowestpriceurl, self.format, self.bookid))
    
    if not connection:
      conn.close()

  def get(self, isbn = None, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()

    isbn = str(isbn)
    while len(isbn) < 10:
      isbn = "0" + isbn

    c.execute("select count(*) from editions where isbn = ?", (isbn,))
    count = c.fetchall()[0][0]
    if count == 1:
      c.execute("select isbn, lowestprice, lowestpriceurl, format, bookid from editions where isbn = ?", (isbn,))
      edition = c.fetchall()[0]
      self.isbn = isbn
      if edition[1]:
        self.lowestprice = edition[1]
      if edition[2]:
        self.lowestpriceurl = edition[2]
      if edition[3]:
        self.format = edition[3]
      if edition[4]:
        self.bookid = edition[4]
    elif count == 0:
      return False
    
    if not connection:
      conn.close()
      
    return True

  def updatePrice(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    currentlowestprice = UNREALISTICPRICE
    currenturl = ""
    prices = {}
    
    if DEBUG:
      print "   " + self.format
      
    for attempt in range(3):
      try:
        if (self.format == "kindle"):
          prices['kindle'] = GetKindlePrice(self.isbn)
        elif self.format in ["hardcover", "paperback", "librarybinding"]:
          prices['amazon'] = GetAmazonPrice(self.isbn)
#           prices['bn'] = GetBNPrice(edition.isbn)
        elif (self.format == "epub"):
          prices['bn'] = GetBNPrice(self.isbn)
          prices['google'] = GetGooglePrice(self.isbn)
        elif (self.format == "audiobook"):
          prices['amazon'] = GetAmazonPrice(self.isbn)
          prices['bn'] = GetBNPrice(self.isbn)
        else:
          return
        break
      except urllib2.HTTPError:
        if DEBUG:
          print "--sleeping"
        time.sleep(2 * (attempt+1))
      except (AttributeError, TypeError, IndexError):
        return
      except Exception as inst:
        logging.error("UPDATE PRICE ERROR: isbn = " + str(self.isbn))
#         logging.error(type(inst))     # the exception instance
#         logging.error(inst.args)      # arguments stored in .args
#         logging.error(inst)           # __str__ allows args to printed directly
        return
    
    for key in prices.keys():
      if (int(prices[key][0]) < int(currentlowestprice)):
        currentlowestprice = int(prices[key][0])
        currenturl = prices[key][1]
  
    self.lowestprice = currentlowestprice  
    self.lowestpriceurl = currenturl
    self.put()
    
    if DEBUG:
      print "     " + str(self.lowestprice)
      
    if not connection:
      conn.close()

  def delete(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    print self.isbn + " " + str(self.bookid)
    book = Book()
    book.get(id = self.bookid, connection = conn)
    try:
      book.editions.remove(str(self.isbn))
      book.put(connection = conn)
    except:
      pass
    
    with conn:
      c.execute("DELETE FROM editions WHERE isbn = ?", (self.isbn,))
        
    if not connection:
      conn.close()

class UserAuthor():
  userid = None
  authorid = None
  archived = False
  ignore = []

  def get(self, authorid, userid, connection = None, addauthor = False):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()

    c.execute("SELECT count(*) FROM userauthors where authorid = ? and userid = ?", (authorid, userid)) 
    count = c.fetchall()[0][0]
    if count == 1:
      c.execute("SELECT userid, authorid, archived, ignore FROM userauthors where authorid = ? and userid = ?", (authorid, userid)) 
      userauthor = c.fetchall()[0]

      if userauthor[0]:
        self.userid = userauthor[0]
      if userauthor[1]:
        self.authorid = userauthor[1]
      if userauthor[2]:
        self.archived = userauthor[2]
      if userauthor[3]:
        self.ignore = pickle.loads(str(userauthor[3]))
    elif addauthor:
      self.userid = userid
      self.authorid = authorid
      self.put()
    else:
      return False
    
    if not connection:
      conn.close()
      
    return True

  def put(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()

    with conn:
      c.execute("REPLACE INTO userauthors (userid, authorid, archived, ignore) VALUES (?, ?, ?, ?)", (self.userid, self.authorid, self.archived, pickle.dumps(self.ignore)))
    
    if not connection:
      conn.close()

  def delete(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    with conn:
      c.execute("DELETE FROM userauthors WHERE authorid = ? and userid = ?", (self.authorid, self.userid))
    
    if not connection:
      conn.close()

class UserBook():
  userid = None
  bookid = None
  acceptedformats = []
  price = 0
  date = datetime.datetime.now()
  archived = False
  notified = datetime.datetime.now()
  labels = []

  def get(self, bookid, userid, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()

    c.execute("SELECT userid, bookid, acceptedformats, price, date, archived, notified, labels FROM userbooks where bookid = ? and userid = ?", (bookid, userid)) 
    userbook = c.fetchall()[0]
  
    if userbook[0]:
      self.userid = userbook[0]
    if userbook[1]:
      self.bookid = userbook[1]
    if userbook[2]:
      self.acceptedformats = pickle.loads(str(userbook[2]))
    if userbook[3]:
      self.price = userbook[3]
    if userbook[4]:
      self.date = userbook[4]
    if userbook[5]:
      self.archived = userbook[5]
    if userbook[6]:
      self.notified = userbook[6]
    if userbook[7]:
      self.labels = pickle.loads(str(userbook[7]))
    
    if not connection:
      conn.close()

  def put(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()

    with conn:
      c.execute("REPLACE INTO userbooks (userid, bookid, acceptedformats, price, date, archived, notified, labels) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (self.userid, self.bookid, pickle.dumps(self.acceptedformats), self.price, self.date, self.archived, self.notified, pickle.dumps(self.labels)))
    
    if not connection:
      conn.close()

  def delete(self, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    with conn:
      c.execute("DELETE FROM userbooks WHERE bookid = ? and userid = ?", (self.bookid, self.userid))
    
    if not connection:
      conn.close()

class Coupon():
  offer = str
  merchant = str
  url = str

class DisplayBook():
  goodreadsid = ""
  bookid = ""
  title = ""
  author = ""
  small_img_url = ""
  price = ""
  acceptedformats = possibleformats
  formatprices = {}
  formaturls = {}
  priceavailable = False
  free = False
  labels = []
  dateadded = str
  
  def xml(self):
    xmlstring = "<DisplayBook>"
    xmlstring = xmlstring + "<goodreadsid>" + self.goodreadsid + "</goodreadsid>"
    xmlstring = xmlstring + "<bookid>" + self.bookid + "</bookid>"
    xmlstring = xmlstring + "<title>" + self.title.replace('<', '&lt;').replace('>', '&gt;') + "</title>"
    xmlstring = xmlstring + "<author>" + self.author.replace('<', '&lt;').replace('>', '&gt;') + "</author>"
    xmlstring = xmlstring + "<price>" + self.price + "</price>"
    xmlstring = xmlstring + "<small_img_url>" + self.small_img_url + "</small_img_url>"
    xmlstring = xmlstring + "<dateadded>" + self.dateadded + "</dateadded>"
    xmlstring = xmlstring + "<priceavailable>" + str(self.priceavailable) + "</priceavailable>"
    xmlstring = xmlstring + "<free>" + str(self.free) + "</free>"
    xmlstring = xmlstring + "<formatprices>"
    for format in self.formatprices:
      xmlstring = xmlstring + "<" + format + ">" + self.formatprices[format] + "</" + format + ">"
    xmlstring = xmlstring + "</formatprices>"
    xmlstring = xmlstring + "<formaturls>"
    for format in self.formaturls:
      xmlstring = xmlstring + "<" + format + ">" + self.formaturls[format] + "</" + format + ">"
    xmlstring = xmlstring + "</formaturls>"
    for label in self.labels:
      xmlstring = xmlstring + "<label>" + label.encode('utf-8').replace('<', '&lt;').replace('>', '&gt;') + "</label>"
    xmlstring = xmlstring + "</DisplayBook>"
    return xmlstring.encode('utf-8')

  def get(self, bookid, user = None, connection = None):
    if connection:
      conn = connection
    else:
      conn = sqlite3.connect(topleveldirectory + "/" + db)
    book = Book()
    book.get(id = bookid, connection = conn)
    userbook = UserBook()
    if user:
      userbook.get(bookid = bookid, userid = user.id, connection = conn)
      self.acceptedformats = userbook.acceptedformats
      self.price = FormatPrice(userbook.price)
      self.dateadded = str(userbook.date)
      self.labels = list(set(userbook.labels) & set(user.labels))
      if userbook.archived:
        self.labels.append('archived')
    else:
      self.dateadded = book.date
    
    self.goodreadsid = book.goodreadsid
    self.bookid = str(book.id)
    self.formatprices = dict.fromkeys(self.acceptedformats)
    self.formaturls = dict.fromkeys(self.acceptedformats)
  
    self.author = book.author
    self.title  = book.title
    self.small_img_url = book.small_img_url

    for format in self.acceptedformats:
      if format in book.prices:
        priceandurl = book.prices[format]
      else:
        priceandurl = (UNREALISTICPRICE, "")
      if user and (priceandurl[0] <= userbook.price):
        self.priceavailable = True
        if (priceandurl[0] <= 0):
          self.free = True
      self.formatprices[format] = FormatPrice(priceandurl[0])
      self.formaturls[format] = priceandurl[1]
    
    if not connection:
      conn.close()

  def dict(self):
    bookdict = {}
    bookdict['bookid'] = self.bookid
    bookdict['goodreadsid'] = self.goodreadsid
    bookdict['title'] = self.title
    bookdict['author'] = self.author
    bookdict['small_img_url'] = self.small_img_url
    bookdict['price'] = self.price
    bookdict['acceptedformats'] = self.acceptedformats
    bookdict['formatprices'] = self.formatprices
    bookdict['formaturls'] = self.formaturls
    bookdict['priceavailable'] = self.priceavailable
    bookdict['free'] = self.free
    bookdict['labels'] = self.labels
    bookdict['dateadded'] = self.dateadded
    return bookdict

class LowPriceBooks():
  email = str
  title = str
  author = str
  format = str
  price = str
  url = str
    
class KindleDeal():
  title = ""
  small_img_url = ""
  price = ""
  description = ""
  url = ""
  
  def addIsbn(isbn, connection = None):
    return
  
  def addLink(link, connection = None):
    return

# ----------------------Price Getting and Comparing ----------------

def FormatPrice(price):
  if (price == UNREALISTICPRICE):
    return ""
  try:
    return "$%d.%2.2d" % (price/100, price%100)
  except TypeError:
    return 
  
def GetAmazonPrice(isbn):
# return list with first element as price and second as url
  associateinfo = bottlenose.Amazon(AMAZON_ACCESS_KEY_ID, AMAZON_SECRET_KEY, AMAZON_ASSOC_TAG)
  response = associateinfo.ItemLookup(ItemId=isbn, Availability="Available", ResponseGroup="Offers", MerchantId = "Amazon")
  bookinfo = xmlparser.xml2obj(response)
  
  price = UNREALISTICPRICE
  url = "amazon"

  try:
    price = bookinfo.Items.Item.Offers.Offer.OfferListing.Price.Amount
    response = associateinfo.ItemLookup(ItemId=str(isbn), ResponseGroup="ItemAttributes", MerchantId = "Amazon")
    bookinfo = xmlparser.xml2obj(response)
    url = bookinfo.Items.Item.DetailPageURL
  except:
    price = bookinfo.Items.Item[0].Offers.Offer.OfferListing.Price.Amount
    response = associateinfo.ItemLookup(ItemId=str(isbn), ResponseGroup="ItemAttributes", MerchantId = "Amazon")
    bookinfo = xmlparser.xml2obj(response)
    url = bookinfo.Items.Item.DetailPageURL
  
  return [int(price), url]

def GetBNPrice(isbn):
# return list with first element as price and second as url
  bookurl = "http://services.barnesandnoble.com/v03_00/ProductLookup?Ean=" + isbn + "&ProductCode=Book&AppId=" + BN_TOKEN
  price = UNREALISTICPRICE
  url = "bn"
  
  response = urllib.urlopen(bookurl).read()
  bookinfo = xmlparser.xml2obj(response)
  price = bookinfo.ProductLookupResult.Product[0].Prices.BnPrice
  encodedurl = bookinfo.ProductLookupResult.Product[0].Url.replace("/", "%2f").replace(":", "%3a")
  url = "http://click.linksynergy.com/deeplink?mid=36889&id=" + LINKSHARE_ID + "&murl=" + encodedurl
  price = int(float(price) * 100)
  deliverymessage = bookinfo.ProductLookupResult.Product[0].ShippingOptions.DeliveryMessage

  return [int(price), url]
      
def GetKindlePrice(isbn):
# return list with first element as price and second as url
  associateinfo = bottlenose.Amazon(AMAZON_ACCESS_KEY_ID, AMAZON_SECRET_KEY, AMAZON_ASSOC_TAG)
  response = associateinfo.ItemLookup(ItemId=isbn, ResponseGroup="ItemAttributes", SearchIndex="Books", IdType="ISBN")
  bookinfo = xmlparser.xml2obj(response)
  
  price = UNREALISTICPRICE 
  url = "kindle"

  url = "https://www.amazon.com/dp/" + isbn
  req = urllib2.Request(url, None, headers)
  content = urllib2.urlopen(req).read()
  prices = re.findall('<input type="hidden" name="displayedPrice" value="(.+)"/>', content)
  if len(prices) > 0:
    price = int(float(prices[0]) * 100)
  else:
    prices = re.findall('a-color-price">\$(\d+.\d\d)</span', content)
    if len(prices) > 0:
      price = int(float(prices[0]) * 100)
      
  url = bookinfo.Items.Item.DetailPageURL
  
#   if (price == UNREALISTICPRICE):
#     url = "http://www.goodreads.com/search.xml?key=" + GOODREADS_ACCESS_KEY_ID + "&q=" + query
#     u = urllib.urlopen(url)
#     response = u.read()
#     results = xmlparser.xml2obj(response)
  
  return [int(price), url]
  
def GetGooglePrice(isbn):
# return list with first element as price and second as url
  isbnurl = "https://www.googleapis.com/books/v1/volumes?q=" + isbn + "+isbn"
  content = urllib.urlopen(isbnurl).read()
  decoder = json.JSONDecoder()
  price = UNREALISTICPRICE
  url="google"
  
  id = decoder.decode(content)['items'][0]['id']
  idurl = "https://www.googleapis.com/books/v1/volumes/" + id
    
  content = urllib.urlopen(idurl).read()
  price = int(decoder.decode(content)['saleInfo']['retailPrice']['amount']*100)
  url = "https://play.google.com/store/books/details?id=" + id
  
  return [int(price), url]
                    
# --------------- Main Page -------------------

class MainPage(webapp2.RequestHandler):
  def get(self):
    currentsession = LoadSession(self.request.cookies)
    if currentsession.user.id:
      myuser = currentsession.user
      url = "/logout"
      url_linktext = 'Logout'
      loggedin = True  
      				  
    else:
      url = "/login/google"
      url_linktext = 'Login'
      loggedin = False
      myuser = []

    template_values = {
      'myuser': myuser,
      'possibleformats': possibleformats,
      'loggedin': loggedin,
      'url': url,
      'version': version,
      'url_linktext': url_linktext,
    }
    
    template = jinja_environment.get_template('index.html')
    self.response.out.write(template.render(template_values))

class MyAuthors(webapp2.RequestHandler):
  def get(self):
    currentsession = LoadSession(self.request.cookies)
    if currentsession.user.id:
      myuser = currentsession.user
      url = "/logout"
      url_linktext = 'Logout'
      loggedin = True  
      				  
    else:
      url = "/login/google"
      url_linktext = 'Login'
      loggedin = False
      myuser = []

    template_values = {
      'myuser': myuser,
      'possibleformats': possibleformats,
      'loggedin': loggedin,
      'url': url,
      'version': version,
      'url_linktext': url_linktext,
    }
    
    template = jinja_environment.get_template('authors.html')
    self.response.out.write(template.render(template_values))

# ------------ Book Operations ------------------------

class SearchBook(webapp2.RequestHandler):
  def get(self):
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    currentsession = LoadSession(self.request.cookies, connection = conn)
    if currentsession.user.id:
      user = currentsession.user
      logurl = "/logout"
      url_linktext = 'Logout'
      loggedin = True  
      				  
      currenttime = datetime.datetime.now()
      timedelta = datetime.timedelta(days=30)
      timedeltatiny = datetime.timedelta(seconds=15)
      query = self.request.get('query')
    
      query = urllib.quote_plus(query)
      url = "http://www.goodreads.com/search.xml?key=" + GOODREADS_ACCESS_KEY_ID + "&q=" + query
    
      u = urllib.urlopen(url)
      response = u.read()
      results = xmlparser.xml2obj(response)
    
      books = []
    
      try:    
        for work in results.search.results.work:
          goodreadsid = str(work.id.data)
          if goodreadsid:
            book = Book()
            if not book.get(goodreadsid = goodreadsid, connection = conn, addbook = False) or (str(book.date) < str(currenttime - timedelta)):
              book.goodreadsid = goodreadsid
              book.title  = work.best_book.title
              book.author = work.best_book.author.name
              authorgoodreadsid = work.best_book.author.id.data
              author = Author()
              author.get(goodreadsid = authorgoodreadsid, connection = conn, addauthor = True)
              logging.error(author.id)
              book.authorid = author.id
              book.small_img_url = work.best_book.small_image_url
              book.date = currenttime
              book.put(connection = conn)
            books.append(book)
      except AttributeError as er:
        pass
    
    else:
      logurl = "/login/google"
      url_linktext = 'Login'
      loggedin = False
      user = []
      books = []

    template_values = {
      'myuser': user,
      'books': books,
      'possibleformats': possibleformats,
      'loggedin': loggedin,
      'url': logurl,
      'version': version,
      'url_linktext': url_linktext,
    }
    
    conn.close()
    template = jinja_environment.get_template('search.html')
    self.response.out.write(template.render(template_values))

class AddBook(webapp2.RequestHandler):  
  def post(self):
    goodreadsids = self.request.get_all('goodreadsid')
    bookids = self.request.get_all('bookid')
    # Only one of these two should have something in it...
    
    formats = self.request.get_all('format')
    labels = self.request.get_all('label')
    price = self.request.get('price')
    
    if goodreadsids:
      self.add(ids = goodreadsids, idtype = "goodreads", formats = formats, labels = labels, price = price)
    if bookids:
      self.add(ids = bookids, idtype = "book", formats = formats, labels = labels, price = price)
    
    self.redirect('/search')
    
  def get(self):
   self.post()

  def add(self, ids, idtype, formats, labels, price):
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    session = LoadSession(self.request.cookies, connection = conn)
    currenttime = datetime.datetime.now()
    notifieddelta = datetime.timedelta(days=session.user.notificationwaittime)

    for id in ids:
      print id
      id = str(id)
      book = Book()
      if idtype == "goodreads":
        book.get(goodreadsid = id, connection = conn)
      elif idtype == "book":
        book.get(id = id, connection = conn)
      else:
        return
      userbook = UserBook()
      userbook.userid = session.user.id
      userbook.bookid = book.id
      userbook.price = int(float(price) * 100)
      userbook.acceptedformats = formats
      userbook.labels = labels
      userbook.archived = False
      userbook.date = currenttime
      userbook.notified = currenttime - notifieddelta
      userbook.put(connection = conn)
      book.addtoqueue()

    conn.close()
    
class ArchiveBook(webapp2.RequestHandler):
  def get(self):
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    currentsession = LoadSession(self.request.cookies, connection = conn)
    bookid = self.request.get('bookid')
    userbook = UserBook()
    userbook.get(bookid = bookid, userid = currentsession.user.id, connection = conn)
    userbook.archived = True
    userbook.date = datetime.datetime.now()
    userbook.put()
    self.redirect('/')
  
class RestoreBook(webapp2.RequestHandler):
  def get(self):
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    currentsession = LoadSession(self.request.cookies, connection = conn)
    bookid = self.request.get('bookid')
    userbook = UserBook()
    userbook.get(bookid = bookid, userid = currentsession.user.id, connection = conn)
    userbook.archived = False
    userbook.date = datetime.datetime.now()
    userbook.put()
    self.redirect('/')
  
class DeleteBook(webapp2.RequestHandler):
  def get(self):
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    currentsession = LoadSession(self.request.cookies, connection = conn)
    bookid = self.request.get('bookid')
    userbook = UserBook()
    userbook.get(bookid = bookid, userid = currentsession.user.id, connection = conn)
    userbook.delete(connection = conn)
    self.redirect('/')

  def post(self):
    self.get()

class EditBook(webapp2.RequestHandler):
  def get(self):
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    currentsession = LoadSession(self.request.cookies, connection = conn)
    bookid = self.request.get('bookid')
    userbook = UserBook()
    userbook.get(bookid = bookid, userid = currentsession.user.id, connection = conn)
    book = Book()
    book.get(id = bookid, connection = conn)

    template_values = {
    	'book': book,
    	'myuser': currentsession.user,
    	'userbook': userbook,
    	'possibleformats': possibleformats,
    }
    
    template = jinja_environment.get_template('edit.html')
    self.response.out.write(template.render(template_values))

  def post(self):
    self.get()

class ProduceDisplayBooksXML(webapp2.RequestHandler):
  def get(self):
    currentsession = LoadSession(self.request.cookies)
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
  
    c.execute("SELECT bookid FROM userbooks WHERE userid = ?", (currentsession.user.id,)) 
    userbooks = c.fetchall()
    
    xmlfile = "<?xml version= \"1.0\"?><content>"
    for item in userbooks:
      displaybook = DisplayBook()
      displaybook.get(item[0], currentsession.user, connection = conn)
      xmlfile = xmlfile + displaybook.xml()
    xmlfile = xmlfile + "</content>"
    xmlfile = xmlfile.replace("&", "&amp;")
    self.response.headers['Content-Type'] = 'text/xml'
    self.response.out.write(xmlfile)

class ProduceDisplayBooks(webapp2.RequestHandler):
  def get(self):
    currentsession = LoadSession(self.request.cookies)
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    
    c.execute("SELECT bookid FROM userbooks WHERE userid = ?", (currentsession.user.id,)) 
    userbooks = c.fetchall()
    display = {}
    display['authors'] = {}
    display['books'] = {}
    authorlist = []
    
    for item in userbooks:
      displaybook = {}
      displaybook['priceavailable'] = False
      displaybook['free'] = False
      formats = []
      book = Book()
      author = Author()
      userbook = UserBook()

      bookid = item[0]
      book.get(id = bookid, connection = conn)
      userbook.get(bookid = bookid, userid = currentsession.user.id, connection = conn)

      displaybook['book'] = book.dict()

      for format in userbook.acceptedformats:
        formatdict = {}
        formatdict['type'] = format
        if format in book.prices:
          formatdict['price'] = book.prices[format][0]
          formatdict['url'] = book.prices[format][1]
        else:
          formatdict['price'] = UNREALISTICPRICE
          formatdict['url'] = ""
        if (formatdict['price'] <= userbook.price):
          displaybook['priceavailable'] = True
          if (formatdict['price'] <= 0):
            displaybook['free'] = True
        formatdict['price'] = FormatPrice(formatdict['price'])
        formats.append(formatdict)
      displaybook['formats'] = formats
      displaybook['labels'] = userbook.labels
      displaybook['price'] = FormatPrice(userbook.price)
      if userbook.archived:
        displaybook['archived'] = True
      else:
        displaybook['archived'] = False

      if book.authorid not in authorlist:
        authorlist.append(book.authorid)
      display['books'][bookid] = displaybook
    
    for authorid in authorlist:  
      author.get(id = authorid, connection = conn)
      display['authors'][authorid] = author.dict()
   
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(json.dumps(display, indent = 2))

class BatchEdit(webapp2.RequestHandler):
  def get(self):
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    currentsession = LoadSession(self.request.cookies, connection = conn)
    currenttime = datetime.datetime.now()
    notifieddelta = datetime.timedelta(days=7)

    bookids = self.request.get_all('bookid')
    action = self.request.get('action')
    format = self.request.get('format')
    label = self.request.get('label')
    price = self.request.get('price')
    
    for bookid in bookids:
      userbook = UserBook()
      userbook.get(bookid = bookid, userid = currentsession.user.id, connection = conn)
      if (action == "addlabel"):
        if (label not in set(userbook.labels)):
          userbook.labels.append(label)
          userbook.labels.sort()
      elif (action == "removelabel"):
        if (label in set(userbook.labels)):
          userbook.labels.remove(label)
      elif (action == "addformat"):
        if (format not in set(userbook.acceptedformats)):
          userbook.acceptedformats.append(format)
          userbook.acceptedformats.sort()
          userbook.date = currenttime
          userbook.notified = currenttime - notifieddelta
          book = Book()
          book.get(id = userbook.bookid, connection = conn)
          book.updateEditions(connection = conn)
      elif (action == "removeformat"):
        if (format in set(userbook.acceptedformats)):
          userbook.acceptedformats.remove(format)
      elif (action == "price"):
        userbook.price = int(float(price) * 100)
        userbook.date = currenttime
        userbook.notified = currenttime - notifieddelta
      elif (action == "archive"):
        userbook.archived = True
        userbook.date = datetime.datetime.now()
      elif (action == "restore"):
        userbook.archived = False
        userbook.notified = currenttime - notifieddelta
        userbook.date = datetime.datetime.now()
      userbook.put(connection = conn)

# ------------ Author Operations ------------------------

class EditAuthors(webapp2.RequestHandler):
  def get(self):
    currentsession = LoadSession(self.request.cookies)
    if currentsession.user.id:
      myuser = currentsession.user
      url = "/logout"
      url_linktext = 'Logout'
      loggedin = True  
      				  
      conn = sqlite3.connect(topleveldirectory + "/" + db)
      c = conn.cursor()
  
      c.execute("SELECT DISTINCT books.authorid FROM books, userbooks WHERE userbooks.userid = ? AND books.id = userbooks.bookid", (currentsession.user.id,)) 
      authorids = c.fetchall()
      
      otherauthors = []
    
      c.execute("SELECT DISTINCT authorid FROM userauthors WHERE userid = ? AND archived = ?", (currentsession.user.id, False)) 
      userauthorids = c.fetchall()
      
      userauthors = []
          
      try:    
        for id in userauthorids:
          author = Author()
          author.get(connection = conn, id = id[0])
          userauthors.append(author)
      except:
        pass
        
      try:    
        for id in authorids:
          if id not in userauthorids:
           author = Author()
           author.get(connection = conn, id = id[0])
           otherauthors.append(author)
      except:
        pass
      
    else:
      url = "/login/google"
      url_linktext = 'Login'
      loggedin = False
      myuser = []
      userauthors = []
      otherauthors = []

    template_values = {
      'myuser': myuser,
      'userauthors': sorted(userauthors, key = methodcaller('lastName')),
      'otherauthors': sorted(otherauthors, key = methodcaller('lastName')),
      'loggedin': loggedin,
      'url': url,
      'version': version,
      'url_linktext': url_linktext,
    }
    
    template = jinja_environment.get_template('editauthors.html')
    self.response.out.write(template.render(template_values))

class ArchiveAuthor(webapp2.RequestHandler):
  def get(self):
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    currentsession = LoadSession(self.request.cookies, connection = conn)
    authorid = self.request.get('authorid')
    userauthor = UserAuthor()
    logging.error("Got it")
    if userauthor.get(authorid = authorid, userid = currentsession.user.id, connection = conn):
      userauthor.archived = True
      userauthor.put()
      logging.error(userauthor.archived)
    self.redirect('/')
  
class TrackAuthor(webapp2.RequestHandler):
  def get(self):
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    currentsession = LoadSession(self.request.cookies, connection = conn)
    authorid = self.request.get('authorid')
    userauthor = UserAuthor()
    userauthor.get(authorid = authorid, userid = currentsession.user.id, connection = conn, addauthor = True)
    userauthor.archived = False
    userauthor.put()
    author = Author()
    author.get(id = userauthor.authorid)
    author.addtoqueue()
    self.redirect('/')
  
class IgnoreBook(webapp2.RequestHandler):
  def get(self):
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    currentsession = LoadSession(self.request.cookies, connection = conn)
    bookid = self.request.get('bookid')
    book = Book()
    book.get(id = bookid, connection = conn)
    
    userauthor = UserAuthor()
    userauthor.get(authorid = book.authorid, userid = currentsession.user.id, connection = conn)
    
    userauthor.ignore.append(str(bookid))
    userauthor.ignore = list(set(userauthor.ignore))

    userauthor.put(connection = conn)
    self.redirect('/')
  
class AddAuthorBook(webapp2.RequestHandler):
  def get(self):
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    currentsession = LoadSession(self.request.cookies, connection = conn)
    bookid = self.request.get('bookid')
    
    userbook = UserBook()
    userbook.userid = currentsession.user.id
    userbook.bookid = bookid
#     userbook.put(connection = conn)

    book = Book()
    book.get(id = bookid, connection = conn)

    template_values = {
    	'book': book,
    	'myuser': currentsession.user,
    	'userbook': userbook,
    	'possibleformats': possibleformats,
    }
    
    template = jinja_environment.get_template('editauthorbook.html')
    self.response.out.write(template.render(template_values))
  
class RestoreAuthorBook(webapp2.RequestHandler):
  def get(self):
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    currentsession = LoadSession(self.request.cookies, connection = conn)
    bookid = self.request.get('bookid')
    book = Book()
    book.get(id = bookid, connection = conn)
    
    userauthor = UserAuthor()
    userauthor.get(authorid = book.authorid, userid = currentsession.user.id, connection = conn)
    
    userauthor.ignore = list(set(userauthor.ignore))
    userauthor.ignore.remove(str(bookid))

    userauthor.put(connection = conn)
    self.redirect('/')
  
class ProduceDisplayAuthors(webapp2.RequestHandler):
  def get(self):
    currentsession = LoadSession(self.request.cookies)
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
  
    allauthors = {}
    allauthors['archived'] = []
    allauthors['visible'] = []
    archivedbooks = []
    addedbooks = []
    
    c.execute("SELECT bookid, archived FROM userbooks WHERE userid = ?", (currentsession.user.id,)) 
    userbooks = c.fetchall()
    
    for item in userbooks:
      if item[1]:
        archivedbooks.append(item[0])
      else:
        addedbooks.append(item[0])
    
    c.execute("SELECT authorid FROM userauthors WHERE userid = ?", (currentsession.user.id,)) 
    userauthors = c.fetchall()
    
    for item in userauthors:
      userauthor = UserAuthor()
      author = Author()
      userauthor.get(authorid = item[0], userid = currentsession.user.id, connection = conn)
      author.get(id = item[0], connection = conn)
            
      authorinfo = {}
      authorinfo['author'] = author.dict()
      authorinfo['trackedbooks'] = []
      authorinfo['addedbooks'] = []
      authorinfo['archivedbooks'] = []
      authorinfo['ignoredbooks'] = []
      
      c.execute("SELECT id FROM books WHERE authorid = ?", (author.id,)) 
      authorbooks = c.fetchall()
      
      for bookitem in authorbooks:
        book = Book()
        book.get(id = bookitem[0], connection = conn)
        if book.id in archivedbooks:
          authorinfo['archivedbooks'].append(book.dict())
        elif book.id in addedbooks:
          authorinfo['addedbooks'].append(book.dict())
        elif str(book.id) in userauthor.ignore:
          authorinfo['ignoredbooks'].append(book.dict())
        else:
          authorinfo['trackedbooks'].append(book.dict())
    
      if userauthor.archived:
        allauthors['archived'].append(authorinfo)
      else:
        allauthors['visible'].append(authorinfo)

    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(json.dumps(allauthors, indent = 2))

# --------------------------- Info Pages -------------------------

class About(webapp2.RequestHandler):
  def get(self):
    currentsession = LoadSession(self.request.cookies)
    if currentsession.user.id:
      logurl = "/logout"
      url_linktext = 'Logout'
      loggedin = True  
    else:
      logurl = "/login/google"
      url_linktext = 'Login'
      loggedin = False

    template_values = {
      'loggedin': loggedin,
      'url': logurl,
      'version': version,
      'url_linktext': url_linktext,
    }
    
    template = jinja_environment.get_template('about.html')
    self.response.out.write(template.render(template_values))

class AccountSettings(webapp2.RequestHandler):
  def get(self):
    currentsession = LoadSession(self.request.cookies)
    if currentsession.user.id:
      user = currentsession.user
      logurl = "/logout"
      url_linktext = 'Logout'
      loggedin = True  
      				  
    else:
      logurl = "/login/google"
      url_linktext = 'Login'
      loggedin = False
      user = []

    template_values = {
      'myuser': user,
      'possibleformats': possibleformats,
      'loggedin': loggedin,
      'url': logurl,
      'version': version,
      'url_linktext': url_linktext,
    }
    
    template = jinja_environment.get_template('accountsettings.html')
    self.response.out.write(template.render(template_values))

class CurrentDeals(webapp2.RequestHandler):
  def get(self):
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    c = conn.cursor()
    session = LoadSession(self.request.cookies, connection = conn)
    currenttime = datetime.datetime.now()
    notifieddelta = datetime.timedelta(days=7)
    
    if session.user.id:
      logurl = "/logout"
      url_linktext = 'Logout'
      loggedin = True  
      				  
    else:
      logurl = "/login/google"
      url_linktext = 'Login'
      loggedin = False
      
    c.execute("SELECT bookid FROM userbooks WHERE notified > ? ORDER BY notified DESC", (str(currenttime-notifieddelta),))
    userbooks = c.fetchall()
    
    displaybooks=[]
    for item in userbooks:
      displaybook = DisplayBook()
      displaybook.get(item[0], connection = conn)
      displaybooks.append(displaybook)

    template_values = {
      'books': displaybooks,
      'loggedin': loggedin,
      'url': logurl,
      'version': version,
      'url_linktext': url_linktext,
    }
    
    conn.close()
    template = jinja_environment.get_template('currentdeals.html')
    self.response.out.write(template.render(template_values))

class Coupons(webapp2.RequestHandler):
  def get(self):
    currentsession = LoadSession(self.request.cookies)

    if currentsession.user.id:
      url = "/logout"
      url_linktext = 'Logout'
      loggedin = True  
      				  
    else:
      url = "/login/google"
      url_linktext = 'Login'
      loggedin = False
      
    dealsurl = "http://couponfeed.linksynergy.com/coupon?token=" + LINKSHARE_TOKEN
    u = urllib.urlopen(dealsurl)
    response = u.read()
    results = xmlparser.xml2obj(response)
    
    coupons=[]
    for deal in results.link:
      coupon = Coupon()
      coupon.offer = deal.offerdescription
      coupon.merchant = deal.advertisername
      coupon.url = deal.clickurl
      coupons.append(coupon)

    template_values = {
      'coupons': coupons,
      'loggedin': loggedin,
      'url': url,
      'version': version,
      'url_linktext': url_linktext,
    }
    
    template = jinja_environment.get_template('coupons.html')
    self.response.out.write(template.render(template_values))

class UpdateSettings(webapp2.RequestHandler):  
  def post(self):
    conn = sqlite3.connect(topleveldirectory + "/" + db)
    session = LoadSession(self.request.cookies, connection = conn)
    session.user.update(self.request, connection = conn)
    conn.close()
    self.redirect('/accountsettings')

# ----------------------------- CRON --------------------------------
    
def UpdateAllBooks(connection = "", force = False):
  if connection:
    conn = connection
  else:
    conn = sqlite3.connect(topleveldirectory + "/" + db)
  c = conn.cursor()
  
  c.execute("SELECT id FROM books ORDER BY lastupdatedprices") 
  books = c.fetchall()
  
  UpdateBooks(connection, force, books)  
  
def UpdateUserBooks(connection = "", force = False):
  if DEBUG:
    print "Only updating userbooks"
    
  if connection:
    conn = connection
  else:
    conn = sqlite3.connect(topleveldirectory + "/" + db)
  c = conn.cursor()
  
  c.execute("SELECT DISTINCT bookid FROM userbooks") 
  books = c.fetchall()
  
  UpdateBooks(connection, force, books)  
  
  if not connection:
    conn.close()

def UpdateAuthors(connection = "", force = False, books = []):
  if connection:
    conn = connection
  else:
    conn = sqlite3.connect(topleveldirectory + "/" + db)
  c = conn.cursor()
  
  c.execute("SELECT DISTINCT authorid FROM userauthors") 
  authors = c.fetchall()

  for item in authors:
    author = Author()
    author.get(id = item[0], connection = conn)
    print author.name
    for attempt in range(3):
      try:
        author.updateBooks(connection = conn, force = force)
        break
      except urllib2.HTTPError:
        time.sleep(1 * (attempt+1))
      except (AttributeError, TypeError, IndexError):
        return
      except Exception as inst:
        logging.error("UPDATE AUTHOR ERROR: author = " + str(author.id))
        return
  
  CleanUpEditions(connection = conn)
  
  if not connection:
    conn.close()

def UpdateBooks(connection = "", force = False, books = []):
  if connection:
    conn = connection
  else:
    conn = sqlite3.connect(topleveldirectory + "/" + db)
  c = conn.cursor()
  
  for item in books:
    book = Book()
    book.get(id = item[0], connection = conn)
    print book.title
    time.sleep(2)
    print "sleep"
    for attempt in range(3):
      try:
        book.updateEditions(connection = conn, force = force)
        break
      except urllib2.HTTPError:
        time.sleep(1 * (attempt+1))
      except (AttributeError, TypeError, IndexError):
        return
      except Exception as inst:
        logging.error("UPDATE PRICE ERROR")
        return
  
  CleanUpEditions(connection = conn)
  
  if not connection:
    conn.close()

def CleanUpEditions(connection = ""):
  if connection:
    conn = connection
  else:
    conn = sqlite3.connect(topleveldirectory + "/" + db)
  c = conn.cursor()
  
  c.execute("SELECT isbn FROM editions") 
  editions = c.fetchall()
  
  for item in editions:
    edition = Edition()
    edition.get(isbn = str(item[0]), connection = conn)
    if str(edition.lowestprice) == str(UNREALISTICPRICE):
      edition.delete()
  
def UpdatePriceCron(connection = "", force = False, useronly = False):
  logging.info("BEGAN UPDATE PRICE CRON")
  currenttime = datetime.datetime.now()
  useremail = {}
  lowpricebooks = []
  notify = False
  
  if connection:
    conn = connection
  else:
    conn = sqlite3.connect(topleveldirectory + "/" + db)
  c = conn.cursor()
  
  if useronly:
    UpdateUserBooks(connection = conn, force = force)
  else:
    UpdateAuthors(connection = conn, force = force)
    UpdateAllBooks(connection = conn, force = force)
  
  c.execute("SELECT bookid, userid FROM userbooks") 
  userbooks = c.fetchall()
  
  for item in userbooks:
    userbook = UserBook()
    userbook.get(bookid = item[0], userid = item[1], connection = conn)
    
    if userbook.archived:
      continue
    
    user = User()
    user.get(id = userbook.userid)
    notifieddelta = datetime.timedelta(days = int(user.notificationwaittime or 7))
    if (userbook.notified and (str(userbook.notified) > str(currenttime - notifieddelta))):
      continue

    book = Book()
    book.get(id = userbook.bookid, connection = conn)
    for format in userbook.acceptedformats:
      try:
        priceandurl = book.prices[format]
      except:
        continue
      if (priceandurl[0] != "") and (priceandurl[0] <= userbook.price):
        lowpricebook = LowPriceBooks()
        lowpricebook.email = user.preferredemail or user.gmail
        lowpricebook.title = book.title
        lowpricebook.author = book.author
        lowpricebook.format = format
        lowpricebook.price = FormatPrice(priceandurl[0])
        lowpricebook.url = priceandurl[1]
        lowpricebooks.append(lowpricebook)
        notify = True
      if notify:
        userbook.notified = currenttime
        userbook.put(connection = conn)
        notify = False
    
  for book in lowpricebooks:
    email = []
    if (book.email in useremail):
      email.append(useremail[book.email])
    else:
      email.append("The following book(s) have become available in your price range: \n\n")
    email.append(book.title)
    email.append("\n")
    email.append(book.author)
    email.append("\n")
    email.append(book.format)
    email.append(": ")
    email.append(book.price)
    email.append("\n")
    email.append(book.url)
    email.append("\n")
    email.append("\n")
    useremail[book.email] = "".join(email)
	
  for key in useremail:
    to = [key]
    body = useremail[key]
    bcc = [GOOGLE_EMAIL]
    subject = "You have new books available"
    if version == "prod":
      SendMail(to, [], bcc, subject, body)
          
  if not connection:
    conn.close()
  
def SendMail(to, cc, bcc, subject, body):
#   to, cc, and bcc are lists
  msg = MIMEText(body)
  msg['Subject'] = subject
  msg['From'] = GOOGLE_EMAIL
  msg['To'] = ", ".join(to)
  msg['CC'] = ", ".join(cc)

  s = smtplib.SMTP('smtp.gmail.com')
  s.ehlo()
  s.starttls()
  s.ehlo()
  s.login(GOOGLE_EMAIL, GOOGLE_PASSWORD)
  s.sendmail(GOOGLE_EMAIL, to + cc + bcc, msg.as_string())
  s.quit()
  
def GetKindleDeals(connection = ""):
  if connection:
    conn = connection
  else:
    conn = sqlite3.connect(topleveldirectory + "/" + db)
  c = conn.cursor()
  
  url = "http://www.amazon.com/gp/feature.html?docId=1000677541"
  content = urllib.urlopen(url)
  ignorenext = False
  isbns = []
  links = []
  for line in content:
    marker = "alt=\"Kindle Daily Deal\""
    if marker in line:
      newlinks = re.findall('<a href="([\d\w/=&?_-]+)">', line)
      newisbns = re.findall('/dp/([\d\w]+)', line)
      if len(newisbns) < len(newlinks):
        for i in range(0, len(newlinks)):
          foo = re.findall('/dp/([\d\w]+)', newlinks[i])
          if len(foo) == 0:
            links.append(newlinks[i])
      isbns = isbns + newisbns
          
  isbns = list(set(isbns))
  links = list(set(links))    
    
  if not connection:
    conn.close()
# -----------------------------  Final Stuff ---------------------


application = webapp2.WSGIApplication([('/', MainPage),
                               ('/search', SearchBook),
                               ('/myauthors', MyAuthors),
                               ('/editauthors', EditAuthors),
                               ('/login/google', google_login),
                               ('/logout', logout),
                               ('/login/google/auth', google_authenticate),
                               ('/archive', ArchiveBook),
                               ('/ignore', IgnoreBook),
                               ('/addauthorbook', AddAuthorBook),
                               ('/restoreauthorbook', RestoreAuthorBook),
                               ('/archiveauthor', ArchiveAuthor),
                               ('/trackauthor', TrackAuthor),
                               ('/getdisplaybooks.xml', ProduceDisplayBooksXML),
                               ('/getdisplaybooks.json', ProduceDisplayBooks),
                               ('/getdisplayauthors.json', ProduceDisplayAuthors),
                               ('/restore', RestoreBook),
                               ('/delete', DeleteBook),
                               ('/edit', EditBook),
                               ('/batchedit', BatchEdit),
                               ('/about', About),
                               ('/currentdeals', CurrentDeals),
                               ('/coupons', Coupons),
                               ('/accountsettings', AccountSettings),
                               ('/updatesettings', UpdateSettings),
                               ('/updatepricecron', UpdatePriceCron),
                               ('/add', AddBook)],
                              debug=True)


