import MapTile
from VMFNode import vectorToString
import os
import random
import argparse


"""
This proof-of-concept random map generator for Left 4 Dead 2 (and other Hammer based maps) loads map tiles from VMF files and puts them together randomly.
"""

TAIL_LENGTH = 3 # The number of portals considered to be the tail of the map. Greater values produce more dead ends.

def chooseConection(connections):
  """Choses a random connection out of the given ones"""
  if len(connections) > 0:
    direction = random.choice(connections)
    portal = random.choice(direction[1])
    otherPortal = random.choice(direction[2])
    connection = (direction[0],portal,otherPortal)
    print("Chose connection %s"%(connection,))
    return connection
  else:
    return None

def collide(box, blockingBoxes):
  """Checks whether two bounding boxes collide"""
  for blockingBox in blockingBoxes:
    if MapTile.collide(blockingBox,box):
      return True
  return False
    
def addTile(base, tile, blockingBoxes):
  """Adds a tile by trying all possible connections"""
  directions = base.findConnections(tile, TAIL_LENGTH)
  for direction in directions:
    for portal in direction[1]:
      for otherPortal in direction[2]:
        connection = (direction[0],portal,otherPortal)
        vectors = base.findPortalsAndVector(tile, connection)
        vector = vectors[0]
        translatedBounds = MapTile.translateBounds(tile.bounds,vector)
        if not collide(translatedBounds,blockingBoxes):
          blockingBoxes.append(translatedBounds)
          base.append(tile, connection, vectors)
          return True
        else:
          print("Tiles collide")
  return False
    
def tryAddTile(base, tile, blockingBoxes):
  """Tries to add a tile by trying one random connection"""
  connections = base.findConnections(tile, TAIL_LENGTH)
  connection = chooseConection(connections)
  if connection is None:
    return False
  vectors = base.findPortalsAndVector(tile, connection)
  vector = vectors[0]
  if vector is None:
    print("Portal size mismatch")
    # TODO: check for portal size match in findConnections
    return False
  translatedBounds = MapTile.translateBounds(tile.bounds,vector)
  if collide(translatedBounds, blockingBoxes):
    print("Tiles collide")
    return False
  else:
    blockingBoxes.append(translatedBounds)
    base.append(tile, connection, vectors)
    return True
    
def selectAndTryToAddTile(base, tiles, blockingBoxes):
  """Selects a random tile and tries to add it to the map"""
  tile = random.choice(tiles)
  print("Chose tile "+os.path.basename(tile.filename))
  success = tryAddTile(base, tile, blockingBoxes)
  if success and tile.getOnce():
    tiles.remove(tile)
    print("Removed tile from pool because it specified to be addeed only once.")
  return success
    
def loadTiles(path):
  """Loads all tiles from a directory"""
  starts = []
  tiles = []
  finales = []
  listing = os.listdir(path)
  for filename in sorted(listing):
    if filename[-3:] == "vmf":
      basename = os.path.basename(filename)
      print("Loading "+basename)
      maptile = MapTile.MapTile()
      maptile.fromfile(path+filename)
      if filename[:5] == "start":
        starts.append(maptile)
      elif filename[:6] == "finale":
        finales.append(maptile)
      else:
        if filename[:4] == "once":
          maptile.setOnce(True)
        tiles.append(maptile)
        try: 
          repeat = int(basename.split('_')[0])
          print("Tile is %d times more likely to be chosen."%(repeat))
          for i in range(repeat):
            tiles.append(maptile)
        except ValueError:
          pass
  return (starts, tiles, finales)
    
if __name__ == "__main__":
  """Main program"""

  parser = argparse.ArgumentParser()
  parser.add_argument("--tilesdir", help="directory to load the tiles from", default="tiles/office/")
  parser.add_argument("--cfgfile", help="path to store the script for generating the navigation mesh to", default="../../../left4dead2/cfg/combined.cfg")
  parser.add_argument("--outfile", help="path to store the output file to", default="combined.vmf")
  parser.add_argument("--seed", help="Seed to initialize the pseudo-random number generator with. This random seed affects the selection of tiles and connections. Different values lead to completely different map layouts.", default=42)
  parser.add_argument("--tilecount", help="How many tiles there should be in the map.", default=19)
  args = parser.parse_args()
  random.seed(args.seed)
  
  starts, tiles, finales = loadTiles(args.tilesdir)
  base = random.choice(starts)
  finale = random.choice(finales)
  blockingBoxes = [base.bounds]

  tilesAdded = 0
  for i in range(args.tilecount*len(tiles)):
    if selectAndTryToAddTile(base, tiles, blockingBoxes):
      tilesAdded += 1
    if tilesAdded == args.tilecount:
      break
  print("%d tiles added"%(tilesAdded))
      
  if not addTile(base, finale, blockingBoxes):
    print("ERROR: Failed to append final \"finale\" tile.")
  else:
    pass
    
  base.close()

  file = open(args.outfile,"w")
  file.write(base.map.root.ToStringRecurse(0))
  file.close()

  if args.cfgfile:
    try:
      file = open(args.cfgfile,"w")
      file.write(base.generateNavMeshScript())
      file.close()
    except IOError:
      print("Could not write %s."%(args.cfgfile))
