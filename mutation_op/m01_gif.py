from mutation_op import *
import utils

class mOP(MutationOP):
  __comment__ = "Mutation1 : set 1024byte from gif resource file in front of seed"
  __mutate_type__ = "file"  # (file|request) ; type of target
  __exclusion_op__ = {'php':['M09','M01_GIF', 'M01_JPG', 'M01_PDF', 'M01_PNG', 'M01_TAR_GZ', 'M01_ZIP', 'M02_GIF', 'M02_JPG', 'M02_JSBMP', 'M02_JSGIF', 'M02_PDF', 'M02_PNG', 'M02_ZIP'], 'html':['M01_GIF', 'M01_JPG', 'M01_PDF', 'M01_PNG', 'M01_TAR_GZ', 'M01_ZIP','M02_GIF', 'M02_JPG', 'M02_JSBMP', 'M02_JSGIF', 'M02_PDF', 'M02_PNG', 'M02_ZIP','M04_ACE','M04_ARC','M04_ARJ','M04_BZ2','M04_DFXP','M04_EPUB','M04_GPX','M04_GZIP','M04_M4V','M04_MPA','M04_MPP','M04_NUMBERS','M04_ONETOC','M04_OXPS','M04_PAGES','M04_WP','M04_WRI','M04_XHT','M04_XLA','M04_XLW','M04_XPS','M04_ZIPX','M06','M07','M08','M09','M10']}
#['M01_JPG', 'M01_PNG', 'M01_ZIP', 'M01_TAR_GZ', 'M01_PDF', 'M02_PNG', 'M02_JPG', 'M02_GIF', 'M02_ZIP', 'M02_PDF', 'M02_JSBMP', 'M02_JSGIF', 'M06', 'M07_OTHER', 'M08','M10'] # ([classname])when this op used for mutation,
                        # operations in this list can be used to extra mutation.
  __resource__ = {"gif":"resource/test.gif"} # ({type:resource filename})
  __seed_dependency__ = __exclusion_op__.keys()#["php","html"] # seed file dependency for operation
  def operation(self, output, seed_file, resource_file=None):
    if resource_file == None:
      resource_file = self.__resource__["gif"]
    if output['filename'] != None and len(output['filename']) > 0:
      filename = output['filename']
    else:
      filename = utils.extract_filename(seed_file)
    output['filename'] = filename + '_M1GIF'
    output['content'] = utils.extract_content(resource_file)[:1024] + \
            output['content']

      #test
      #f = open('file.bin', 'wb')
      #f.write(output['content'])
      #f.close()
