from mutation_op import *
import utils

class mOP(MutationOP):
  __comment__ = "Mutation13: Appending Signature"
  __mutate_type__ = "file"  # (file|request) ; type of target
  __exclusion_op__ = {'php':['M13'], 'html':['M04_BZ2','M13'], 'xhtml':['M13','M8'], 'js':['M13']}#['M10', 'M07_PHP', 'M07_OTHER', 'M04_JPG', 'M04_PNG', 'M04_GIF', 'M04_ZIP', 'M04_TAR_GZ', 'M04_PDF', 'M04_PHP3', 'M04_PHP4', 'M04_PHP5', 'M04_PHP7', 'M04_PHAR', 'M04_PHT', 'M04_PHTML'] # ([classname])when this op used for mutation,
                        # operations in this list can be used to extra mutation.
  __resource__ = {} # ({type:resource filename})
  __seed_dependency__ = __exclusion_op__.keys()#["html"] # seed file dependency for operation

  def operation(self, output, seed_file, resource_file=None):
      if output['filename'] != None and len(output['filename']) > 0:
        filename = output['filename']
      else:
        filename = utils.extract_filename(seed_file)

      with open('./resource/test.jpg','rb') as fp:
        data = fp.read(8)

      output['filename'] = filename + '_M13'
      if output['content'][-1] == '\x0a':
        output['content'] = output['content'][:-1]+data
      else:
        output['content'] += data

