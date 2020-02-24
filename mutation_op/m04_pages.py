from mutation_op import *
import utils

class mOP(MutationOP):
  __comment__ = "Mutation4: Change Extensions to Mutation Resource File"
  __mutate_type__ = "file"  # (file|request) ; type of target
  __exclusion_op__ = {'php':['M12_HTML','M12_XHTML','M12_PAGES','M04_ACE', 'M04_ARC', 'M04_ARJ', 'M04_BZ2', 'M04_DFXP', 'M04_EPUB', 'M04_GIF', 'M04_GPX', 'M04_GZIP', 'M04_JPG', 'M04_M4V', 'M04_MPA', 'M04_MPP', 'M04_NUMBERS', 'M04_ONETOC', 'M04_OXPS', 'M04_PAGES', 'M04_PDF', 'M04_PHAR', 'M04_PHP3', 'M04_PHP4', 'M04_PHP5', 'M04_PHP7', 'M04_PHTML', 'M04_PHT', 'M04_PNG', 'M04_TAR_GZ', 'M04_TXT', 'M04_WP', 'M04_WRI', 'M04_XHT', 'M04_XLA', 'M04_XLW', 'M04_XPS', 'M04_ZIP', 'M04_ZIPX','M07','M10'],'html':['M12_PAGES','M04_ACE', 'M04_ARC', 'M04_ARJ', 'M04_BZ2', 'M04_DFXP', 'M04_EPUB', 'M04_GIF', 'M04_GPX', 'M04_GZIP', 'M04_JPG', 'M04_M4V', 'M04_MPA', 'M04_MPP', 'M04_NUMBERS', 'M04_ONETOC', 'M04_OXPS', 'M04_PAGES', 'M04_PDF', 'M04_PHAR', 'M04_PHP3', 'M04_PHP4', 'M04_PHP5', 'M04_PHP7', 'M04_PHTML', 'M04_PHT', 'M04_PNG', 'M04_TAR_GZ', 'M04_TXT', 'M04_WP', 'M04_WRI', 'M04_XHT', 'M04_XLA', 'M04_XLW', 'M04_XPS', 'M04_ZIP', 'M04_ZIPX','M06','M07','M08','M10','M12_BZ2', 'M12_BZ2', 'M12_GIF', 'M12_JPG', 'M12_PDF', 'M12_PNG', 'M12_TAR_GZ', 'M12_TXT', 'M12_ZIP', 'M12_XHT'],'xhtml':['M12_PAGES','M04_ACE', 'M04_ARC', 'M04_ARJ', 'M04_BZ2', 'M04_DFXP', 'M04_EPUB', 'M04_GIF', 'M04_GPX', 'M04_GZIP', 'M04_JPG', 'M04_M4V', 'M04_MPA', 'M04_MPP', 'M04_NUMBERS', 'M04_ONETOC', 'M04_OXPS', 'M04_PAGES', 'M04_PDF', 'M04_PHAR', 'M04_PHP3', 'M04_PHP4', 'M04_PHP5', 'M04_PHP7', 'M04_PHTML', 'M04_PHT', 'M04_PNG', 'M04_TAR_GZ', 'M04_TXT', 'M04_WP', 'M04_WRI', 'M04_XHT', 'M04_XLA', 'M04_XLW', 'M04_XPS', 'M04_ZIP', 'M04_ZIPX','M06','M07','M08','M10','M12_BZ2', 'M12_BZ2', 'M12_GIF', 'M12_JPG', 'M12_PDF', 'M12_PNG', 'M12_TAR_GZ', 'M12_TXT', 'M12_ZIP'],'js':['M12_HTML','M12_XHTML','M12_PAGES','M10','M07','M04_ACE', 'M04_ARC', 'M04_ARJ', 'M04_BZ2', 'M04_DFXP', 'M04_EPUB', 'M04_GIF', 'M04_GPX', 'M04_GZIP', 'M04_JPG', 'M04_M4V', 'M04_MPA', 'M04_MPP', 'M04_NUMBERS', 'M04_ONETOC', 'M04_OXPS', 'M04_PAGES', 'M04_PDF', 'M04_PHAR', 'M04_PHP3', 'M04_PHP4', 'M04_PHP5', 'M04_PHP7', 'M04_PHTML', 'M04_PHT', 'M04_PNG', 'M04_TAR_GZ', 'M04_TXT', 'M04_WP', 'M04_WRI', 'M04_XHT', 'M04_XLA', 'M04_XLW', 'M04_XPS', 'M04_ZIP', 'M04_ZIPX', 'M12_JPG', 'M12_GIF', 'M12_PNG']}#['M04_JPG', 'M04_GIF', 'M04_ZIP', 'M04_TAR_GZ', 'M04_PDF', 'M04_PHP3', 'M04_PHP4', 'M04_PHP5', 'M04_PHP7', 'M04_PHAR', 'M04_PHT', 'M04_PHTML', 'M04_PNG', 'M04_TXT', 'M07_PHP', 'M07_OTHER', 'M10'] # ([classname])when this op used for mutation,
                        # operations in this list can be used to extra mutation.
  __resource__ = {} # ({type:resource filename})
  __seed_dependency__ = __exclusion_op__.keys()#["html"] # seed file dependency for operation

  def operation(self, output, seed_file, resource_file=None):
      if output['filename'] != None and len(output['filename']) > 0:
        filename = output['filename']
      else:
        filename = utils.extract_filename(seed_file)

      output['filename'] = filename + '_M4PAGES'
      output['fileext'] = 'pages'
