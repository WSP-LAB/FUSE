import mimetypes
import datetime
import hashlib

def print_mutate_information(mutate_list, seed_file, resource_file):
  print '[*] Mutation Information'
  print '[*] mutate_list:', mutate_list
  print '[*] seed_file:', seed_file
  print '[*] resource_file', resource_file
  print '\n'

def extract_content(path):
  with open(path, "rb") as f:
    content = f.read()
  return content

def extract_fileext(path):
  return path.split('.')[-1]

def extract_filename(path):
#  return path.split('/')[-1].split('.')[0]
  return hashlib.md5(datetime.datetime.now().__str__()).hexdigest()

def extract_filetype(path):
  return mimetypes.guess_type(path)[0] or 'application/octet-stream'

def getMD5hash(binary):
  return hashlib.md5(binary).hexdigest() 
