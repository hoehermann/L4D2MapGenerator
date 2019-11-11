## About:
This is a proof of concept random map generator for Source Based games.  
It is intended to create levels from random map tiles for Left 4 Dead 2.  
This project is abandoned. Pick it up, if you like!  
Created by Mc$core, ask him for help. Knowledge of Pyhton programming required.  
http://www.hehoe.de/mcs  
CC BY-SA 3.0

**Note:** As of 2019, this generator is not fully operative. The map generation itself is fine, but it looks like the [navigation mesh generation](https://developer.valvesoftware.com/wiki/Navigation_Meshes) was changed. You can see the map, but due to a reportedly troublesome navigation mesh, the game deems the map "unplayable".

## Usage:
* Put the files into the directory "…\Steam\SteamApps\common\left 4 dead 2\sdk_content\mapsrc\mcs".
* Hold shift while performing a right-click in the directory and open a PowerShell or command-line here.
* Run the python script "combiner.py". The script was tested with Python 3.7.0 and NumPy 1.17.4.
* Open the resulting map source file "combined.vmf" in the Hammer Editor with the appropriate configuration (for L4D2 Hammer is started from the L4D2 Authoring Tools).
* Choose File → Run Map.
* Start L4D2 with the console enabled (using -console and -dev as command-line parameters is recommended) and load the map (direct execution by Hammer is fine, too).
* Execute the config file "combined" by entering "exec combined" in the console.
* Press the + key on your keypad repeatedly. This will let the game generate the nav mesh. Keep striking it until the level loads for the second time and cheats are disabled again. Continuing to strike + will do nothing but printing "Finished" to the console.
* Restart L4D2 and start playing!

## Advanced Usage:
* Edit combiner.py and change the seed and/or NUMBER_OF_TILES for different maps.
* In case the final map cannot be added, try a different setting or tweak the map in Hammer.
* Create additional tiles or new tile sets (see below)

## Included Features:
- Nonlinear levels
- Support for more than one door per direction
- Support for doors in arbitrary position
- Support for overlays and cubemaps
- Checks for different door sizes
- Loop detection and mending with self
- Support for rectangular shaped map tiles of arbitrary size
- Improved map tile collision detection
- Support for more than one ground level

## Missing Features:
- proper translation of materials
- fully automated nav mesh generation ("pointer" crosshair is not updated with setpos - player interaction needed)
- to be checked: what else apart from overlays and cubemaps needs IDs to operate
- to be checked: alpha blending on displacements
- Improved layout generation
- Calculate distances while generating (Dijkstra?), limit dead-end lengths
- Support ladders
- Improve automatic navigation mesh generation

## Map Tiles:
A map tile is connected to the next tile with a "portal". To define a portal, create a solid brush within the outmost side of the tile. Apply the material DEV/DEV_BLENDMEASURE (configurable) to the side facing outward only. This markes this exact position to be a "portal". The combiner looks for portals to mend the tiles together. You may place a prop_door_rotating in the vicinity (configurable) of the portal. In case the door leads to nowhere, the combiner will remove the door and leaves the solid in place. In case the door connects to another room, the solid is removed and the door is left in place. A map tile must allow player transit between all portals.  
A tile is always translated only, never rotated. Due to the translation, all positions will become integers (they should be integers anyway). Angles are unaffected.
