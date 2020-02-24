import pyinotify
import json
import socket
import threading
import atexit
import time
import hashlib
import os

MONITOR_PATH='/var/www/html/'
MONITOR_PORT=20174           # Default value for test
EVENT_LIST_LIMITATION=8000
EVENT_LIST = []

#Debug = True
Debug = False

# Todo - Daemonize communication module

class FileEventHandler(pyinotify.ProcessEvent):
  def __init__(self):
    self.mutex = threading.Lock()

  def process_IN_ATTRIB(self,event):
    if Debug:
      print "[IN_ATTRIB] {}".format(event.pathname)
    self.mutex.acquire()
    if len(EVENT_LIST)>=EVENT_LIST_LIMITATION:
      for i in range(0,len(EVENT_LIST)-EVENT_LIST_LIMITATION+1):
        EVENT_LIST.remove(EVENT_LIST[0])
      if Debug:
        print "[!] EVENT_LIST Removed - {}".format(len(EVENT_LIST))
    if os.path.isdir(event.pathname):
      pass
    else:
      try:
        with open(event.pathname, 'r') as fp:
          binary = fp.read()
          #print binary
          tmpList = [event.pathname,hashlib.md5(binary).hexdigest()]
        if tmpList not in EVENT_LIST and os.path.isfile(event.pathname):
          EVENT_LIST.append([event.pathname,hashlib.md5(binary).hexdigest()])
          #EVENT_LIST.append([event.pathname,hashlib.md5(binary).hexdigest()])
        if Debug:
          print "[!] Appended - ({}){}".format(hashlib.md5(binary).hexdigest(),event.pathname)
      except:
        pass
    self.mutex.release()

  def process_IN_CREATE(self,event):
    self.mutex.acquire()
    if Debug:
      print "[IN_CREATE] {}".format(event.pathname)
    if len(EVENT_LIST)>=EVENT_LIST_LIMITATION:
      for i in range(0,len(EVENT_LIST)-EVENT_LIST_LIMITATION+1):
        EVENT_LIST.remove(EVENT_LIST[0])
      if Debug:
        print "[!] EVENT_LIST Removed - {}".format(len(EVENT_LIST))
    if os.path.isdir(event.pathname):
      pass
    else:
      try:
        with open(event.pathname, 'r') as fp:
          binary = fp.read()
          tmpList = [event.pathname,hashlib.md5(binary).hexdigest()]
        #print binary
        if tmpList not in EVENT_LIST and os.path.isfile(event.pathname):
          EVENT_LIST.append([event.pathname,hashlib.md5(binary).hexdigest()])
        if Debug:
         print "[!] Appended - ({}){}".format(hashlib.md5(binary).hexdigest(),event.pathname)
      except:
        pass
    self.mutex.release()

class EventCommunicator(object):
  def __init__(self,ip,port):
    self.host = ip
    self.port = port
    return
  def connWait(self):
    self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.server.bind((self.host,self.port))
    self.server.listen(5)
    self.conn, self.addr = self.server.accept()
  def recv(self):
    recvData = ""
    try:
      while True:
        recvDataPart = self.conn.recv(10)
        if not recvDataPart or len(recvDataPart)==0:
          break
        elif '\n' in recvDataPart:
          recvData += recvDataPart
          break
        recvData += recvDataPart
    except:
      print "Error occured during recieving command"
      return None
    if Debug:
      print "[RECV] {}".format(recvData)
    try:
      retData = json.loads(recvData)
    except:
      print "Error occured during parsing recieved command"
      return None
    return retData
  def send(self,data):
    sendData = json.dumps(data)
    self.conn.send(sendData+'\n')
  def close(self):
    self.conn.close()

def eventMonitor(path):
  monitorObj = pyinotify.WatchManager()
  monitorObj.add_watch(path,pyinotify.ALL_EVENTS, rec=True, auto_add=True)

  eventHandler = FileEventHandler()

  notifier = pyinotify.Notifier(monitorObj, eventHandler)
  notifier.loop()

def connectionThread(connObj):
  mutex = threading.Lock()
  while connObj:
    cmd = connObj.recv()
    ret_msg = {}
    try:
      type_ = cmd["type"]
      if type_  == 'disconn':
        if mutex.test():
          mutex.release()
        connObj.close()
        return
      filename = cmd["filename"]
      ext = cmd["ext"]
      filehash = cmd["filehash"]
      if Debug:
        print "[!] Parsed - filename : {}".format(filename)
        print "[!] Parsed - ext : {}".format(ext)
        print "[!] Parsed - filehash : {}".format(filehash)
    except:
      ret_msg["msg"] = "Wrong Command..."
      ret_msg["type"] = "Error"
      connObj.send(json.dumps(ret_msg))
      continue
    mutex.acquire()
    for i in EVENT_LIST:
      ListedFile = i[0].split('/')[-1]
      if Debug:
        print "[~] Comparing.. {} - {}".format(filename, ListedFile)
      if filename in ListedFile:
        if ext and "{}.{}".format(filename,ext) == ListedFile:
          ret_msg["msg"] = "Exactly Matched"
          ret_msg["type"] = "Exist"
          ret_msg["path"] = i[0]
          ret_msg["hash"] = filehash
          EVENT_LIST.remove(i)
          break
        elif not ext:
          ret_msg["msg"] = "Exactly Matched"
          ret_msg["type"] = "Exist"
          ret_msg["path"] = i[0]
          ret_msg["hash"] = filehash
          EVENT_LIST.remove(i)
          break
      if Debug:
        print "[~] Comparing.. {} - {}".format(i[1], filehash)
      if i[1] == filehash:
        ret_msg["msg"] = "Exactly Matched"
        ret_msg["type"] = "Exist"
        ret_msg["path"] = i[0]
        ret_msg["hash"] = filehash
        EVENT_LIST.remove(i)
        break
    if Debug:
      if len(ret_msg.keys())!=0:
        print "[~] Result : {} - {}".format(filename,ret_msg["msg"])
      else:
        print "[~] Result : {} - Fail".format(filename)

    mutex.release()
    if len(ret_msg.keys()) == 0:
      ret_msg["msg"] = "Fail to find file"
      ret_msg["type"] = "Fail"
    else:
      if not os.path.isfile(ret_msg["path"]):
        ret_msg = {}
        ret_msg["msg"] = "Fail to find file"
        ret_msg["type"] = "Fail"
    print ret_msg
    connObj.send(json.dumps(ret_msg))

if __name__ == '__main__':
  # 1. run monitor thread
  print "Start Event Monitor Thread"
  t = threading.Thread(target = eventMonitor,args=(MONITOR_PATH,))
  t.daemon = True
  t.start()

  # 2. connect with client
  while True:
    print "Connection with client"
    connObj = EventCommunicator('0.0.0.0',MONITOR_PORT)
    connObj.connWait()
    tc = threading.Thread(target=connectionThread, args=(connObj,))
    tc.start()
    tc.join()

