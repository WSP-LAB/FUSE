import ConfigParser
import sys, os
import time
import hashlib
import socket
import json
import functools
import re
import urllib
import urllib2
import zlib
import gzip
import datetime
import cookielib
import Cookie
from bs4 import BeautifulSoup
import random
import StringIO as StrIO
import itertools
import mimetools
import mimetypes
import utils


def ungzip(data,encode=None):
  if encode != None:
    if "deflate" in encode.lower():
      ret = zlib.decompress(data, 16+zlib.MAX_WBITS)
    elif "gzip" in encode.lower():
      tmp = StrIO.StringIO(data)
      ret = gzip.GzipFile(fileobj=tmp).read()
  else:
    ret = data
  return ret


Debug = False

class MultiPartForm(object):
  """Accumulate the data to be used when posting a form."""
  """Provided by Ahnmo @ KAIST WSPLAB"""

  def __init__(self):
    self.form_fields = []
    self.files = []
    self.boundary = mimetools.choose_boundary()
    return

  def get_content_type(self):
    return 'multipart/form-data; boundary=%s' % self.boundary

  def add_field(self, name, value):
    """Add a simple field to the form data."""
    self.form_fields.append((name, value))
    return

  def add_file(self, fieldname, filename, fileHandle, mimetype=None):
    """Add a file to be uploaded."""
    body = fileHandle
    if mimetype is None:
      mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    self.files.append((fieldname, filename, mimetype, body))
    return

  def __str__(self):
    """Return a string representing the form data, including attached files."""
    # Build a list of lists, each containing "lines" of the
    # request.  Each part is separated by a boundary string.
    # Once the list is built, return a string where each
    # line is separated by '\r\n'.
    parts = []
    part_boundary = '--' + self.boundary

    # Add the form fields
    parts.extend(
      [ part_boundary,
        'Content-Disposition: form-data; name="%s"' % name,
        '',
        value,
      ]
      for name, value in self.form_fields
      )

    # Add the files to upload
    parts.extend(
      [ part_boundary,
        'Content-Disposition: file; name="%s"; filename="%s"' % \
         (field_name, filename),
        'Content-Type: %s' % content_type,
        '',
        body,
      ]
      for field_name, filename, content_type, body in self.files
      )

    # Flatten the list and add closing boundary marker,
    # then return CR+LF separated data
    flattened = list(itertools.chain(*parts))
    flattened.append('--' + self.boundary + '--')
    flattened.append('')
    return '\r\n'.join(flattened)



class configDigester(object):
  def __init__(self, confpath):
    self.parser = ConfigParser.ConfigParser()
    self.parser.read(confpath)
    self.target = {}
    self.framework = {}
    self.target["id"] = self.parser.get('USER_CREDENTIAL','ID')
    self.target["pw"] = self.parser.get('USER_CREDENTIAL','PW')
    self.target["webRootPath"] = self.parser.get('USER_CREDENTIAL','WebRootPath')
    self.target["webHost"] = self.parser.get('USER_CREDENTIAL','WebHost')
    self.target["webLoginURL"] = self.parser.get('USER_CREDENTIAL','WebLoginURL')
    self.target["webLoginPageURL"] = self.parser.get('USER_CREDENTIAL','WebLoginPageURL')
    self.target["webLoginIDName"] = self.parser.get('USER_CREDENTIAL','WebLoginIDName')
    self.target["webLoginPWName"] = self.parser.get('USER_CREDENTIAL','WebLoginPWName')
    self.target["webLoginCSRFName"] = self.parser.get('USER_CREDENTIAL','WebLoginCSRFName')
    self.target["webLoginSuccessStr"] = self.parser.get('USER_CREDENTIAL','WebLoginSuccessStr')
    self.target["webLoginAdditionalValue"] = self.parser.get('USER_CREDENTIAL', 'WebLoginAdditionalValue')
    self.target["webUploadURL"] = self.parser.get('USER_CREDENTIAL','WebUploadURL')
    self.target["webUploadPageURL"] = self.parser.get('USER_CREDENTIAL','WebUploadPageURL')
    self.target["webUploadFormAttr"] = self.parser.get('USER_CREDENTIAL','WebUploadFormAttr')
    self.target["webUploadCSRFName"] = self.parser.get('USER_CREDENTIAL','WebUploadCSRFName')
    self.target["webUploadCustomHeader"] = self.parser.get('USER_CREDENTIAL','WebUploadCustomHeader')
    self.target["webUploadSuccessStr"] = self.parser.get('USER_CREDENTIAL','WebUploadSuccessStr')
    self.target["webUploadAdditionalValue"] = self.parser.get('USER_CREDENTIAL','WebUploadAdditionalValue')
    self.target["webUploadedFileUrlPattern"] = self.parser.get('USER_CREDENTIAL', 'WebUploadedFileUrlPattern')
    self.target["webUploadFilesURL"] = self.parser.get('USER_CREDENTIAL', 'WebUploadFilesURL')

    tmpParameter = self.parser.get('USER_CREDENTIAL', 'WebUploadFilesParameter')

    self.framework["mutationChainLimit"] = self.parser.getint('DETECTOR_CONF','MutationChainLimit')
    self.framework["monitorEnable"] = self.parser.getboolean('DETECTOR_CONF','MonitorEnable')
    self.framework["monitorHost"] = self.parser.get('DETECTOR_CONF','MonitorHost')
    try:
      self.framework["monitorPort"] = int(self.parser.get('DETECTOR_CONF','MonitorPort'))
    except:
      self.framework["monitorPort"] = 20174

    if len(tmpParameter)==0:
      self.target["webUploadFilesParameter"] = None
    elif ";" in tmpParameter and "=" in tmpParameter:
      tmpParameter = tmpParameter.split(";")
      if len(tmpParameter[0])==0:
        self.target["webUploadFilesParameter"] = None
        return

      self.target["webUploadFilesParameter"] = {}
      for i in tmpParameter:
        tmpList = i.split("=",1)
        self.target["webUploadFilesParameter"][tmpList[0]] = tmpList[1]
      self.target["webUploadFilesParameter"] = urllib.urlencode(self.target["webUploadFilesParameter"])
    else:
      # It is not formated and seperated Parameter of POST Request but it is body of POST Request.
      self.target["webUploadFilesParameter"] = tmpParameter


