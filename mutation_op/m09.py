from mutation_op import *
import utils

class mOP(MutationOP):
  __comment__ = "Mutation09 : Prepending HTML Dummy Comment"
  __mutate_type__ = "request"  # (file|request) ; type of target
  __exclusion_op__ = {'php':['M09'], 'html':['M01_GIF', 'M01_JPG', 'M01_PDF', 'M01_PNG', 'M01_TAR_GZ', 'M01_ZIP', 'M02_GIF', 'M02_JPG', 'M02_JSBMP', 'M02_JSGIF', 'M02_PDF', 'M02_PNG', 'M02_ZIP', 'M06', 'M09','M04_BZ2','M04_XHT'], 'xhtml':['M06', 'M09','M04_BZ2']}#['M10', 'M07_PHP', 'M07_OTHER', 'M04_JPG', 'M04_PNG', 'M04_GIF', 'M04_ZIP', 'M04_TAR_GZ', 'M04_PDF', 'M04_PHP3', 'M04_PHP4', 'M04_PHP5', 'M04_PHP7', 'M04_PHAR', 'M04_PHT', 'M04_PHTML'] # ([classname])when this op used for mutation,
                        # operations in this list can be used to extra mutation.
  __resource__ = {} # ({type:resource filename})
  __seed_dependency__ = __exclusion_op__.keys()#["html"] # seed file dependency for operation

  def operation(self, output, seed_file, resource_file=None):
      if output['filename'] != None and len(output['filename']) > 0:
        filename = output['filename']
      else:
        filename = utils.extract_filename(seed_file)
      dummy = "<!--"+"a"*4096+"-->"
      output['content'] = dummy + output['content']
      output['filename'] = filename + '_M9'
