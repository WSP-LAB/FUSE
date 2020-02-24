import ConfigParser
import sys, os
import time
import hashlib
import socket
import json
import multiprocessing
import functools
from multiprocessing import Process, Queue,Pool
import re
import urllib
import urllib2
import zlib
import gzip
import StringIO

import fileuploader
import filemutator
import rabbitmq

def ungzip(data,encode=None):
  if encode != None:
    if "deflate" in encode.lower():
      ret = zlib.decompress(data, 16+zlib.MAX_WBITS)
    elif "gzip" in encode.lower():
      tmp = StringIO.StringIO(data)
      ret = gzip.GzipFile(fileobj=tmp).read()
  else:
    ret = data
  return ret


Debug = False

TotalRequest = 0
ProcessedRequest = 0
SuccessRequest = 0

upload_time = 0
vfy_time = 0
mutation_time = 0

PROCESS_LIMIT = 8


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
    # search the unique value
    uniqRe = re.compile(self.uniquePattern)
    try:
      uniqObj = uniqRe.search(binary)
      if uniqObj != None:
        uniqueValue = uniqObj.string[uniqObj.start()+4:uniqObj.end()-3]
      else:
        uniqRe = re.compile("=3c=21=2d=2d[0-9|a-f]{16}=2d=2d=3e") # For M6
        uniqObj = uniqRe.search(binary)
        uniqueValue = uniqObj.string[uniqObj.start()+12:uniqObj.end()-9]
    except:
      print "[-] Fail to find Unique value in Binary"
      exit(0)
    if filename != None:
      filename_hash = filename[:32]
    else:
      filename_hash = None

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


def mutation_wrapping(ch, method, properties, body, manager_wrap, type_seed_files_wrap, inQueue_wrap):
  if ch.is_open:
    ch.basic_ack(method.delivery_tag)
  mutate_box = rabbitmq.unwrap(body)
  mutate_list = list(mutate_box["mutate_list"])
  mutate_type = mutate_box["type"]
  for seed_file in type_seed_files_wrap[mutate_type]:
    mut_start = time.time()
    if len(mutate_list)==0:
      mutate_list = []
      mutate_data = manager_wrap.makeMutatedData(mutate_list, seed_file, None)
      mutate_data["filename"] = mutate_data["filename"]+'_SEED'
    else:
      mutate_data = manager_wrap.makeMutatedData(mutate_list, seed_file, None)

    requestSeed=fileuploader.makeUploadRequest(conf.target,mutate_data)
    isuploaded =  fileuploader.uploadFile(conf.target,requestSeed)
    if mutate_data['fileext'] != None and len(mutate_data['fileext']) > 0:
      file_name = mutate_data['filename']+'.'+mutate_data['fileext']
    else:
      file_name = mutate_data['filename']
    mut_end = time.time()
    mut_time = mut_end - mut_start
    inQueue_wrap.put([isuploaded, mutate_data, seed_file, mutate_list, file_name,mutate_type, mut_time])

def mutation(rabbitmq_name, manager, type_seed_files, inQueue):
  rbQueue = rabbitmq.mqMsgqIo()
  rbQueue.msgqDeclare(rabbitmq_name)
  cb = functools.partial(mutation_wrapping,manager_wrap=manager,type_seed_files_wrap=type_seed_files, inQueue_wrap=inQueue)
  rbQueue.workerize(cb)