class MonitorDisableClient(object):
  pattern = None
  filename = None
  uniquePattern = None
  baseurl = None
  def __init__(self,FilePattern,uploadUrl):
    self.pattern = FilePattern
    self.filename = "[a-f|0-9]{32}(_M[0-9]{1,2}[A-Z|0-9]*)+(\.[a-z|A-Z|0-9]*)+"
    if "%genfile#" in self.pattern:
      self.pattern = self.pattern.replace("%genfile#",self.filename)
    self.uniquePattern = "<!--[0-9|a-f]{16}-->"
    self.baseurl = uploadUrl.rsplit("/",1)[0]

  def fileValidator(self,body,binary,filename=None, ext=None):
    if "%filename#" in self.pattern:
      if filename != None and ext != None:
        directURL = self.pattern.replace("%filename#",filename).replace(conf.target['webHost']+'/','')
        if len(ext)>0:
          directURL += ".{}".format(ext)
        if directURL[:4] == "http":
          directURL = directURL.split("/",3)[-1]
        return [True,directURL]
      else:
        print "[-] %filename# custom tag in uploaded file name pattern needs more data"
        exit(0)

    body = body.replace('\\','')
    cursor = re.finditer(self.pattern, body,0)
    uniqueValue = binary
    filename_hash = filename

    try:
      condid_url_list = []
      while True:
        target = cursor.next()
        condid_url = target.string[target.start():target.end()]

        if 'http://' not in condid_url:
          condid_url = condid_url.split("/")
          tmp_url = self.baseurl
          while True:
            if ".." in condid_url[0]:
              condid_url = condid_url[1:]
              tmp_url = tmp_url.rsplit('/',1)[0]
            elif "." == condid_url[0]:
              condid_url = condid_url[1:]
            elif "" == condid_url[0]:
              tmp_url = '/'.join(tmp_url.split("/",3)[:-1])
              condid_url = condid_url[1:]
            else:
              condid_url = tmp_url+'/'+'/'.join(condid_url)
              break

        if filename_hash != None and filename_hash in condid_url:
          condid_url = condid_url.replace(conf.target['webHost']+'/','')
          return [True, condid_url]
        else:
          condid_url_list.append(condid_url)
    except StopIteration as e:
      pass

    for condid_url in condid_url_list:
      try:
        conn_uploaded = urllib2.Request(condid_url)
        conn_uploaded.add_header('Cookie',conf.target['webLoginCookie'])
        if Debug:
          print "[http request] non-monitor mode file verification urllib open"
        res_uploaded_test = urllib2.urlopen(conn_uploaded)
        condid_url = condid_url.replace(conf.target['webHost']+'/','')
      except urllib2.HTTPError as e:
        if Debug:
          print "[-] Access Error - {}".format(e)
        continue
      if res_uploaded_test.code == 200:

        res_uploaded_text = res_uploaded_test.read()
        if uniqueValue in res_uploaded_text:
          return [True, condid_url]
        continue
      elif res_uploaded_test.code == 403:
        continue # uploaded file is exist but can not confirm the file
      elif res_uploaded_test.code == 500:
        continue # uploaded file is exist but can not confirm the file.
      else:
        pass
    return [False, "Can not found proper url"]
  def close(self):
    pass

