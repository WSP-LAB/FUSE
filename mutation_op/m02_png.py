from mutation_op import *
import struct
import zlib

class mOP(MutationOP):
  __comment__ = "Mutation2 : set seed in resource file as metadata"
  __mutate_type__ = "file"  # (file|request) ; type of target
  __exclusion_op__ = {'php':['M09','M01_GIF', 'M01_JPG', 'M01_PDF', 'M01_PNG', 'M01_TAR_GZ', 'M01_ZIP', 'M02_GIF', 'M02_JPG', 'M02_JSBMP', 'M02_JSGIF', 'M02_PDF', 'M02_PNG', 'M02_ZIP'], 'html':['M01_GIF', 'M01_JPG', 'M01_PDF', 'M01_PNG', 'M01_TAR_GZ', 'M01_ZIP','M02_GIF', 'M02_JPG', 'M02_JSBMP', 'M02_JSGIF', 'M02_PDF', 'M02_PNG', 'M02_ZIP','M04_ACE','M04_ARC','M04_ARJ','M04_BZ2','M04_DFXP','M04_EPUB','M04_GPX','M04_GZIP','M04_M4V','M04_MPA','M04_MPP','M04_NUMBERS','M04_ONETOC','M04_OXPS','M04_PAGES','M04_WP','M04_WRI','M04_XHT','M04_XLA','M04_XLW','M04_XPS','M04_ZIPX','M06','M07','M08','M09','M10']}#['M01_JPG', 'M01_PNG', 'M01_GIF', 'M01_ZIP', 'M01_TAR_GZ', 'M01_PDF', 'M02_JPG', 'M02_GIF', 'M02_ZIP', 'M02_PDF', 'M02_JSBMP', 'M02_JSGIF', 'M06', 'M08', 'M10', 'M07_OTHER'] # ([classname])when this op used for mutation,
                        # operations in this list can be used to extra mutation.
  __resource__ = {"jpg":""} # ({type:resource filename})
  __seed_dependency__ = __exclusion_op__.keys()#["php","html"] # seed file dependency for operation

  def operation(self, output, seed_file, resource_file=None):
    textChunk = [struct.pack('>I',8+len(output['content'])),b'tEXt',b'Comment\x00',output['content']]
    textChunk.append(struct.pack('>I',zlib.crc32(b''.join(textChunk[1:]))&0xffffffff))
    with open('./resource/test.png','rb') as fp:
      data = fp.read()
    injectpoint = data.index('IEND')-4

    output['content'] = data[:injectpoint]+b''.join(textChunk)+data[injectpoint:]
    """
    with open('new.png','wb') as fp:
      print "test"
      fp.write(output['content'])
    """
    if output['filename'] != None and len(output['filename']) > 0:
      filename = output['filename']
    else:
      filename = utils.extract_filename(seed_file)
    output['filename'] = filename + '_M2PNG'
