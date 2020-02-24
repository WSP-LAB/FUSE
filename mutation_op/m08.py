from mutation_op import *
import utils

class mOP(MutationOP):
  __comment__ = "Mutation 8: Insert scripts in SVG file"
  __mutate_type__ = "file"  # (file|request) ; type of target

  # XXX: Fill the exclusion operator and seed dependency
  __exclusion_op__ = {'html':['M01_GIF', 'M01_JPG', 'M01_PDF', 'M01_PNG', 'M01_TAR_GZ', 'M01_ZIP', 'M02_GIF', 'M02_JPG', 'M02_JSBMP', 'M02_JSGIF', 'M02_PDF', 'M02_PNG', 'M02_ZIP', 'M04_ACE', 'M04_ARC', 'M04_ARJ', 'M04_BZ2', 'M04_DFXP', 'M04_EPUB', 'M04_GIF', 'M04_GPX', 'M04_GZIP', 'M04_JPG', 'M04_M4V', 'M04_MPA', 'M04_MPP', 'M04_NUMBERS', 'M04_ONETOC', 'M04_OXPS', 'M04_PAGES', 'M04_PDF', 'M04_PHAR', 'M04_PHP3', 'M04_PHP4', 'M04_PHP5', 'M04_PHP7', 'M04_PHTML', 'M04_PHT', 'M04_PNG', 'M04_TAR_GZ', 'M04_TXT', 'M04_WP', 'M04_WRI', 'M04_XHT', 'M04_XLA', 'M04_XLW', 'M04_XPS', 'M04_ZIP', 'M04_ZIPX', 'M06', 'M07', 'M08', 'M10']}
                        # operations in this list can be used to extra mutation.
  __resource__ = {""} # ({type:resource filename})
  __seed_dependency__ = __exclusion_op__.keys()#['html'] # seed file dependency for operation

  def operation(self, output, seed_file, resource_file=None):
    base_headdata = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 105">\n"""
    base_taildata = """\n  <g fill="#97C024" stroke="#97C024" stroke-linejoin="round" stroke-linecap="round">
    <path d="M14,40v24M81,40v24M38,68v24M57,68v24M28,42v31h39v-31z" stroke-width="12"/>
    <path d="M32,5l5,10M64,5l-6,10 " stroke-width="2"/>
  </g>
  <path d="M22,35h51v10h-51zM22,33c0-31,51-31,51,0" fill="#97C024"/>
  <g fill="#FFF">
    <circle cx="36" cy="22" r="2"/>
    <circle cx="59" cy="22" r="2"/>
  </g>
</svg>
"""
    output['content'] = base_headdata+output['content']+base_taildata
    #print output['content']
    if output['filename'] != None and len(output['filename']) > 0:
      filename = output['filename']
    else:
      filename = utils.extract_filename(seed_file)
    output['filename'] = filename + '_M8'
    output['fileext'] = 'svg'