class MonitorClient(object):
  __ip__ = None
  def __init__(self,ip,port=20174):
    self.__ip__ = ip
    self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.conn.connect((ip,port))

  def fileValidator(self,filename,filebinary):
    filehash = hashlib.md5(filebinary).hexdigest()
    if filename[0] != '.':
      namespliter = filename.rsplit('.',1)
    else:
      namespliter = filename[1:].rsplit('.',1)
      namespliter[0] = '.'+namespliter[0]

    if len(namespliter) < 2:
      namespliter.append(None)
    sendData = {}
    sendData['type'] = "verify"
    sendData['filename'] = namespliter[0]
    sendData['ext'] = namespliter[1]
    sendData['filehash'] = filehash
    self.send(sendData)
    response = self.recv()
    if response == None:
      print "Fail to Communicate Server"
    else:
      if response["type"] == "Fail":
        return (False, None)
      else:
        if filehash != response["hash"]:
          print "[-] File hash is not matched"
        return (True, response)

  def recv(self):
    recvData = ""
    try:
      while True:
        recvDataPart = self.conn.recv(10)
        if not recvDataPart:
          break
        elif '\n' in recvDataPart:
          recvData += recvDataPart
          break
        recvData += recvDataPart
    except:
      print "[-] Error occured during recieving command"
      return None
    if recvData[0] == "\"":
      recvData = recvData[1:]
    if recvData[-2] == "\"":
      recvData = recvData[:-2]
    if '\\' in recvData:
      recvData = recvData.replace('\\','')
    try:
      retData = json.loads(recvData)
    except:
      print "[-] Error occured during parsing recieved command"
      return None
    return retData

  def send(self,data):
    sendData = json.dumps(data)
    while True:
      try:
        self.conn.send(sendData+'\n')
        break
      except:
        print "[Monitor Client Send] Restart monitor socket"
        self.conn.close()
        self.__init__(self.__ip__)


  def close(self):
    closedata={}
    closedata['type'] = 'disconn'
    try:
      self.send(closedata)
    except socket.error as e:
      print "[Monitor Client] {}".format(e)
      pass
    self.conn.close()


def verifier(monitorClient, isuploaded, file_name, file_ext, contents):
  if isuploaded:
    if conf.framework["monitorEnable"]:
      isvalid = monitorClient.fileValidator(file_name,contents)
      if isvalid[0] == True:
        return [True, isvalid[1]['path']]
      else:
        return [False, None]
    else:
      if len(conf.target["webUploadFilesURL"])>0:

        if conf.target["webUploadFilesParameter"]!=None:
          UploadList = urllib2.Request(conf.target["webUploadFilesURL"],(conf.target["webUploadFilesParameter"]))
          if conf.target["webUploadFilesParameter"][0]== '{':
            addHeader(UploadList,conf.target["webHost"],contenttype="application/json",referer=conf.target["webUploadURL"])
          elif conf.target["webUploadFilesParameter"][0]== '<':
            addHeader(UploadList,conf.target["webHost"],contenttype="application/xml",referer=conf.target["webUploadURL"])
        else:
          UploadList = urllib2.Request(conf.target["webUploadFilesURL"])
          addHeader(UploadList,conf.target["webHost"],referer=conf.target["webUploadURL"])
        UploadList.add_header('Accept-encoding', 'gzip,deflate')

        UploadList.add_header('Cookie',conf.target["webLoginCookie"])

        if Debug:
          print "[http request] non-monitor mode verifier urlopen"

        UploadList_ret = urllib2.urlopen(UploadList)

        if "content-encoding" in UploadList_ret.headers.keys():
          encode = UploadList_ret.headers['content-encoding']
        else:
          encode = None

        BodyData = ungzip(UploadList_ret.read(),encode)
      else:
        BodyData = isuploaded[1]

      isvalid = monitorClient.fileValidator(BodyData,contents,file_name,file_ext)
      if isvalid[0] == True:
        return [True, isvalid[1]]
      else:
        return [False, isvalid[1]]

  else:
    return [False, None]


def varifier_wrapper(target, framework, isuploaded, file_name,file_ext, contents, file_type):
  result = []
  if conf.framework['monitorEnable']:
    while True:
      try:
        monitorClient = MonitorClient(conf.framework['monitorHost'],conf.framework['monitorPort'])
      except:
        print "cannot connect to webserver.. try again"
        continue
      break
  else:
    monitorClient = MonitorDisableClient(conf.target['webUploadedFileUrlPattern'],conf.target['webUploadURL'])

  base_url = target["webHost"]
  if base_url[-1] != '/':
    base_url += "/"
  if base_url[:7] != "http://" and base_url[:8] != "https://":
    base_url = "http://"+base_url

  seedType = file_type
  ret = verifier(monitorClient,isuploaded,file_name,file_ext,contents)

  return ret[0]


# 302 Request Catcher
class ResponseCatcher(urllib2.HTTPErrorProcessor):
  def http_response(self,request,response):
    return response
  https_response = http_response

