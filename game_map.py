"""
    This module is used to detect inaccessible tiles in the gameplay
    region and perform actions with them.
    """
import os
from time import sleep
from enum import Enum
import re
import numpy as np
import cv2
import pyautogui
import pytesseract
from utilities import Utilities
from backpack import Backpack

class GameMap:
    """
        This class is used to detect inaccessible tiles in the gameplay
        region and perform actions with them.
        """
    TILE_DIM = 16
    TILES = Enum(
        'Tile', 'UNKNOWN, ACCESSIBLE, DOOR, GRAVEL, INACCESSIBLE, MOUNTAIN, WEAPON_SHOPKEEPER, ITEM_SHOPKEEPER, POTION_SHOPKEEPER, BANKER, BLACKSMITH, PLAYER')

    def __init__(self):
        """
            Create a tuple for each tile containing the following properties:
            0: tile data, 1: name, 2: frequency
            Frequency will be incremented every time the tile is found
            and be used to sort the list. This will result in fewer overall comparisons
            """
        self.utils = Utilities()
        self.backpack = Backpack()
        self.game_map = np.ones(shape=(82, 240), dtype="int")
        self.game_map[:, 0:166] = self.TILES.INACCESSIBLE.value
        self.game_map[:, -10:-1] = self.TILES.INACCESSIBLE.value
        self.game_map[0, :] = self.TILES.INACCESSIBLE.value
        self.game_map[-10:-1, :] = self.TILES.INACCESSIBLE.value
        self.player_position = (0, 0)

        # Load all accessible tile templates
        self.accessible_templates = []
        for tile in os.listdir('./accessible_tiles'):
            tile_template = cv2.imread('./accessible_tiles/' + tile)
            tile_template = cv2.cvtColor(tile_template, cv2.COLOR_BGR2GRAY)
            self.accessible_templates.append(
                [tile_template, 'accessible/' + tile.split('.')[0], 0])

        # Load all inaccessible tile templates
        self.inaccessible_templates = []
        for tile in os.listdir('./inaccessible_tiles'):
            tile_template = cv2.imread('./inaccessible_tiles/' + tile)
            tile_template = cv2.cvtColor(tile_template, cv2.COLOR_BGR2GRAY)
            self.inaccessible_templates.append(
                [tile_template, 'inaccessible/' + tile.split('.')[0], 0])
        
         # Load all NPC tile templates
        self.npc_templates = []
        for tile in os.listdir('./npcs'):
            tile_template = cv2.imread('./npcs/' + tile)
            tile_template = cv2.cvtColor(tile_template, cv2.COLOR_BGR2GRAY)
            self.npc_templates.append(
                [tile_template, 'npcs/' + tile.split('.')[0], 0])

    def update_player_position(self, screenshot):
        """To update the player position the following steps are taken.
            1. The sextant is location and used
            2. The coordinates are parsed and normalized
            3. Old player position is removed from map
            4. New player position is added to the map

            If any of these operations fails, the game will quit.

            Returns tuple containing player position as well as the tile map
            """

        sextant_x = None
        sextant_y = None
        errors = 0

        while sextant_x is None:
            # Move mouse to a neutral position that won't obstruct template matching
            pyautogui.moveTo(400, 400)

            # Find and use the sextant
            self.backpack.use_item('sextant', None, (5, 2), True)

            # Take a new screenshot that includes the location
            screenshot = self.utils.take_screenshot()

            # Find the current position
            position = screenshot[450: 465, 120: 180]

            # Resize and parse the image to a string
            position = cv2.resize(position, (0, 0), fx=5, fy=5)
            position = cv2.bitwise_not(position)
            position = cv2.blur(position, (8, 8))

            text = ''

            try:
                text = pytesseract.image_to_string(position, config='--psm 8')
                # Split the text into coordinates
                sextant_x, sextant_y = text.split(", ")[0::1]
            except UnicodeDecodeError:
                self.utils.log(
                    "SEVERE", F"Unable to parse sextant coordinates string")
                self.utils.quit_game()
            except ValueError as value_error:
                self.utils.log("WARN", F"{value_error}")
                # Move mouse to a neutral position that won't obstruct template matching
                pyautogui.moveTo(400, 400)
                errors += 1

            if errors == 10:
                self.utils.log(
                    "SEVERE", F"Sextant failed 10 times")
                self.utils.quit_game()

        # Normalize the coordinates to fit the map indicies
        normalized_x = int(sextant_x) - self.utils.NORMALIZATION_CONSTANT
        normalized_y = int(sextant_y) - self.utils.NORMALIZATION_CONSTANT

        # Remove old player position from the map
        self.game_map[self.game_map ==
                      self.TILES.PLAYER.value] = self.TILES.ACCESSIBLE.value
        self.player_position = (normalized_x, normalized_y)
        self.game_map[self.player_position] = self.TILES.PLAYER.value

    def match_template_type(self, tile, templates):
        """
            Compare the tile with a set of templates
            """
        potential_tiles = []

        # Go through all accessible tiles
        for template in templates:
            result = cv2.matchTemplate(
                tile, template[0], cv2.TM_CCORR_NORMED)
            max_val = cv2.minMaxLoc(result)[1]

            # Confidence too low for a match
            if max_val < 0.90:
                continue

            # This is a potential tile
            potential_tiles.append((template, max_val))

            # Very high confidence that this is the correct tile
            if max_val > 0.99:
                break
        
        return potential_tiles

    def update_map(self, screenshot=None):
        """
            Takes a screenshot of the game, this method will iterate
            over the gameplay region in 16x16 chunks.  Each chunk is compared
            with all potential inaccessible tiles until a match is found.

            When a match is found, the frequency of that tile is incremented
            so future chunks are compared with high frequency tiles first.
            """

        # Clear all in the nearby
        nearby = self.game_map[
            (self.player_position[0] - 10): (self.player_position[0] + 11),
            (self.player_position[1] - 10): (self.player_position[1] + 11)
        ]
        nearby.fill(self.TILES.UNKNOWN.value)

        # Take screenshot and isolate the gamplay region
        if screenshot is None:
            screenshot = self.utils.take_screenshot()
        play = screenshot[8:344, 8:344]

        # loop through gameplay region, incrementing by 16 pixels
        for i in range(21):
            for j in range(21):
                # Scale up the dimensions
                tile_x = j * self.TILE_DIM
                tile_y = i * self.TILE_DIM

                # The center cell is always the player
                if i == 10 and j == 10:
                    tile_x = self.player_position[0] + int(tile_x / 16) - 10
                    tile_y = self.player_position[1] + int(tile_y / 16) - 10
                    self.game_map[(tile_x, tile_y)] = self.TILES.PLAYER.value
                    continue

                # Slice the tile from the play region
                tile = play[tile_y:tile_y + self.TILE_DIM,
                            tile_x:tile_x + self.TILE_DIM]

                tile_x = self.player_position[0] + int(tile_x / 16) - 10
                tile_y = self.player_position[1] + int(tile_y / 16) - 10

                # Go through all tile types looking for a high confidence match
                potential_tiles = []
                potential_tiles += self.match_template_type(tile, self.inaccessible_templates)
                potential_tiles += self.match_template_type(tile, self.accessible_templates)
                potential_tiles += self.match_template_type(tile, self.npc_templates)

                # Failed to find a template match for the tile
                if len(potential_tiles) == 0:
                    # Assume it is inaccessible
                    self.game_map[(tile_x, tile_y)] = self.TILES.INACCESSIBLE.value
                    continue

                # Sort the potential tiles to find the most likely
                potential_tiles = sorted(
                    potential_tiles, key=lambda tup: tup[1])

                # Chose the most likely template
                template = potential_tiles[0][0]

                # Increment tile occurrence frequency
                template[2] += 1

                # By default, mark tile as inaccessible
                label = None

                # Mark as mineable
                if re.search(r'rock', template[1], re.M | re.I):
                    label = self.TILES.MOUNTAIN.value
                elif re.search(r'door', template[1], re.M | re.I):
                    label = self.TILES.DOOR.value
                elif re.search(r'gravel', template[1], re.M | re.I):
                    label = self.TILES.GRAVEL.value
                elif re.search(r'shopkeeper', template[1], re.M | re.I):
                    label = self.TILES.WEAPON_SHOPKEEPER.value
                elif re.search(r'blacksmith', template[1], re.M | re.I):
                    label = self.TILES.BLACKSMITH.value
                elif re.search(r'guard', template[1], re.M | re.I):
                    label = self.TILES.INACCESSIBLE.value
                elif re.search(r'inaccessible', template[1], re.M | re.I):
                    label = self.TILES.INACCESSIBLE.value
                elif re.search(r'accessible', template[1], re.M | re.I):
                    label = self.TILES.ACCESSIBLE.value
                
                if label is None:
                    print(template[1])

                # Calculate coordinates of tile in the map relative to the player
                self.game_map[(tile_x, tile_y)] = label

        # Sort the tiles based on their frequency
        self.accessible_templates = sorted(
            self.accessible_templates, key=lambda tup: tup[2])
        self.inaccessible_templates = sorted(
            self.inaccessible_templates, key=lambda tup: tup[2])
        self.npc_templates = sorted(
            self.npc_templates, key=lambda tup: tup[2])

        self.update_mountain_accessibility()
        return

    def update_mountain_accessibility(self):
        """
            This method is intended to be executed after tile detection has occurred.
            It will examine all the newly added around the player and check that
            each mountain tile has atleast one accessible tile adjacent to it. If it
            does not, it will update the map to relabel that tile as inaccessibl.
            """
        # Slice a view of the map, restricted to just the visible range
        nearby = self.game_map[
            (self.player_position[0] - 10): (self.player_position[0] + 11),
            (self.player_position[1] - 10): (self.player_position[1] + 11)
        ]

        # Go through all tiles in the gameplay region
        for i in range(21):
            for j in range(21):
                # Found a mountain tile
                if nearby[(i, j)] == self.TILES.MOUNTAIN.value:
                    tile_left = nearby[(i-1, j)]

                    # Only allow mountains to be minable if they are beside gravel
                    if not tile_left == self.TILES.GRAVEL.value:
                        nearby[(i, j)] = self.TILES.INACCESSIBLE.value

        return self.game_map
