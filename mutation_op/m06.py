from mutation_op import *
import utils

class mOP(MutationOP):
  __comment__ = "Mutation 6: Apply form EML"
  __mutate_type__ = "file"  # (file|request) ; type of target

  # XXX: Fill the exclusion operator and seed dependency
  __exclusion_op__ = {'html':['M01_GIF', 'M01_JPG', 'M01_PDF', 'M01_PNG', 'M01_TAR_GZ', 'M01_ZIP', 'M02_GIF', 'M02_JPG', 'M02_JSBMP', 'M02_JSGIF', 'M02_PDF', 'M02_PNG', 'M02_ZIP', 'M04_ACE', 'M04_ARC', 'M04_ARJ', 'M04_BZ2', 'M04_DFXP', 'M04_EPUB', 'M04_GIF', 'M04_GPX', 'M04_GZIP', 'M04_JPG', 'M04_M4V', 'M04_MPA', 'M04_MPP', 'M04_NUMBERS', 'M04_ONETOC', 'M04_OXPS', 'M04_PAGES', 'M04_PDF', 'M04_PHAR', 'M04_PHP3', 'M04_PHP4', 'M04_PHP5', 'M04_PHP7', 'M04_PHTML', 'M04_PHT', 'M04_PNG', 'M04_TAR_GZ', 'M04_TXT', 'M04_WP', 'M04_WRI', 'M04_XHT', 'M04_XLA', 'M04_XLW', 'M04_XPS', 'M04_ZIP', 'M04_ZIPX', 'M06' ,'M07', 'M08', 'M09', 'M10'], 'xhtml':['M04_ACE', 'M04_ARC', 'M04_ARJ', 'M04_BZ2', 'M04_DFXP', 'M04_EPUB', 'M04_GIF', 'M04_GPX', 'M04_GZIP', 'M04_JPG', 'M04_M4V', 'M04_MPA', 'M04_MPP', 'M04_NUMBERS', 'M04_ONETOC', 'M04_OXPS', 'M04_PAGES', 'M04_PDF', 'M04_PHAR', 'M04_PHP3', 'M04_PHP4', 'M04_PHP5', 'M04_PHP7', 'M04_PHTML', 'M04_PHT', 'M04_PNG', 'M04_TAR_GZ', 'M04_TXT', 'M04_WP', 'M04_WRI', 'M04_XHT', 'M04_XLA', 'M04_XLW', 'M04_XPS', 'M04_ZIP', 'M04_ZIPX', 'M06' ,'M07', 'M08', 'M09', 'M10']}#['M01_JPG', 'M01_PNG', 'M01_GIF', 'M01_ZIP', 'M01_TAR_GZ', 'M01_PDF', 'M02_PNG', 'M02_JPG', 'M02_GIF', 'M02_ZIP', 'M02_PDF', 'M08','M04_JPG', 'M04_PNG', 'M04_GIF', 'M04_ZIP', 'M04_TAR_GZ', 'M04_PDF', 'M04_PHP3', 'M04_PHP4', 'M04_PHP7', 'M04_PHAR', 'M04_PHT', 'M04_PHTML', 'M04_TXT', 'M07_OTHER', 'M10', 'M04_PHP5'] # ([classname])when this op used for mutation,
                        # operations in this list can be used to extra mutation.
  __resource__ = {""} # ({type:resource filename})
  __seed_dependency__ = __exclusion_op__.keys()#['html'] # seed file dependency for operation

  def operation(self, output, seed_file, resource_file=None):
    base_data='''TESTEML
Content-Type: text/html
Content-Transfer-Encoding: quoted-printable

'''
    normalstr = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01234567890 \n\t'
    emlenc = lambda x: '='+hex(ord(x))[2:]
    data = ''
    for i in output['content']:
      if i not in normalstr:
        data +=emlenc(i)
      else:
        data += i
    output['content'] = base_data+data
    if output['filename'] != None and len(output['filename']) > 0:
      filename = output['filename']
    else:
      filename = utils.extract_filename(seed_file)
    #print output['content']
    output['filename'] = filename + '_M6'
    output['fileext'] = 'eml'