# add Headers in request
def addHeader(req, host,referer=None,contenttype=None):
  req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36')
  req.add_header('Accept','text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8')
  req.add_header('Origin', host)
  if referer != None:
    req.add_header('Referer',referer)
  if contenttype != None:
    req.add_header('Content-Type',contenttype)

def charEscaper(data,condition):
  if data == None:
    return ''
  data = list(data)
  for i in range(0,len(data)):
    if data[i] in condition:
      data[i] = '%{}#'.format(hex(ord(data[i]))[2:])
  return ''.join(data)

def charDescaper(data):
  ret = ""
  pass_counter = 0
  for i in range(0,len(data)):
    if pass_counter > 0:
      pass_counter -= 1
      continue
    if data[i] == '%' and (i+3 < len(data) and data[i+3] == '#'):
      ret += chr(int(data[i+1:i+3],16))
      pass_counter += 3
    else:
      ret += data[i]
  return ret


# cookie merge
def cookieMerger(origin,new):
  # escaping and descaping for evade Cookielib bug - array variable([])

  merger = Cookie.SimpleCookie()
  merger.load(charEscaper(origin,'[/]'))
  merger.load(charEscaper(new,'[/]'))

  for i in merger.keys():
    try:
      if merger[i].value[-1] == ',':
        merger[i] = merger[i].value[:-1]
    except:
      pass

  out = merger.output('',header='')
  out = out.split('\r\n')
  out = map(str.strip,out)
  out = charDescaper('; '.join(out))
  return out


def url_simplizer(baseurl, url):
  if baseurl[-1]=='/':
    base = baseurl[:-1]
  else:
    base = baseurl


  if 'http://' not in url:
    new_url = url.split("/")
    tmp_url = base
    while True:
      if ".." in new_url[0]:
        new_url = new_url[1:]
        tmp_url = tmp_url.rsplit('/',1)[0]
      elif "." == new_url[0]:
        new_url = new_url[1:]
      elif "" == new_url[0]:
        tmp_url = '/'.join(tmp_url.split("/",3)[:-1])
        new_url = new_url[1:]
      else:
        new_url = tmp_url+'/'+'/'.join(new_url)
        break
  else:
    new_url = url
  return new_url


# Try to Login
def tryLogin(target):
  CSRFName = None
  logined_page = None

  if target['webLoginCSRFName']:
    CSRFName = target['webLoginCSRFName']

  # Get basic cookies and CSRF Value if it is exist
  setCookie, CSRFValue = urlValidator(target,CSRFName)

  cookie_process = setCookie.split(',')
  setCookie=[]
  for i in cookie_process:
    setCookie.append(i.split(';',1)[0])
  setCookie = ';'.join(setCookie)

  # Set id, pw information
  data = {}
  data[target['webLoginIDName']]=target['id']
  data[target['webLoginPWName']]=target['pw']

  # Set CSRF Value if it is exist
  if CSRFValue != None and len(CSRFValue)>0 and CSRFValue[0]!='' and CSRFValue[0] != None:
    for i in CSRFValue:
      CSRFElement = i.split('=',1)
      data[CSRFElement[0]]=CSRFElement[1]

  # Set Additional Variable in POST Body
  additional = target['webLoginAdditionalValue'].split(';')
  if additional[0]!='':
    for i in additional:
     sp = i.split('=',1)
     data[sp[0]]=sp[1]

  # Build Request
  cookieJar = cookielib.CookieJar()
  loginOpener = urllib2.build_opener(ResponseCatcher, urllib2.HTTPCookieProcessor(cookieJar))
  req = urllib2.Request(target['webLoginURL'],urllib.urlencode(data))
  if 'webCSRFHeader' in target.keys() and target['webCSRFHeader'] != None:
    req.add_header(target['webCSRFHeader'][0],target['webCSRFHeader'][1])
  # if basic cookie exist, it is appended to request header
  if setCookie != '':
    req.add_header('Cookie',setCookie)

  # Add basic header
  addHeader(req,target['webHost'],referer=customTag(target,target["webLoginPageURL"]), contenttype='application/x-www-form-urlencoded')

  # try to login
  res = loginOpener.open(req)
  if 'set-cookie' in res.headers.keys():
    setCookie = cookieMerger(setCookie,res.headers['Set-Cookie'])

  # 302/303 processing
  if int(res.code) >= 300 and int(res.code) < 400:
    # Make Redirection Request using Location Header
    while res.code >= 300 and res.code < 400:
      if '/' not in res.headers['Location']:
        baseurl = target['webLoginPageURL'].rsplit('/',1)[0]
        red_req = urllib2.Request("{}/{}".format(baseurl,res.headers['Location']))
      elif 'http://' not in res.headers['Location']:
        # case for "Location : /relation/path"
        relocation_path = res.headers['Location']
        if relocation_path[0] == '/':
          relocation_path = relocation_path[1:]
        red_req = urllib2.Request("{}/{}".format(target['webHost'],relocation_path))

      else:
        # case for "Location : http://blah.blahblah.bl/relation/path"
        red_req = urllib2.Request(res.headers['Location'])

      logined_cookie = None

      # Merge given session cookie and append it to Redirection Request

     # append Basic header and Referer
      red_req.add_header('Referer',target['webLoginURL'])
      if setCookie != '':
        red_req.add_header('Cookie',setCookie)
      addHeader(red_req,target['webHost'])

      # Send Redirection Request
      res = loginOpener.open(red_req)
      if 'set-cookie' in res.headers.keys():
        setCookie = cookieMerger(setCookie,res.headers['Set-Cookie'])

    logined_page = res.read()
  # 200 Processing - do not need to another processing
  elif res.code == 200:
    # get session cookie
    if 'set-cookie' in res.headers.keys():
      setCookie = cookieMerger(setCookie,res.headers['Set-Cookie'])
    logined_page = res.read()
  # response code is not 200 or 302 | 303, this login try maybe failed
  else:
    print "[-] Can not Login.."
  # Verify Login using string
  if target["webLoginSuccessStr"] in logined_page:
    print "[+] Login Success"
    return setCookie

  else:
    print "[-] Login Fail"
    exit(0)