def verifier(monitorClient,isuploaded, mutate_data, seed_file, mutate_list, file_name):
  if isuploaded[0]:
    if conf.framework["monitorEnable"]:
      isvalid = monitorClient.fileValidator(file_name,mutate_data['content'])
      if isvalid[0] == True:
        return [True, mutate_data, seed_file, isvalid[1]['msg'], mutate_list, isvalid[1]['path']]
      else:
        return [False, mutate_data, seed_file, "NOT_CREATED", mutate_list, None]
    else:
      if len(conf.target["webUploadFilesURL"])>0:

        if conf.target["webUploadFilesParameter"]!=None:
          UploadList = urllib2.Request(conf.target["webUploadFilesURL"],(conf.target["webUploadFilesParameter"]))
          if conf.target["webUploadFilesParameter"][0]== '{':
            fileuploader.addHeader(UploadList,conf.target["webHost"],contenttype="application/json",referer=conf.target["webUploadURL"])
          elif conf.target["webUploadFilesParameter"][0]== '<':
            fileuploader.addHeader(UploadList,conf.target["webHost"],contenttype="application/xml",referer=conf.target["webUploadURL"])
        else:
          UploadList = urllib2.Request(conf.target["webUploadFilesURL"])
          fileuploader.addHeader(UploadList,conf.target["webHost"],referer=conf.target["webUploadURL"])
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
      insteadPattern = mutate_data['filename']

      isvalid = monitorClient.fileValidator(BodyData,mutate_data['content'],mutate_data['filename'],mutate_data['fileext'])
      if isvalid[0] == True:
        return [True, mutate_data, seed_file, "Monitor Not Used", mutate_list, isvalid[1]]
      else:
        return [False, mutate_data, seed_file, "Monitor Not Used", mutate_list, isvalid[1]]

  else:
    return [False, mutate_data, seed_file, "UPLOAD_FAIL",mutate_list, None]


def verifier_thread(target, framework, manager, inQueue, rbQueue):
  global TotalRequest
  global ProcessedRequest
  global vfy_time
  global mutation_time
  chainCounter = 0
  success_mutation = {}
  fail_mutation = []
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
  accessValid = None
  base_url = target["webHost"]
  if base_url[-1] != '/':
    base_url += "/"
  if base_url[:7] != "http://" and base_url[:8] != "https://":
    base_url = "http://"+base_url

  print "[+] Connection Succeed"
  while True:
    rbQueue.process_data_events()
    if not inQueue.empty():
      data = inQueue.get()
      ProcessedRequest += 1
      vfy_start = time.time()
      seedType = data[5]
      ret = verifier(monitorClient,data[0],data[1],data[2],data[3],data[4])
      mutate_list = ret[4]
      mutation_time += data[6]
      if ret[0] == True:
        path = ret[5].replace(target["webRootPath"],"")
        url = base_url+path

        accessValid = fileuploader.accessValidation(target, url, ret[1]["content"], "FUSE_GEN",seedType)
      else:
        url = ""
        accessValid = [None,None]
      if seedType not in success_mutation.keys():
        success_mutation[seedType] = []

      mut_combination ='+'.join(data[3])

      if accessValid[0] and ((seedType=='js' and accessValid[1]=="Code Exposed") or (seedType=='php' and (accessValid[1]=="Execution Succeed")) or((seedType == 'html' or seedType == 'xhtml') and (accessValid[1]=="Code Exposed" or accessValid[1]=="Execution Succeed"))):
        print "Success = [{}] - {}".format(seedType, '+'.join(mutate_list))
        if seedType in success_mutation.keys():
          success_mutation[seedType].append(mutate_list)
        else:
          success_mutation[seedType] = [mutate_list]
      elif seedType=='php' and (mut_combination != '' and ((accessValid[0] and accessValid[1] == "Code Exposed") or (not accessValid[0] and accessValid[1] == "Forbidden"))): #PHP PCE - about Extension without M12
        print "Success = [{}] - {}".format(seedType, '+'.join(mutate_list))
        if seedType in success_mutation.keys():
          success_mutation[seedType].append(mutate_list)
        else:
          success_mutation[seedType] = [mutate_list]

      else:
        fail_mutation.append([mutate_list,seedType])
      accessValid.append(url)
      accessValid.append(ret)
      result.append(accessValid)
      vfy_end = time.time()
      vfy_time += vfy_end-vfy_start
    else:
      continue

    if TotalRequest == ProcessedRequest:
      if chainCounter > conf.framework['mutationChainLimit']:
        print "[+] Chain counter hits the limit - {}".format(chainCounter)
        break
      else:
        chainCounter += 1

      for ele in fail_mutation:
        failed_mutate_ele = '+'.join(ele[0])
        failed_mutate_seed = ele[1]
        append_list = manager.mutation_chain(failed_mutate_ele, failed_mutate_seed, success_mutation[failed_mutate_seed])
        for i in append_list:
          mutate_box = {}
          mutate_box["type"] = failed_mutate_seed
          mutate_box["mutate_list"] = i.split("+")
          mutate_box_wrapped = rabbitmq.wrap(mutate_box)
          TotalRequest += 1
          rbQueue.push(mutate_box_wrapped)
      fail_mutation=[]
      print "mutations = {}/{}".format(ProcessedRequest, TotalRequest)
      if TotalRequest == ProcessedRequest:
        break

  return result

