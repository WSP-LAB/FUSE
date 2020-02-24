from mutation_op import *
import struct

class mOP(MutationOP):
  __comment__ = "Mutation2 : set seed in resource file as metadata"
  __mutate_type__ = "file"  # (file|request) ; type of target
  __exclusion_op__ = {'js':['M02_GIF', 'M02_JPG', 'M02_JSBMP', 'M02_JSGIF', 'M02_PDF', 'M02_PNG', 'M02_ZIP','M04_JPG','M04_PNG','M04_GIF']}#['M01_JPG', 'M01_PNG', 'M01_GIF', 'M01_ZIP', 'M01_TAR_GZ', 'M01_PDF', 'M02_JPG', 'M02_PNG', 'M02_GIF', 'M02_ZIP', 'M02_PDF', 'M02_JSBMP', 'M06', 'M08','M10'] # ([classname])when this op used for mutation,
                        # operations in this list can be used to extra mutation.
  __resource__ = {} # ({type:resource filename})
  __seed_dependency__ = __exclusion_op__.keys()#["js"] # seed file dependency for operation

  def operation(self, output, seed_file, resource_file=None):
    gifstructure = [b'\x47\x49\x46\x38\x39\x61', b'\x2F\x2A', b'\x0A\x00', b'\x00', b'\xFF', b'\x00', b'\x2C\x00\x00\x00\x00\x2F\x2A\x0A\x00\x00\x02\x00\x3B', b'\x2A\x2F', b'\x3D\x31\x3B']

    output['content'] = b''.join(gifstructure)+output['content']+b'\x3B'
    """
    with open('new.gif','wb') as fp:
      fp.write(output['content'])
    """
    if output['filename'] != None and len(output['filename']) > 0:
      filename = output['filename']
    else:
      filename = utils.extract_filename(seed_file)
    output['filename'] = filename + '_M2JSGIF'

#============================================================================================================#
#======= Script Referenced from : https://pastebin.com/6yUbfGX5 =============================================#
#============================================================================================================#