# if url is valid, it returns default cookies.
def urlValidator(target,CSRF=None):
  url = customTag(target,target["webLoginPageURL"])
  cookieJar = cookielib.CookieJar()
  loginOpener = urllib2.build_opener(ResponseCatcher, urllib2.HTTPCookieProcessor(cookieJar))

  req = urllib2.Request(url)
  addHeader(req,target["webHost"])
  res = loginOpener.open(req)
  cookie = ''

  # 200 response is valid for login url. Others maybe not useable
  while True:
    if res.code >=300 and res.code < 400:
      if 'set-cookie' in res.headers.keys():
        cookie = res.headers['set-cookie']
      if 'http://' not in res.headers['Location']:
        # case for "Location : /relation/path"

       # print "*{}{}".format(target['webHost'],res.headers['Location'])
        red_req = urllib2.Request("{}{}".format(target['webHost'],res.headers['Location']))
      else:
        # case for "Location : http://blah.blahblah.bl/relation/path"
        red_req = urllib2.Request(res.headers['Location'])
      red_req.add_header('Cookie',cookie)
      addHeader(red_req,target['webHost'],target['webLoginPageURL'])
      if Debug:
        print "[http request] urlValidator urlopen"
      res = urllib2.urlopen(red_req)
      continue
    try:
      data = res.read()
    except:
      print "response read fail"
      exit(0)
    if res.code == 200 or len(data)>0:
      CSRFValue = None
      # if it has CSRF Token, get Token
      if CSRF!=None and CSRF != '':
        CSRFValue = getCSRFToken(res,data,CSRF,target)

      # if it has basic cookies, get cookie
      if 'set-cookie' in res.headers.keys():
        cookie = res.headers['set-cookie']

      # return both
      return cookie, CSRFValue

    else:
      # if url is not valid, return None
      return None, None

def getCSRFToken(res_obj, html,CSRFEles,target):
  CSRF_LIST = CSRFEles.split(';')
  ret = []
  target['webCSRFHeader'] = None
  for CSRF in CSRF_LIST:
    if "%cookietoken#" in CSRF:
      if 'set-cookie' in res_obj.headers.keys():
        setcookie_data = res_obj.headers['set-cookie']
      if 'webLoginCookie' in target.keys():
        target['webLoginCookie'] = cookieMerger(target['webLoginCookie'],setcookie_data)
      else:
        target['webLoginCookie'] = setcookie_data
    elif "%headertoken" in CSRF:
      header_name = CSRF.split(':',1)[1][:-1]
      header_name = header_name.split('@',1)
      if header_name[0] == 'html_tag': #%headertoken:html_metatag@taginfo=csrf-token=headername#
        soup = BeautifulSoup(html,'html.parser')
        findname = header_name[1].split('=')
        # findname [0] - tag [1] - attrname [2] - attrvalue [3] getAttrName [4] Header Name
        csrftoken = soup.find(findname[0],{findname[1]:re.compile(findname[2])})
        target['webCSRFHeader'] = [findname[4],csrftoken[findname[3]].encode('ascii')]

      elif header_name[0] == 'html_regex':
        findname = header_name[1].split('=')
        reg_obj = re.compile(findname[0])
        data = reg_obj.search(html)
        find_str = data.string[data.start():data.end()]
        reg_detail_obj = re.compile(findname[1])
        data = reg_detail_obj.search(find_str)
        csrftoken = data.string[data.start():data.end()]
        if data != None:
          target['webCSRFHeader'] = [findname[2],csrftoken]
        else:
          print "[-] CSRFToken was not found in upload page"
          exit(0)

      elif header_name[0] == 'header':
        if header_name[1] in res_obj.headers.keys():
          target['webCSRFHeader'] = [header_name,res_obj.headers[header_name[1]]]
        else:
          print "[-] Can't not found CSRF Token in Response Header"
          exit(0)
      else:
        print "[-] Weird CSRF Expression"
        exit(0)
    else:
      try:
        soup = BeautifulSoup(html,'html.parser')

        if "%reg" == CSRF[:4]:
          csrftoken = soup.find("input",{"name":re.compile(CSRF[5:-1])})

        else:
          csrftoken = soup.find("input",{"name":CSRF})

      except:
        ret.append(None)
        continue
      if csrftoken == None:
        ret.append(None)
        continue

      ret.append("{}={}".format(csrftoken['name'],csrftoken['value']))
  return ret