def sec2time(second):
  second = int(second)
  sec_ = second%60
  min_ = second/60
  hour_ = min_/60
  min_ = min_%60
  sec_ = "{} sec".format(sec_)
  if min_ != 0:
    min_ = "{} min ".format(min_)
  else:
    min_ = ""
  if hour_ != 0:
    hour_ = "{} hour ".format(hour_)
  else:
    hour_ = ""
  return hour_+min_+sec_

def reporter(results, start_time, mid_time, target, seed_list, seed_report):
  global SuccessRequest
  pce = {} # Potencial Code Execution
  ce = {} # Code Execution
  err = {}

  print "Result Count - {}".format(len(results))

  start = time.time()
  # Determine folder name which is written mutation files that succeed to upload
  folder_name = target["webHost"]
  if folder_name[:7] == "http://":
    folder_name = folder_name[7:]
  elif folder_name[:8] == "https://":
    folder_name = folder_name[8:]

  if "/" in folder_name:
    folder_name = folder_name.split("/")[0]

  if not os.path.isdir(folder_name):
    os.mkdir(folder_name)
  base_url = target["webHost"]
  if base_url[-1] != '/':
    base_url += "/"
  if base_url[:7] != "http://" and base_url[:8] != "https://":
    base_url = "http://"+base_url
  print "[+] Creates the Report...."
  counter = 0
  all_results = len(results)
  for data_ in results:
    if not (data_[0] == None):
      accessValid = data_[0:2]
      url = data_[2]
      i = data_[3]
      seedType = i[2].rsplit(".",1)[-1]
      if not accessValid[0] and accessValid[1] == "Forbidden" and (seedType == 'php'):
        SuccessRequest += 1
        if seedType not in pce.keys():
          pce[seedType] = []
        pce[seedType].append((i,url))
      elif accessValid[0] and "M06" in i[4] and (seedType == 'html' or seedType == 'xhtml'):
        SuccessRequest += 1
        if seedType not in ce.keys():
          ce[seedType] = []
        ce[seedType].append((i,url))
      elif accessValid[0]:
        if accessValid[1] == "Execution Succeed" and (seedType == 'php' or seedType == 'html' or seedType == 'xhtml'):
          SuccessRequest += 1
          if seedType not in ce.keys():
            ce[seedType] = []
          ce[seedType].append((i,url))
        elif accessValid[1] == "Code Exposed" and (seedType == 'html' or seedType == 'xhtml'):
          SuccessRequest += 1
          if seedType not in ce.keys():
            ce[seedType] = []
          ce[seedType].append((i,url))
        elif accessValid[1] == "Code Exposed" and (seedType == 'php' or seedType == 'js'):
          SuccessRequest += 1
          if seedType not in pce.keys():
            pce[seedType] = []
          pce[seedType].append((i,url))
        else:
          print "something Wrong - [{}, {}] - {}".format(accessValid[0],accessValid[1],i[2].rsplit('.',1)[-1])
          if seedType not in err.keys():
            err[seedType] = []
          err[seedType].append((i,url))
      else:
        if seedType not in err.keys():
          err[seedType] = []
        err[seedType].append((i,url))

  end = time.time()
  print "verify_time : {}".format(vfy_time)
  print "Finished headless browser test - {} sec".format(end-start)
  output = "File Upload Sinkpoint Explorer v0.2 - Report\n\n"
  output += "[+] Host : {}\n".format(target["webHost"])
  output += "[+] Tried Seed : {}\n".format(', '.join(seed_list))
  output += "[+] Upload Target URL : {}\n".format(target["webUploadURL"])
  output += "[+] Total Execution Time : {}\n".format(sec2time(end-start_time)) # Start
  output += "[+] Preparing Time : {}\n".format(sec2time(mid_time-start_time))
  output += "[+] Average Uploading Time ({} Process) : {}\n".format(PROCESS_LIMIT,sec2time(mutation_time/PROCESS_LIMIT))
  output += "[+] Verify Time : {}\n".format(sec2time(vfy_time))
  output += "[+] Tried to Upload File : {}\n".format(TotalRequest)
  output += "[+] Uploaded Files having CE/PCE ability : {}\n\n".format(SuccessRequest)

  output += "\n"


  for ceType in ce.keys():
    output += "[+] Found Code Executable Uploaded Files( {} ) - {} files\n".format(ceType, len(ce[ceType]))
    for ele in ce[ceType]:
      i = ele[0]
      if i[1]['fileext'] != None and len(i[1]['fileext']) > 0:
        file_name = i[1]['filename']+'.'+i[1]['fileext']
      else:
        file_name = i[1]['filename']
      output += "  Seed({})\t{}:  {}\n".format(i[2],'+'.join(i[4]),file_name)
      output += "   -> {}\n".format(ele[1])
      with open("{}/ce_{}".format(folder_name,file_name),"wb") as fp:
        fp.write(i[1]['content'])
    output += "\n"

  for pceType in pce.keys():
    output += "[+] Found Potentially Code Executable Uploaded Files( {} ) - {} files\n".format(pceType, len(pce[pceType]))
    for ele in pce[pceType]:
      i = ele[0]
      if i[1]['fileext'] != None and len(i[1]['fileext']) > 0:
        file_name = i[1]['filename']+'.'+i[1]['fileext']
      else:
        file_name = i[1]['filename']
      output += "  Seed({})\t{}:  {}\n".format(i[2],'+'.join(i[4]),file_name)
      output += "   -> {}\n".format(ele[1])
      with open("{}/pce_{}".format(folder_name,file_name),"wb") as fp:
        fp.write(i[1]['content'])
    output += "\n"

  for errType in err.keys():
    output += "[-] Upload succeed but not usable ( {} ) - {} files\n".format(errType, len(err[errType]))
    for ele in err[errType]:
      i=ele[0]
      if i[1]['fileext'] != None and len(i[1]['fileext']) > 0:
        file_name = i[1]['filename']+'.'+i[1]['fileext']
      else:
        file_name = i[1]['filename']
      output += "  Seed({})\t{}:  {}\n".format(i[2],'+'.join(i[4]),file_name)
      output += "   -> {}\n".format(ele[1])
    output += "\n"

  ########### S1 test ############
  # 1. upload .htaccess
  s1request=fileuploader.makeUploadRequest(conf.target,fileuploader.makeS1Data())
  isS1Uploaded =  fileuploader.uploadFile(conf.target,s1request)
  s1Flag = False
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

  if isS1Uploaded:
    print ".htaccess uploaded"
    # 2. upload s1 test data
    testdata = fileuploader.makeS1TestData()
    s1TestRequest = fileuploader.makeUploadRequest(conf.target,testdata)
    isS1TestUploaded = fileuploader.uploadFile(conf.target,s1TestRequest)
    if isS1TestUploaded[0]:
      print "Test data uploaded"
      # 3. php execution test
      if conf.framework["monitorEnable"]:
        isvalid = monitorClient.fileValidator(testdata["filename"],testdata['content'])
      else:
        if len(conf.target["webUploadFilesURL"])>0:
          if conf.target["webUploadFilesParameter"]!=None:
            UploadList = urllib2.Request(conf.target["webUploadFilesURL"],conf.target["webUploadFilesParameter"])
            if conf.target["webUploadFilesParameter"][0]== '{':
              fileuploader.addHeader(UploadList,conf.target["webHost"],contenttype="application/json",referer=conf.target["webUploadURL"])
            elif conf.target["webUploadFilesParameter"][0]== '<':
              fileuploader.addHeader(UploadList,conf.target["webHost"],contenttype="application/xml",referer=conf.target["webUploadURL"])
          else:
            UploadList = urllib2.Request(conf.target["webUploadFilesURL"])
            fileuploader.addHeader(UploadList,conf.target["webHost"],referer=conf.target["webUploadURL"])

          UploadList.add_header('Cookie',conf.target["webLoginCookie"])
          UploadList.add_header('Accept-encoding', 'gzip,deflate')

          UploadList_ret = urllib2.urlopen(UploadList)
          if "content-encoding" in UploadList_ret.headers.keys():
            encode = UploadList_ret.headers['content-encoding']
          else:
            encode = None

          if Debug:
            print "[http request] non-monitor mode .htaccess test urlopen 1"
          BodyData = ungzip(UploadList_ret.read(),encode)
        else:
          BodyData = isS1TestUploaded[1]

        isvalid = monitorClient.fileValidator(BodyData,testdata['content'],testdata['filename'],testdata['fileext'])
      if isvalid[0]:
        print "upload data file created"
        if conf.framework["monitorEnable"]:
          path = isvalid[1]['path'].replace(target["webRootPath"],"")
          url = base_url+path
        else:
          url = base_url+isvalid[1]
        accessValid = fileuploader.accessValidation(target, url, testdata['content'], "FUSE_GEN", "php")
        if accessValid[0] and accessValid[1] == "Execution Succeed":
          print "Execution Success"
          s1Flag = True
  if s1Flag:
    output += "[+] S1 - .htaccess upload success & It works. (Vulnerable!)\n\n"
  else:
    output += "[-] S1 - .htaccess upload fail or It doesn't work (Secure!)\n\n"
    ########### S1+M3_JPG test ############
    # 1. upload .htaccess
    M3_type_list = ['image/jpeg','image/png','image/gif','application/zip','application/pdf','application/x-gzip']
    for mimetype in M3_type_list:
      s1request=fileuploader.makeUploadRequest(conf.target,fileuploader.makeS1Data(m3_mut=mimetype))
      isS1Uploaded =  fileuploader.uploadFile(conf.target,s1request)
      if isS1Uploaded[0]:
        print ".htaccess uploaded"
        # 2. upload s1 test data
        testdata = fileuploader.makeS1TestData()
        s1TestRequest = fileuploader.makeUploadRequest(conf.target,testdata)
        # 3. php execution test
        if conf.framework["monitorEnable"]:
          isvalid = monitorClient.fileValidator(testdata["filename"],testdata['content'])
        else:
          if len(conf.target["webUploadFilesURL"])>0:
            if conf.target["webUploadFilesParameter"]!=None:
              UploadList = urllib2.Request(conf.target["webUploadFilesURL"],conf.target["webUploadFilesParameter"])
              if conf.target["webUploadFilesParameter"][0]== '{':
                fileuploader.addHeader(UploadList,conf.target["webHost"],contenttype="application/json",referer=conf.target["webUploadURL"])
              elif conf.target["webUploadFilesParameter"][0]== '<':
                fileuploader.addHeader(UploadList,conf.target["webHost"],contenttype="application/xml",referer=conf.target["webUploadURL"])
            else:
              UploadList = urllib2.Request(conf.target["webUploadFilesURL"])
              fileuploader.addHeader(UploadList,conf.target["webHost"],referer=conf.target["webUploadURL"])

            UploadList.add_header('Cookie',conf.target["webLoginCookie"])
            UploadList.add_header('Accept-encoding', 'gzip,deflate')
            UploadList_ret = urllib2.urlopen(UploadList)
            if "content-encoding" in UploadList_ret.headers.keys():
              encode = UploadList_ret.headers['content-encoding']
            else:
              encode = None
            if Debug:
              print "[http request] non-monitor mode .htaccess test urlopen 2"
            BodyData = ungzip(UploadList_ret.read(),encode)
          else:
            BodyData = isS1TestUploaded[1]

          isvalid = monitorClient.fileValidator(BodyData,testdata['content'],testdata['filename'],testdata['fileext'])


        if isvalid[0]:
          print "upload data file created"
          if conf.framework['monitorEnable']:
            path = isvalid[1]['path'].replace(target["webRootPath"],"")
            url = base_url+path
          else:
            url = base_url+isvalid[1]
          accessValid = fileuploader.accessValidation(target, url, testdata['content'], "FUSE_GEN", "php")
          if accessValid[0] and accessValid[1] == "Execution Succeed":
            print "Execution Success"
            s1Flag = True
            break
    if s1Flag:
      output += "[+] S1+M3 {} - .htaccess upload success & It works. (Vulnerable!)\n\n".format(mimetype)
    else:
      output += "[-] S1+M3 - .htaccess upload fail or It doesn't work (Secure!)\n\n"

  ####################################

  monitorClient.close()
  with open("{}_{}.txt".format(folder_name,"report"),"w") as fp:
    fp.write(output)
  #print output
  print "[!] Report file created - {}_{}.txt\nDone...!".format(folder_name,"report")




