import numpy
import copy

MAX_MATERIAL_SIZE = 1024

def indent(depth):
  """Returns a whitespace string simulating an intendation of depth depth"""
  out = ""
  for d in range(depth):
    out += "  "
  return out
  
def vectorToString(vector):
  """Returns the vector in a VMF compatible integer string format"""
  out = ""
  for element in vector:
    out += "%i " % element # TODO: should be %e for precision
  return out[:-1]
  
def getBounds(points):
  """Returns the bounding box around the given set of 3D points"""
  return numpy.array([numpy.min(points, axis=0),numpy.max(points, axis=0)])
  
def planeNormal(plane):
  """Returns the normal vector for the given plane specified by three 3D points"""
  normal = numpy.cross(plane[0]-plane[1],plane[2]-plane[0])  magnitude = numpy.max(numpy.absolute(normal))
  normal //= magnitude 
  # [0 -1 0] -> south, [0 1 0] -> north
  # redundant? is it in vaxis and uaxis?
  return normal
  
class VMFNode:  
  """The VMFNode yields data from a VMF file's content
     A node may be an entity, a plane, a solid, or a whole map
     https://developer.valvesoftware.com/wiki/VMF_documentation"""
     
  def __init__(self, name):
    """Constructor for an empty node"""
    self.name = name # structure in memory could be a dict tree (with names in dict keys)
    self.children = []
    self.properties = {}
    self.plane = None
    self.origin = None
    
  def deepcopy(self):
    """Returns a deep copy of this node"""
    deepcopy = VMFNode(self.name)
    deepcopy.properties = copy.deepcopy(self.properties)
    if self.plane is not None:
      deepcopy.plane = self.plane.copy()
    else:
      deepcopy.plane = None
    if self.origin is not None:
      deepcopy.origin = self.origin.copy()
    else:
      deepcopy.origin = None
    for child in self.children:
      deepcopy.AddChild(child.deepcopy())
    return deepcopy
    
  def AddChild(self,child):
    """Adds a child node to this node"""
    # TODO: rename to append, top level Node may be python list
    self.children.append(child)
    
  def AddProperty(self,key,value):
    """Adds or overwrites a property in this node"""
    if key == "plane":
      self.SetPlane(value)
    elif key == "origin":
      self.SetOrigin(value)
    else:
      self.properties[key] = value
      
  def translatePlane(self,vector):
    """Translates the plane property vectors along the given vector"""
    for index, corner in enumerate(self.plane):
      self.plane[index] = corner + vector
    
  def translateOrigin(self,vector):
    """Translates the origin property vector along the given vector.
       Also translates the BasisOrigin property vectors along the given vector (used by info_overlay entities)."""
    self.origin = self.origin + vector
    if "BasisOrigin" in self.properties:
      basisOrigin = numpy.int_(numpy.rint(numpy.fromstring(self.properties["BasisOrigin"], dtype=float, sep=' ')).reshape(3))
      basisOrigin = basisOrigin + vector
      self.properties["BasisOrigin"] = vectorToString(basisOrigin)
  
  def SetOrigin(self,origin):
    """Sets the node's origin property to the given string"""
    self.origin = numpy.int_(numpy.rint(numpy.fromstring(origin, dtype=float, sep=' ')).reshape(3))
    
  def GetOrigin(self):
    """Returns the node's origin property as a VMF compatible integer string"""
    return vectorToString(self.origin)
      
  def SetPlane(self,plane):
    """Sets the node's plane property to the given string"""
    plane = plane.translate({ord(c): None for c in "()"})
    self.plane = numpy.int_(numpy.rint(numpy.fromstring(plane, dtype=float, sep=' ')).reshape((3,3)))
    
  def GetPlane(self):
    """Returns the node's plane property as a VMF compatible integer list string"""
    out = ""
    for corner in self.plane:
      out += "(" + vectorToString(corner) + ") "
    return out[:-1]
  
  def shiftMaterial(self,axis,shift):
    """Shifts the material along an axis ("uaxis" or "vaxis") by the given distance.
       Should be the same as shifting in Hammer (material setting X or Y).
       The distance is modulo'd by MAX_MATERIAL_SIZE to prevent huge shifts (the material is repeated either way)."""
    split = self.properties[axis].split(" ")
    offset = int(float(split[3].strip("]")))
    factor = float(split[4])
    offset += (shift/factor)%MAX_MATERIAL_SIZE
    split[3] = str(offset)+"]"
    self.properties[axis] = " ".join(split)
  
  def TranslateMaterial(self,vector):
    """Translates the material on this node property"""
    # TODO: implement properly. currently poorly works for the Z shift only
    normal = planeNormal(self.plane)
    if normal[0] == 0 and normal[1] == 0:
      self.shiftMaterial("uaxis", vector[0])
      self.shiftMaterial("vaxis", vector[1])
    elif normal[0] == 0: #and normal[2] == 0
      self.shiftMaterial("vaxis", vector[2]) # shift Z
      self.shiftMaterial("uaxis", vector[0]) # shift Y
    elif normal[1] == 0: #and normal[2] == 0
      self.shiftMaterial("vaxis", vector[2]) # shift Z
      self.shiftMaterial("uaxis", vector[1]) # shift X
    else:
      if not self.properties["material"] == "TOOLS/TOOLSNODRAW":
        print(normal)
        print("WARNING: Not shifting plane with material",self.properties["material"],"and normals",self.properties["uaxis"],self.properties["vaxis"])
    # if self.properties["uaxis"][:7] == "[1 0 0 " and self.properties["vaxis"][:7] == "[0 -1 0":
      # self.shiftMaterial("uaxis", vector[0]) # total guess
      # self.shiftMaterial("vaxis", vector[1]) # total guess
    # else:
      # self.shiftMaterial("vaxis", vector[2]) # shift Z
      # if self.properties["uaxis"][:7] == "[0 1 0 " and self.properties["vaxis"][:7] == "[0 0 -1":
        # self.shiftMaterial("uaxis", vector[1]) # shift Y
      # elif self.properties["uaxis"][:7] == "[1 0 0 " and self.properties["vaxis"][:7] == "[0 0 -1":
        # self.shiftMaterial("uaxis", vector[0]) # shift X
      # else:
        # print "WARNING: Not shifting material with normals",self.properties["uaxis"],self.properties["vaxis"]
  
  def TranslateRecurse(self,vector):
    """Recursively translate this node and all child nodes"""
    if self.origin is not None:
      self.translateOrigin(vector)
    elif self.plane is not None:
      self.translatePlane(vector)
      self.TranslateMaterial(vector)
    for child in self.children:
      child = child.TranslateRecurse(vector)
    return self
      
  def ToStringRecurse(self,depth):
    """Recursively print out this node and all child nodes in VMF compatible format"""
    if self.name is not None:
      output = indent(depth) + self.name + "\n" + indent(depth) +"{\n"
      for key, value in list(self.properties.items()):
        output += indent(depth+1) + "\""+key+"\" \""+value+"\"\n"
      if self.origin is not None:
        output += indent(depth+1) + "\"origin\" \""+self.GetOrigin()+"\"\n"
      if self.plane is not None:
        output += indent(depth+1) + "\"plane\" \""+self.GetPlane()+"\"\n"
    else:
      output = ""
      depth -= 1
    for child in self.children:
      output += child.ToStringRecurse(depth+1)
    if self.name is not None:
      output += indent(depth) + "}\n"
    return output
    
  def IncreaseIdRecurse(self,increase):
    """Recursively increase VMF/Hammer IDs of this node and all child nodes"""
    if "id" in self.properties:
      self.properties["id"] = str(int(self.properties["id"]) + increase)
    if "sides" in self.properties:
      sides = self.properties["sides"].split(" ")
      self.properties["sides"] = ""
      for side in sides:
        self.properties["sides"] += str(int(side) + increase)
    for child in self.children:
      child = child.IncreaseIdRecurse(increase)
    return self
  
  def GetMaximumIdRecurse(self,maxId):
    """Find maximum ID recursively"""
    if "id" in self.properties:
      id = int(self.properties["id"])
      if id > maxId:
        maxId = id
    for child in self.children:
      id = child.GetMaximumIdRecurse(maxId)
      if id > maxId:
        maxId = id
    return maxId
  
  def getWorldIndex(self):
    """Get the index of the "world" node in the root node's children"""
    out = None
    for index in range(len(self.children)):
      if self.children[index].name == "world":
        out = index
    return out
  
  def AddOtherMap(self,otherMap):
    """Recursively add all data from another VMFNode tree to this tree"""
    worldIndex = self.getWorldIndex()
    world = self.children[worldIndex]
    for otherNode in otherMap.children:
      if otherNode.name == "world":
        for child in otherNode.children:
          world.AddChild(child)
      elif otherNode.name == "entity":
        self.AddChild(otherNode)
    self.children[worldIndex] = world # index still valid because of append in AddChild
  
  def FindRecurse(self,predicate):
    """Recursively find all nodes matching the predicate"""
    hits = []
    if predicate(self):
      hits = [self]
    else:
      for child in self.children:
        hits.extend(child.FindRecurse(predicate))
    return hits
  
  def DeleteRecurse(self,predicate):
    """Recursively delete all nodes matching the predicate"""
    removed = 0
    for child in self.children:
      if predicate(child):
        self.children.remove(child)
        removed += 1
      else:
        removed += child.DeleteRecurse(predicate)
    return removed
    
  def GetBoundsRecurse(self):
    """Get this map's bounding box by recursively searching for the outmost bounds"""
    bounds = None
    if self.plane is not None:
      bounds = getBounds(self.plane)
    for child in self.children:
      childBounds = child.GetBoundsRecurse()
      if childBounds is not None:
        if bounds is None:
          bounds = childBounds
        else:
          combined = numpy.append(childBounds,bounds).reshape((4,3))
          bounds = getBounds(combined)
    return bounds
  
  def __str__(self): 
    return "VMFNode type "+self.name