# upload form Parser to get upload processing url(action) and variables
# It use 'beautifulsoup4' library
def formParser(target):
  formAttr = target['webUploadFormAttr'].split(';')
  if len(formAttr[0]) == 0:
    return

  req = urllib2.Request(customTag(target,target['webUploadPageURL']))
  req.add_header('Cookie',target['webLoginCookie'])
  addHeader(req,target['webHost'])
  req.add_header('Accept-encoding', 'gzip,deflate')
  if Debug:
    print "[http request] formParser urlopen"
  res = urllib2.urlopen(req)
  if 'content-encoding' in res.headers.keys():
    cnt = res.headers['content-encoding']
  else:
    cnt = None
  body = ungzip(res.read(),cnt)
  soup = BeautifulSoup(body,'html.parser')
  attr = {}
  for i in formAttr:
    part = i.split('=',1)
    if len(part) != 2:
      part[1] = ''
    attr[part[0]] = part[1]
  if "enctype" not in attr.keys():
    attr["enctype"] = "multipart/form-data"
  form  =  soup.find("form",attr)
  input_cursor = form.findAll("input")
  param = []
  for i in  input_cursor:
    if not i.has_attr('name'):
      continue
    elif not i.has_attr('value'):
      i['value'] = ''
    if i['type']=="file":
      i['value'] = "%filebinary#"
    uniq = True
    for j in param:
      temp_param = j.split("=",1)
      if i['name'] == temp_param[0]:
        uniq = False # it makes multiple-valued parameter use first value.
        break
    if uniq:
      param.append("{}={}".format(i['name'],i['value']))
  if len(target['webUploadAdditionalValue'])!=0:
    checklist = target['webUploadAdditionalValue'].split(';')
    for check_params in checklist:
      checker_param = check_params.split('=',1)
      isexist_flag = False
      for i in range(0,len(param)):
       checked_param = param[i].split('=',1)
       if checker_param[0] == checked_param[0]:
         if checker_param[1]!='' and checker_param[1]=='%find#':
           param[i] = "{}={}".format(checker_param[0], checked_param[1])
         elif checker_param[1]!='' and checker_param[1]!='%find#':
           param[i] = "{}={}".format(checker_param[0], checker_param[1])
         isexist_flag = True
      if not isexist_flag and checked_param[1]!='%find#':
        param.append('{}={}'.format(checked_param[0], checked_param[1]))
      elif isexist_flag:
        pass
      else:
        print "  [!] Parameter {} isn't found from upload page".format(checker_param[0])
        param.append('{}='.format(checked_param[0]))

  if form['action'] == '':
    target['webUploadURL'] = target['webUploadPageURL']
  elif 'http:' not in form['action']:
    if '//' == form['action'][:2]:
      target['webUploadURL'] = 'http:'+form['action']
    elif '/' == form['action'][0]:
      target['webUploadURL'] = target['webHost'][:-1]+form['action']
    else:
      folder = target['webUploadPageURL'].rsplit("/",1)
      target['webUploadURL'] = folder[0]+'/'+form['action']
  else:
    target['webUploadURL'] = form['action']

  target['webUploadAdditionalValue'] = ';'.join(param)

