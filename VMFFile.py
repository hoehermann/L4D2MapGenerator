from VMFNode import VMFNode
import copy

class VMFFile:
  """The VMFFile class reads a VMF File
     The contents are stored in a hieracical tree built of VMFNode objects
     https://developer.valvesoftware.com/wiki/VMF_documentation"""
  def __init__(self):
    """Empty constructor"""
    self.root = None
  
  def fromfile(self,filename):
    """Reads a VMF file"""
    # TODO: make this a classmethod
    file = open(filename, "r")
    stack = []
    node = VMFNode(None) # root should be python list
    previousLine = None
    line = file.readline().strip()
    while line:
      if previousLine is not None:
        line = line.strip()
        if line == "{":
          stack.append(node)
          node = VMFNode(previousLine)
        elif line == "}":
          parentNode = stack.pop()
          parentNode.AddChild(node)
          node = parentNode
        elif line[0] == "\"": # TODO: better differentation of key-value pairs and node names
          split = line.split("\" \"")
          if len(split) == 2:
            node.AddProperty(split[0].strip("\""),split[1].strip("\""))
          else:
            print "WARNING: Unknown token number",len(split),"in",split
      previousLine = line
      line = file.readline()
    #print "Final depth:",len(stack)
    self.root = node
    return self
    
  def deepcopy(self):
    """Returns a deep copy of this object"""
    deepcopy = VMFFile()
    deepcopy.root = self.root.deepcopy()
    return deepcopy
