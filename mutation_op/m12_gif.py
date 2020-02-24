from mutation_op import *
import utils

class mOP(MutationOP):
  __comment__ = "Mutation12: Double extension"
  __mutate_type__ = "file"  # (file|request) ; type of target
  __exclusion_op__ = {'php':['M04_GIF','M07', 'M10', 'M12_ACE', 'M12_ARC', 'M12_ARJ', 'M12_BZ2', 'M12_DFXP', 'M12_EPUB', 'M12_GIF', 'M12_GPX', 'M12_GZIP', 'M12_JPG', 'M12_M4V', 'M12_MPA', 'M12_MPP', 'M12_NUMBERS', 'M12_ONETOC', 'M12_OXPS', 'M12_PAGES', 'M12_PDF', 'M12_PNG', 'M12_TAR_GZ', 'M12_TXT', 'M12_WP', 'M12_WRI', 'M12_XHT', 'M12_XLA', 'M12_XLW', 'M12_XPS', 'M12_ZIP', 'M12_HTML','M12_XHTML','M12_ZIPX'], 'js':['M04_GIF','M04_ACE','M04_ARC','M04_ARJ','M04_DFXP','M04_EPUB','M04_GIF','M04_GPX','M04_GZIP','M04_JPG','M04_M4V','M04_MPA','M04_MPP','M04_NUMBERS','M04_ONETOC','M04_OXPS','M04_PAGES','M04_PNG','M04_WP','M04_WRI','M04_XLA','M04_XLW','M04_XPS','M04_ZIPX','M7','M12_ACE', 'M12_ARC', 'M12_ARJ', 'M12_BZ2', 'M12_DFXP', 'M12_EPUB', 'M12_GIF', 'M12_GPX', 'M12_GZIP', 'M12_JPG', 'M12_M4V', 'M12_MPA', 'M12_MPP', 'M12_NUMBERS', 'M12_ONETOC', 'M12_OXPS', 'M12_PAGES', 'M12_PDF', 'M12_PNG', 'M12_TAR_GZ', 'M12_TXT', 'M12_WP', 'M12_WRI', 'M12_XHT', 'M12_XLA', 'M12_XLW', 'M12_XPS', 'M12_ZIP', 'M12_HTML','M12_XHTML','M12_ZIPX'], 'html':['M04_ACE', 'M04_ARC', 'M04_ARJ', 'M04_BZ2', 'M04_DFXP', 'M04_EPUB', 'M04_GIF', 'M04_GPX', 'M04_GZIP', 'M04_JPG', 'M04_M4V', 'M04_MPA', 'M04_MPP', 'M04_NUMBERS', 'M04_ONETOC', 'M04_OXPS', 'M04_PAGES', 'M04_PDF', 'M04_PHAR', 'M04_PHP3', 'M04_PHP4', 'M04_PHP5', 'M04_PHP7', 'M04_PHTML', 'M04_PHT', 'M04_PNG', 'M04_TAR_GZ', 'M04_TXT', 'M04_WP', 'M04_WRI', 'M04_XHT', 'M04_XLA', 'M04_XLW', 'M04_XPS', 'M04_ZIP', 'M04_ZIPX', 'M06', 'M10', 'M07', 'M12_ACE', 'M12_ARC', 'M12_ARJ', 'M12_BZ2', 'M12_DFXP', 'M12_EPUB', 'M12_GIF', 'M12_GPX', 'M12_GZIP', 'M12_JPG', 'M12_M4V', 'M12_MPA', 'M12_MPP', 'M12_NUMBERS', 'M12_ONETOC', 'M12_OXPS', 'M12_PAGES', 'M12_PDF', 'M12_PNG', 'M12_TAR_GZ', 'M12_TXT', 'M12_WP', 'M12_WRI', 'M12_XHT', 'M12_XLA', 'M12_XLW', 'M12_XPS', 'M12_ZIP', 'M12_HTML','M12_XHTML','M12_ZIPX'],'xhtml':['M04_ACE', 'M04_ARC', 'M04_ARJ', 'M04_BZ2', 'M04_DFXP', 'M04_EPUB', 'M04_GIF', 'M04_GPX', 'M04_GZIP', 'M04_JPG', 'M04_M4V', 'M04_MPA', 'M04_MPP', 'M04_NUMBERS', 'M04_ONETOC', 'M04_OXPS', 'M04_PAGES', 'M04_PDF', 'M04_PHAR', 'M04_PHP3', 'M04_PHP4', 'M04_PHP5', 'M04_PHP7', 'M04_PHTML', 'M04_PHT', 'M04_PNG', 'M04_TAR_GZ', 'M04_TXT', 'M04_WP', 'M04_WRI', 'M04_XHT', 'M04_XLA', 'M04_XLW', 'M04_XPS', 'M04_ZIP', 'M04_ZIPX', 'M06', 'M10', 'M07', 'M12_ACE', 'M12_ARC', 'M12_ARJ', 'M12_BZ2', 'M12_DFXP', 'M12_EPUB', 'M12_GIF', 'M12_GPX', 'M12_GZIP', 'M12_JPG', 'M12_M4V', 'M12_MPA', 'M12_MPP', 'M12_NUMBERS', 'M12_ONETOC', 'M12_OXPS', 'M12_PAGES', 'M12_PDF', 'M12_PNG', 'M12_TAR_GZ', 'M12_TXT', 'M12_WP', 'M12_WRI', 'M12_XHT', 'M12_XLA', 'M12_XLW', 'M12_XPS', 'M12_ZIP', 'M12_HTML','M12_XHTML','M12_ZIPX','M08']}#['M12_JPG',          'M12_TXT','M12_PNG','M12_PDF','M12_ZIP','M12_TAR_GZ', 'M10', 'M07_PHP', 'M07_OTHER', 'M04_JPG', 'M04_PNG', 'M04_GIF', 'M04_ZIP', 'M04_TAR_GZ', 'M04_PDF', 'M04_PHP3', 'M04_PHP4', 'M04_PHP5', 'M04_PHP7', 'M04_PHAR', 'M04_PHT', 'M04_PHTML', 'M04_TXT'] # ([classname])when this op used for mutation,
                        # operations in this list can be used to extra mutation.
  __resource__ = {} # ({type:resource filename})
  __seed_dependency__ = __exclusion_op__.keys()#["html","js","php"] # seed file dependency for operation

  def operation(self, output, seed_file, resource_file=None):
      if output['filename'] != None and len(output['filename']) > 0:
        filename = output['filename']
      else:
        filename = utils.extract_filename(seed_file)

      output['filename'] = filename + '_M12GIF'

      output['fileext'] = 'gif.'+output['fileext']