#uploadFile
def makeUploadRequest(target,uploadFile):
  req = {}
  form = MultiPartForm()

  # Append CSRF Token to Body
  if (target['webUploadCSRFName'] != ''):
    semi_req = urllib2.Request(customTag(target,target['webUploadPageURL']))
    addHeader(semi_req, target['webHost'])
    semi_req.add_header('Cookie',target['webLoginCookie'])
    semi_req.add_header('Accept-encoding', 'gzip,deflate')
    if Debug:
      print "[http request] makeUploadRequest urlopen(CSRF Append)"
    semi_res = urllib2.urlopen(semi_req)
    if 'content-encoding' in semi_res.headers.keys():
      cnt = semi_res.headers['content-encoding']
    else:
      cnt = None
    semi_data = ungzip(semi_res.read(),cnt)
    semi_CSRF = getCSRFToken(semi_res,semi_data,target['webUploadCSRFName'],target)
    if semi_CSRF != None and len(semi_CSRF) > 0 and semi_CSRF[0] != '' and semi_CSRF[0] != None:
      for i in semi_CSRF:
        part = i.split('=',1)
        form.add_field(part[0],part[1])
    if "%dom:" in target['webUploadURL']:
        arg = target['webUploadURL'].split(':',1)[1].split('@')
        regex_urlform = re.compile(arg[0])
        regex_urlform_match = re.compile(arg[1][:-1])
        semi_data = semi_data.replace('\\','')
        reg_urlform = regex_urlform.search(semi_data)
        return_url = ""
        if reg_urlform != None:
          condid_url = reg_urlform.string[reg_urlform.start():reg_urlform.end()]
          reg_urlform_match = regex_urlform_match.search(condid_url)
          if reg_urlform_match != None:
            return_url = reg_urlform_match.string[reg_urlform_match.start():reg_urlform_match.end()]
        target["webDynamicUploadURL"] = None
        if return_url != "":
          target["webDynamicUploadURL"] = return_url
        else:
          print "[-] Not Found Dynamic upload URL"
          exit(0)

  # Append other parameters to Body
  append_field = target['webUploadAdditionalValue'].split(";")
  for i in append_field:
    part=i.split("=",1)
    if len(part) < 2:
      part.append('')

    # if parameter value or name determined by file..
    if "%filename#" in part[1]:
      if uploadFile["fileext"] != None and len(uploadFile["fileext"]) > 0:
        form.add_field(part[0],uploadFile["filename"]+"."+uploadFile["fileext"])# file name
      else:
        form.add_field(part[0],uploadFile["filename"])
    elif "%filebinary#" in part[1]:
      if uploadFile["fileext"] != None and len(uploadFile["fileext"]) > 0:
        form.add_file(part[0],uploadFile["filename"]+"."+uploadFile["fileext"],fileHandle=uploadFile["content"],mimetype=uploadFile["filetype"])
      else:
        form.add_file(part[0],uploadFile["filename"],fileHandle=uploadFile["content"],mimetype=uploadFile["filetype"])
    elif "%cookie" in part[1] or "%domtoken" in part[1] or "%randint" in part[1]:
      form.add_field(part[0],customTag(target,part[1]))
    else:
      form.add_field(part[0],part[1])

  # preparing return data
  req['body'] = str(form)
  req['type'] = form.get_content_type()
  req['filename'] = uploadFile['filename']
  return req

def customTag(target, data):
  tagExist = False
  if '%' in data and '#' in data:
    tagExist = True
  while tagExist:
    startPoint = data.index('%')
    endPoint = data.index('#')
    while True:
      try:
        svSp = data.index('%',startPoint+1)
      except:
        break
      if svSp > endPoint:
        break
      else:
        startPoint = svSp
    custom = data[data.index('%')+1:data.index('#')]
    replaced_data = None
    custom = custom.split(':',1)
    if custom[0] == "rndint":
      replaced_data = random.randrange(1,100000)
    elif custom[0] == "cookie":
      cookieManager = Cookie.SimpleCookie()
      cookieManager.load(charEscaper(target['webLoginCookie'],'[/'))
      if "reg" in custom[1]:
        regex_ = re.compile(custom[1].split(':',1)[1])
        for i in cookieManager.keys():
          reg_result = regex_.findall(charDescaper(i))
          if len(reg_result)>0:
            replaced_data = cookieManager[i].value
            break
      else:
        for i in cookieManager.keys():
          if charDescaper(i) == custom[1]:
            replaced_data = cookieManager[i].value
            break
    elif custom[0] == "domtoken":
      arg = custom[1].rsplit('@',1)
      token_req = urllib2.Request(customTag(target,target['webUploadPageURL']))
      token_req.add_header('cookie',target['webLoginCookie'])
      token_req.add_header('Accept-encoding', 'gzip,deflate')
      addHeader(token_req,target['webHost'])
      if Debug:
        print "[http request] custom tag - domtoken urllib2"
      token_res_obj = urllib2.urlopen(token_req)
      if "content-encoding" in token_res_obj.headers.keys():
        cnt = token_res_obj.headers['content-encoding']
      else:
        cnt = None
      token_res = ungzip(token_res_obj.read(),cnt)
      regex_token = re.compile(arg[0])
      reg_result = regex_token.findall(token_res)
      regex_extract = re.compile(arg[1])
      for i in reg_result:
        tmp = regex_extract.findall(i)
        if len(tmp)>0:
          replaced_data = tmp[0]
          break
      if "%dom:" in target['webUploadURL']:
        arg = target['webUploadURL'].split(':',1)[1].split('@')
        regex_urlform = re.compile(arg[0])
        regex_urlform_match = re.compile(arg[1])
        token_res = token_res.replace('\\','')
        reg_urlform = regex_urlform.search(token_res)
        return_url = ""
        if reg_urlform != None:
          condid_url = reg_urlform.string[reg_urlform.start():reg_urlform.end()]
          reg_urlform_match = regex_urlform_match.search(condid_url)
          if reg_urlform_match != None:
            return_url = reg_urlform_match.string[reg_urlform_match.start():reg_urlform_match.end()]
        target["webDynamicUploadURL"] = None
        if return_url != "":
          target["webDynamicUploadURL"] = return_url
        else:
          print "[-] Not Found Dynamic upload URL"
          exit(0)


    if replaced_data == None:
      replaced_data = ''
    data = data.replace('%{}#'.format(':'.join(custom)),replaced_data)
    if '%' not in data or '#' not in data:
      tagExist=False
  return data

