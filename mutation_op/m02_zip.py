from mutation_op import *
import struct

class mOP(MutationOP):
  __comment__ = "Mutation2 : set seed in resource file as metadata"
  __mutate_type__ = "file"  # (file|request) ; type of target
  __exclusion_op__ = {'php':['M09','M01_GIF', 'M01_JPG', 'M01_PDF', 'M01_PNG', 'M01_TAR_GZ', 'M01_ZIP', 'M02_GIF', 'M02_JPG', 'M02_JSBMP', 'M02_JSGIF', 'M02_PDF', 'M02_PNG', 'M02_ZIP'], 'html':['M01_GIF', 'M01_JPG', 'M01_PDF', 'M01_PNG', 'M01_TAR_GZ', 'M01_ZIP','M02_GIF', 'M02_JPG', 'M02_JSBMP', 'M02_JSGIF', 'M02_PDF', 'M02_PNG', 'M02_ZIP','M04_ACE','M04_ARC','M04_ARJ','M04_BZ2','M04_DFXP','M04_EPUB','M04_GPX','M04_GZIP','M04_M4V','M04_MPA','M04_MPP','M04_NUMBERS','M04_ONETOC','M04_OXPS','M04_PAGES','M04_WP','M04_WRI','M04_XHT','M04_XLA','M04_XLW','M04_XPS','M04_ZIPX','M06','M07','M08','M09','M10']}#['M01_JPG', 'M01_PNG', 'M01_GIF', 'M01_ZIP', 'M01_TAR_GZ', 'M01_PDF', 'M02_PNG', 'M02_JPG', 'M02_GIF', 'M02_PDF', 'M02_JSBMP', 'M02_JSGIF', 'M06', 'M08', 'M07_OTHER', 'M10'] # ([classname])when this op used for mutation,
                        # operations in this list can be used to extra mutation.
  __resource__ = {"jpg":""} # ({type:resource filename})
  __seed_dependency__ = __exclusion_op__.keys()#["php","html"] # seed file dependency for operation

  def operation(self, output, seed_file, resource_file=None):
    DIRENTRY_SIGN = b'\x50\x4b\x01\x02'
    with open('./resource/test.zip','rb') as fp:
      data = fp.read()

    direntry_root = data.index(DIRENTRY_SIGN)
    COMMENT_LEN = struct.pack('<H',len(output['content']))
    injectpoint = direntry_root+46+struct.unpack('<H',data[direntry_root+28:direntry_root+30])[0]+struct.unpack('<H',data[direntry_root+30:direntry_root+32])[0]

    output['content'] = data[:direntry_root+32]+COMMENT_LEN+data[direntry_root+34:injectpoint]+output['content']+data[injectpoint:]
    """
    with open('new.zip','wb') as fp:
      fp.write(output['content'])
    """
    if output['filename'] != None and len(output['filename']) > 0:
      filename = output['filename']
    else:
      filename = utils.extract_filename(seed_file)
    output['filename'] = filename + '_M2ZIP'
