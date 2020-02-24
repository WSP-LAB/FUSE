from mutation_op import *
import utils

class mOP(MutationOP):
  __comment__ = "Mutation11: Case Mutator"
  __mutate_type__ = "file"  # (file|request) ; type of target
  __exclusion_op__ = {'php':['M07','M10', 'M11'], 'html':['M07', 'M10', 'M11','M04_BZ2','M04_XHT','M12_HTML','M12_XHTML'], 'xhtml':['M07', 'M10', 'M08', 'M11', 'M04_BZ2'], 'js':['M10', 'M11','M04_GIF','M04_PNG', 'M04_JPG']}#['M10', 'M07_PHP', 'M07_OTHER', 'M04_JPG', 'M04_PNG', 'M04_GIF', 'M04_ZIP', 'M04_TAR_GZ', 'M04_PDF', 'M04_PHP3', 'M04_PHP4', 'M04_PHP5', 'M04_PHP7', 'M04_PHAR', 'M04_PHT', 'M04_PHTML'] # ([classname])when this op used for mutation,
                        # operations in this list can be used to extra mutation.
  __resource__ = {} # ({type:resource filename})
  __seed_dependency__ = __exclusion_op__.keys()#["html","js"] # seed file dependency for operation

  def operation(self, output, seed_file, resource_file=None):
      if output['filename'] != None and len(output['filename']) > 0:
        filename = output['filename']
      else:
        filename = utils.extract_filename(seed_file)

      output['filename'] = filename + '_M11'
      tmp = ""
      for i in range(0,len(output['fileext'])):
        if i == '.':
          pass
        elif i % 2 == 0:
          tmp += output['fileext'][i].upper()
        else:
          tmp += output['fileext'][i]

      output['fileext'] = tmp