def uploadFile(target, upload_req):
  if "%dom:" in target['webUploadURL']:
    url = target["webDynamicUploadURL"]
  else:
    url = customTag(target,target['webUploadURL'])
  url = url_simplizer(target['webUploadPageURL'], url)
  try:
    req = urllib2.Request(url.encode('ascii'))
    req.add_header('Content-Type', upload_req['type'])
    req.add_header('Content-Length', len(upload_req['body']))
    req.add_header('Cookie',target['webLoginCookie'])
    req.add_data(upload_req['body'])
    addHeader(req, target['webHost'], referer=customTag(target,target['webUploadPageURL']))
    if target['webUploadCustomHeader'] != '':
      custom = target['webUploadCustomHeader'].split('=',1)
      if len(custom) >0:
        req.add_header(custom[0], custom[1])
      else:
        print "[-] Custom Header is wrong"
        exit(0)
    if 'webCSRFHeader' in target.keys() and target['webCSRFHeader'] != None:
      req.add_header(target['webCSRFHeader'][0],target['webCSRFHeader'][1])
    req.add_header('Accept-encoding', 'gzip,deflate')

    if Debug:
      print "[http request] uploadFile urlopen"
    res_obj = urllib2.urlopen(req)
  except urllib2.HTTPError as e:
    res_obj = e

  if res_obj.code >=300 and res_obj.code<400:
    redirect_url = res_obj.headers['Location']
    while True:
     rereq = urllib2.Request(redirect_url)
     rereq.add_header('Accept-encoding','gzip,deflate')
     rereq.add_header('Cookie',target['webLoginCookie'])
     addHeader(rereq, target['webHost'], referer=url)
     try:
       if Debug:
         print "[http request] upload File - 302 re-urlopen"
       res_obj = urllib2.urlopen(rereq)
     except urllib2.HTTPError as e:
       res_obj = e
     if not (res_obj.code >=300 and res_obj.code<400):
       break
  if "content-encoding" in res_obj.headers.keys():
    encode = res_obj.headers['content-encoding']
  else:
    encode = None
  res = ungzip(res_obj.read(),encode)
  if res_obj.code == 200:
    return res
  else:
    return None


if __name__ == "__main__":
  conf = configDigester(sys.argv[1])
  print "[+] Start Login Process"
  if conf.target['webLoginURL'] != '':
    conf.target['webLoginCookie'] = tryLogin(conf.target)
  else:
    print "[~] Pass Login Process"
    conf.target['webLoginCookie'] = ''
  formParser(conf.target)

  #print "[+] Make Mutate List"
  #opListCreator = filemutator.mutate_manager()
  #opList = opListCreator.combinatedOpList()
  # Append file path - temp
  #seed_files = os.listdir('seed')
  resource_files = os.listdir('../resource')


  #opList = []
  #for i in seed_files:
  #  opList.append(i.rsplit('.',1)[1])

  resource_files = ['../resource/' + x for x in resource_files]

  #total_ops = opList.keys()


  for i in resource_files:
    fp = open(i,'rb')
    item_filecontent = fp.read()
    fp.close()
    item_filename = i.rsplit('/',1)[-1].rsplit('.',1)
    item_fileext = item_filename[-1]
    item_filename = item_filename[0]
    item_filetype = utils.extract_filetype(i)
    file_item = {
    'filename': hashlib.md5((str)(time.time())).hexdigest()+"_M0TEST",
    'fileext': item_fileext,
    'filetype': item_filetype,
    'content': item_filecontent
    }
    uploadRequest = makeUploadRequest(conf.target,file_item)
    isuploaded =  uploadFile(conf.target,uploadRequest)
    #print isuploaded
    results = varifier_wrapper(conf.target, conf.framework, isuploaded, item_filename, item_fileext, item_filecontent, item_filetype)
    #print results
    if results:
      print "[+] Yay! FUSE can process the configuration file!"
      exit(0)

  print "[-] Fail to process the configuration file..."


