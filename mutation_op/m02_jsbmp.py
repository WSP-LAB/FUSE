from mutation_op import *
import struct

class mOP(MutationOP):
  __comment__ = "Mutation2 : set seed in resource file as metadata"
  __mutate_type__ = "file"  # (file|request) ; type of target
  __exclusion_op__ = {'js':['M02_GIF', 'M02_JPG', 'M02_JSBMP', 'M02_JSGIF', 'M02_PDF', 'M02_PNG', 'M02_ZIP','M04_GIF','M04_JPG','M04_PNG']}#['M01_JPG', 'M01_PNG', 'M01_GIF', 'M01_ZIP', 'M01_TAR_GZ', 'M01_PDF', 'M02_JPG', 'M02_PNG', 'M02_GIF', 'M02_ZIP', 'M02_PDF', 'M02_JSGIF', 'M06', 'M08','M10'] # ([classname])when this op used for mutation,
                        # operations in this list can be used to extra mutation.
  __resource__ = {} # ({type:resource filename})
  __seed_dependency__ = __exclusion_op__.keys()#["js"] # seed file dependency for operation


  def operation(self, output, seed_file, resource_file=None):
    with open('./resource/test.bmp') as fp:
      data = fp.read()

    data = data.replace(b'\x2A\x2F',b'\x00\x00')

    output['content'] = data[0:2]+b'\x2F\x2A'+data[4:]+b'\xFF\x2A\x2F\x3D\x31\x3B'+output['content']

    """
    with open('new.bmp','wb') as fp:
      fp.write(output['content'])
    """
    if output['filename'] != None and len(output['filename']) > 0:
      filename = output['filename']
    else:
      filename = utils.extract_filename(seed_file)
    output['filename'] = filename + '_M2JSBMP'

#============================================================================================================#
#======= Script Referenced from : https://pastebin.com/04y7ee3u =============================================#
#============================================================================================================#
# Basic Principals : make header file size with \x2f\x2a\x00\x00 ( it is same with /* ) and append end of mutated bmp */=1;
# In javascript, it same with BM/* blah blah */=1;, so it has not error in javascript syntax. Also, It has bmp structure.
