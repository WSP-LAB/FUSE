#!/usr/bin/env python
import os
import re
import utils

class mutate_manager:
  __op_path__ = './mutation_op/'
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

  def mutation_op_list(self):
    dir_list = os.listdir(self.__op_path__)
    mutation_list = []
    for i in dir_list:
      if ".py" not in i or ".pyc" in i or "__init__" in i or "mutation" in i:
        pass
      else:
        mutation_list.append(i.upper().rsplit('.',1)[0])
    mutation_list.sort()
    return mutation_list

  def mutation_chain(self, base_chain, seed_type, success_list):
    mutation_list = self.mutation_op_list()
    if '+' in base_chain:
      last_op_idx = mutation_list.index(base_chain.rsplit('+',1)[-1])+1
      base_chain = base_chain.split('+')
    elif len(base_chain)<=0:
      last_op_idx = 0
      base_chain = []
    else:
      last_op_idx = mutation_list.index(base_chain)+1
      base_chain = [base_chain]

    op_range = mutation_list[last_op_idx:]
    ret = []
    base_chain_import = {}
    op_range_import = {}
    for i in base_chain:
      base_chain_import[i] = self.importor(i)
    for i in op_range:
      op_range_import[i] = self.importor(i)
    for i in op_range:
      excludedflag = True

      if seed_type not in op_range_import[i].mOP.__seed_dependency__:
        excludedflag = False
      else:
        for ele in base_chain_import.keys():
          if seed_type not in base_chain_import[ele].mOP.__exclusion_op__.keys():
            excludedflag = False
            break
          elif i in base_chain_import[ele].mOP.__exclusion_op__[seed_type]:
            excludedflag = False
            break
      if excludedflag:
        input_mutation = ('+'.join(base_chain)+"+{}".format(i))
        if input_mutation[0] == "+":
          ret.append(input_mutation[1:])
        else:
          ret.append(input_mutation)
    filtered_ret = []
    for i in ret:
      banflag = False
      for ban in success_list:
        if type(ban) == str and ban in i:
          banflag = True
          break
        elif type(ban) == list:
          hitcount = 0
          for ban_ele in ban:
            if ban_ele in i:
              hitcount += 1
          if hitcount == len(ban):
            banflag = True
            break
      if not banflag:
        filtered_ret.append(i)
    return filtered_ret


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
        for banop in self.op_dict[aop[0]].mOP.__exclusion_op__[seedtype]: #List(List
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
    return oplist

  def makeMutatedData(self, mutate_list, seed_file, resource_file):
      output = {
          'filename': utils.extract_filename(seed_file),
          'fileext': utils.extract_fileext(seed_file),
          'filetype': utils.extract_filetype(seed_file),
          'content': utils.extract_content(seed_file)
      }


      # insert specific data for hash
      output['content'] = output['content'].replace("%unique#",os.urandom(8).encode('hex'))


      for mutation in mutate_list:
          mutator = self.op_dict[mutation].mOP()
          mutator.operation(output, seed_file,resource_file)
       # XXX: Finally, use output variable to make request

      return output

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
  OpList = test.combinatedOpList()

  seed_files = os.listdir('seed')
  resource_files = os.listdir('resource')

  seed_files = ['seed/' + x for x in seed_files]
  resource_files = ['resource/' + x for x in resource_files]

  count = 0
  for key in OpList.keys():
    type_seed_files = get_type_seed_files(key, seed_files)
    print "{} - {}".format(key,len(OpList[key]))
