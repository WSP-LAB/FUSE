#!/usr/bin/env python
import os
import re
import utils

class mutate_manager:
  __op_path__ = './mutation_op/'#'./mutation_op/not_implemented/'
  extension = lambda x: x.rsplit('.',1)[1]
  __seedList__ = map(extension,os.listdir('./seed/'))
  importor = lambda self,x : __import__(self.__op_path__[2:-1]+'.'+x.lower(),fromlist=["{}.{}".format(x,x)])
  file2class = lambda self,x : (x.split('.',1)[0]).upper()
  op_dict = {}

  def __init__(self):
    op_dir = os.listdir(self.__op_path__)
    ops = []
    class_re = re.compile(r'm\d+.*[.]py$')
    for i in op_dir:
      # File name should always match with m[Number].py
      if class_re.match(i):
        ops.append(i)
    ops = list(set(map(self.file2class,ops)))
    for i in ops:
      self.op_dict[i] = self.importor(i)

  def combinatedOpList(self,seedtype=None):
    opList = {}
    if seedtype==None:
      for i in self.__seedList__:
        opList[i] = self.combinatedOpListFactory(i)
    elif seedtype in self.__seedList__:
      opList[seedtype] = self.combinatedOpListFactory(seedtype)
    else:
      print "[-] Given seed type is not exist in seed list"
      return None

    return opList

  def combinatedOpListFactory(self,seedtype):
    #eqmaker = lambda x : ('+'.join(x))
    available_op = []
    oplist = []

    # find available op
    for i in self.op_dict.keys():
      if seedtype in self.op_dict[i].mOP.__seed_dependency__ and i != "M0":
        available_op.append([i])

    oplist += available_op # 1R - same with oplist, available_op

    # make list, 2R~
    for aop in available_op: #List(List(Str)) -> List(Str)
      round_templist = []
      for opl in oplist:
        banflag = False
        for banop in self.op_dict[aop[0]].mOP.__exclusion_op__: #List(List
          if banop in opl:
            banflag = True
            break
        if not banflag and aop[0] not in opl:
          append_op = []
          append_op += aop
          append_op += opl
        else:
          continue
        round_templist.append(append_op)
      map(list.sort,round_templist)

      oplist += round_templist
      oplist = map(tuple,oplist)
      oplist = map(list,set(oplist))
    #oplist.insert(0,['M0'])
    return oplist


  def testMutatedData(self, mutation, seed_files):

      mutator = self.op_dict[mutation].mOP()
      seed_dep = mutator.__seed_dependency__[0]
      resource_file = None

      for i in seed_files:
        if "." + seed_dep in i:
          seed_file = i
          break

      output = {
          'filename': utils.extract_filename(seed_file),
          'fileext': utils.extract_fileext(seed_file),
          'filetype': utils.extract_filetype(seed_file),
          'content': utils.extract_content(seed_file)
      }

      origin = {
          'filename': utils.extract_filename(seed_file),
          'fileext': utils.extract_fileext(seed_file),
          'filetype': utils.extract_filetype(seed_file),
          'content': utils.extract_content(seed_file)
      }

      mutator.operation(output, seed_file, resource_file)

      seed_type = seed_file.split(".")[-1]
      write_content(seed_type, output)
      """
      if output['filename'] != origin['filename']:
        print "[+] Mutation succeed ( {} ) - filename".format(mutation)
        return True
      el
      """
      if output['fileext'] != origin['fileext']:
        print "[+] Mutation succeed ( {} ) - fileext( {} -> {} )".format(mutation,origin["fileext"], output["fileext"])
        return True
      elif output['filetype'] != origin['filetype']:
        print "[+] Mutation succeed ( {} ) - filetype( {} -> {} )".format(mutation,origin["filetype"], output["filetype"])
        return True
      elif output['content'] != origin['content']:
        print "[+] Mutation succeed ( {} ) - content( {} b -> {} b )".format(mutation,len(origin["content"]), len(output["content"]))
      elif output['filename'][0] == '.':
        print "[+] Mutation succeed ( {} ) - filename( {} -> {} )".format(mutation,origin["filename"], output["filename"])

        return True

      return False


def write_content(seed_type, output):
  if output['fileext'] == '':
    full_file_name = output['filename']
  else:
    full_file_name = "%s.%s" % (output['filename'], output['fileext'])

  if seed_type != "php":
    if not os.path.exists(seed_type):
      os.makedirs(seed_type)
    with open("%s/%s" % (seed_type, full_file_name), "w") as f:
        f.write(output['content'])

def get_type_seed_files(types, seed_files):
  type_seed_files = []
  for i in seed_files:
    # XXX: Maybe we can check file metadata, not use the file extension to
    # check their type?
    if "." + types in i:
      type_seed_files.append(i)
  return type_seed_files

# if you need to find full chain, use this code.
if __name__ == '__main__':
  test = mutate_manager()

  seed_files = os.listdir('./seed')
  resource_files = os.listdir('./resource')

  seed_files = ['./seed/' + x for x in seed_files]
  resource_files = ['./resource/' + x for x in resource_files]
  print seed_files
  test_op = test.op_dict.keys()
  test_op.sort()
  print test_op
  for i in test_op:
    test.testMutatedData(i,seed_files)
