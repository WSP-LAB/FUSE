from mutation_op import *
import utils

class mOP(MutationOP):
  __comment__ = "Mutation3 : Change Contents-Type to JPG File"
  __mutate_type__ = "file"  # (file|request) ; type of target
  __exclusion_op__ = {'php':['M03_GIF', 'M03_JPG', 'M03_PDF', 'M03_PNG', 'M03_TAR_GZ', 'M03_ZIP'], 'html':['M03_GIF', 'M03_JPG', 'M03_PDF', 'M03_PNG', 'M03_TAR_GZ', 'M03_ZIP','M04_BZ2','M04_XHT'], 'xhtml':['M03_GIF', 'M03_JPG', 'M03_PDF', 'M03_PNG', 'M03_TAR_GZ', 'M03_ZIP','M04_BZ2'], 'js':['M03_GIF', 'M03_JPG', 'M03_PDF', 'M03_PNG', 'M03_TAR_GZ', 'M03_ZIP','M04_JPG','M04_PNG','M04_GIF']}# ['M03_PNG', 'M03_GIF', 'M03_ZIP', 'M03_TAR_GZ', 'M03_PDF'] # ([classname])when this op used for mutation,
                        # operations in this list can be used to extra mutation.
  __resource__ = {"jpg":"resource/test.jpg"} # ({type:resource filename})
  __seed_dependency__ = __exclusion_op__.keys()#["php","html","js"] # seed file dependency for operation

  def operation(self, output, seed_file, resource_file=None):
    if resource_file == None:
      resource_file = self.__resource__["jpg"]

    if output['filename'] != None and len(output['filename']) > 0:
      filename = output['filename']
    else:
      filename = utils.extract_filename(seed_file)
    output['filename'] = filename + '_M3JPG'
    output['filetype'] = utils.extract_filetype(resource_file)
