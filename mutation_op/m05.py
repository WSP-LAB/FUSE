from mutation_op import *
import utils

class mOP(MutationOP):
  __comment__ = "Mutation 5: Change PHP tag to short tag"
  __mutate_type__ = "file"  # (file|request) ; type of target

  # XXX: Fill the exclusion operator and seed dependency
  __exclusion_op__ = {'php':['M05']}# [] # ([classname])when this op used for mutation,
                        # operations in this list can be used to extra mutation.
  __resource__ = {} # ({type:resource filename})
  __seed_dependency__ = __exclusion_op__.keys()#self.__exclusion_op__.keys()#['php'] # seed file dependency for operation

  def operation(self, output, seed_file, resource_file=None):
      output['content'] = output['content'].replace('<?php', '<?')
      if output['filename'] != None and len(output['filename']) > 0:
        filename = output['filename']
      else:
        filename = utils.extract_filename(seed_file)
      output['filename'] = filename + '_M5'