if __name__ == "__main__":
  conf = configDigester(sys.argv[1])
  inQueue = Queue()
  outQueue = Queue()
  rbQueue = rabbitmq.mqMsgqIo()
  rbQname = "mutate_op"
  rbQueue.msgqDeclare(rbQname,True)
  start_time = time.time()
  print "[+] Start Login Process"
  if conf.target['webLoginURL'] != '':
    conf.target['webLoginCookie'] = fileuploader.tryLogin(conf.target)
  else:
    print "[~] Pass Login Process"
    conf.target['webLoginCookie'] = ''
  fileuploader.formParser(conf.target)
  print "[+] Make Mutate List"
  opListCreator = filemutator.mutate_manager()
  #opList = opListCreator.combinatedOpList()
  # Append file path - temp
  seed_files = os.listdir('seed')
  resource_files = os.listdir('resource')

  seed_files = ['seed/' + x for x in seed_files]
  opList = []
  for i in seed_files:
    opList.append(i.rsplit('.',1)[1])

  resource_files = ['resource/' + x for x in resource_files]

  #total_ops = opList.keys()

  results = []
  mid_time= time.time()
  mutation_length = 0
  seed_result = {}

  pidList = []
  type_seed_files={}
  for key in opList:
    type_seed_files[key] = filemutator.get_type_seed_files(key, seed_files)

  while len(pidList)<PROCESS_LIMIT:
    p = Process(target = mutation, args=(rbQname, opListCreator, type_seed_files, inQueue))
    p.daemon = True
    p.start()
    pidList.append(p)

  for key in opList:
    mutate_box = {}
    mutate_box["type"] = key
    mutate_box["mutate_list"] = ""
    TotalRequest += 1
    rbQueue.push(rabbitmq.wrap(mutate_box))

  print "[+] Verifier start"
  results = verifier_thread(conf.target, conf.framework ,opListCreator, inQueue, rbQueue)
  print "[+] Finishing Upload Process...."
  while inQueue.qsize() != 0 or not inQueue.empty():
    pass

  while len(pidList)>0:
    for i in pidList:
      i.terminate()
      i.join()
      pidList.pop(pidList.index(i))
  #end_time = time.time()

  inQueue.close()
  inQueue.join_thread()
  reporter(results, start_time, mid_time, conf.target, opList, seed_result)

