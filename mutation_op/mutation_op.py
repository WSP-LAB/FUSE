from abc import *

class MutationOP:

  __metaclass__ = ABCMeta

  # Attribute for each operations
  __comment__ = "Base Class"
  __mutate_type__ = ""  # (file|request) ; type of target
  __exclusion_op__ = {} # ({type:[classname]})when this op used for mutation,
                        # operations in this list can be used to extra mutation.
  __resource__ = {"":""} # ({type:resource filename})
  __seed_dependency__ = [] # ([filetype]) ; seed file dependency for operation


  # Maybe, we need to chage seed_file to request later
#  def __init__(self):
#    self.output = output

  @abstractmethod
  def operation(self):
    pass
