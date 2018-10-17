"""
    This module handles all actions related to movement
    """
import random
from time import sleep
import numpy as np
import pyautogui
import astar
import utilities as utils


class Move:
    """
        This class handles all actions related to movement
        """
    BANKER = (34, 203)
    POTION_SHOPKEEPER = (25, 209)
    ITEM_SHOPKEEPER = (26, 219)
    WEAPON_SHOPKEEPER = (47, 217)
    FURNACE = (54, 217)
    ANVIL = (51, 217)
    MOUNTAIN_RANGE = (65, 207)

    def __init__(self, game_map):
        # Notes on sextant usage::
        # Going left reduces x-values, going up reduces y-values
        # The bounding box for lyria is:
        #   x-axis: 3150 -> 3231
        #   y-axis: 3313 -> 3390
        # Therefore, can scale by subtracting 3156 from all sextant readings
        # The bounding box then becomes:
        #   x-axis: 0 -> 81
        #   y-axis: 163 -> 240
        self.game_map = game_map

    def move_to(self, destination, mining=False):
        """
            Finds a path from the players position to the destination using the aStar
            shortest path algorithm.  Once a path is found, the player takes a step.
            After each step, the surroundings are examined again and a new path is
            calculated. This extra work is required because obstacles such as the shopkeepers
            can move and impede the players movement.
            """
        error = 0
        turns_without_moving = 0
        while not self.game_map.player_position == destination:
            # Find a path to the destination
            path = astar.get_path(self.game_map.game_map, self.game_map.player_position, destination)

            # Failed to get a path, retry up to 3 times
            if not path:
                error += 1
                utils.log("WARN", F"Failed to get path from {self.game_map.player_position} to {destination}")

                # Update map incase something was mislabeled
                self.game_map.update_map()

                # Try mining at a different mountain
                if mining:
                    return False

                if error == 10:
                    utils.log(
                        "SEVERE", "Failed to get path after 10 attempts")
                    utils.debug_print_matrix(
                        self.game_map.game_map.T)
                    utils.quit_game()

                # Wait for merchant to move
                blacksmith_errors = 0
                while self.game_map.game_map[destination] == self.game_map.TILES.BLACKSMITH.value:
                    # Don't wait forever for him to move
                    blacksmith_errors += 1
                    if blacksmith_errors == 20:
                        utils.log(
                            "SEVERE", "Waited 100 seconds for blacksmith to move, suspect error")
                        utils.quit_game()

                    utils.log(
                        "INFO", "Blacksmith is blocking spot, waiting for him to move")
                    sleep(5)
                continue

            # Reset error count
            error = 0

            # Get the next move from the path
            step_to = path[0]
            destination = path[-1]

            # Take a step towards the destination
            previous_position = self.game_map.player_position
            self.step(step_to)

            # Check if the player has gone several turns without movement
            if previous_position == self.game_map.player_position:
                turns_without_moving += 1
            else:
                turns_without_moving = 0

            if turns_without_moving == 10:
                utils.log(
                    "SEVERE", "Failed to move after 10 attempts")
                utils.debug_print_matrix(
                    self.game_map.game_map.T)
                utils.quit_game()
        return True

    def step(self, new_position):
        """
            Given a set of coordinates, calculate what direction to step
            and send that key to the game
            """
        # Calculate direction of movement
        x_diff = self.game_map.player_position[0] - new_position[0]
        y_diff = self.game_map.player_position[1] - new_position[1]

        # Determine what key to press
        direction = ''
        if x_diff == 1:
            direction = 'a'
        elif x_diff == -1:
            direction = 'd'
        elif y_diff == 1:
            direction = 'w'
        elif y_diff == -1:
            direction = 's'
        else:
            utils.log(
                'SEVERE', F"Invalid step difference. xDiff: {x_diff}, yDiff: {y_diff}")
            utils.quit_game()

        # Move along path
        pyautogui.press(direction)
        sleep(0.1)

        # Player moved, re-detect environment
        screenshot = utils.take_screenshot()
        self.game_map.update_player_position(screenshot)
        self.game_map.update_map()

    def go_to_mine(self):
        """
            Moves player to a mineable rock and gives the pixel
            coordinates for the pickaxe to be used at. Only consider
            mountains within 10 rows above/below the player
            """
        arrived_at_destination = False
        coords = (0, 0)
        while not arrived_at_destination:
            nearby = self.game_map.game_map[
                (self.game_map.player_position[0] - 10): (self.game_map.player_position[0] + 11),
                (self.game_map.player_position[1] - 10): (self.game_map.player_position[1] + 11)
            ]

            # Filter map to contain only rock1 and rock2 tiles
            mountains = np.where(
                nearby == self.game_map.TILES.MOUNTAIN.value)

            # No mountains have been found
            if len(mountains[0]) == 0:
                # Move to where mountains are
                self.move_to(self.MOUNTAIN_RANGE)

                # Update position
                nearby = self.game_map.game_map[
                    (self.game_map.player_position[0] - 10): (self.game_map.player_position[0] + 11),
                    (self.game_map.player_position[1] - 10): (self.game_map.player_position[1] + 11)
                ]
                mountains = np.where(
                    nearby == self.game_map.TILES.MOUNTAIN.value)

            # Get the coordinates of a randomly selected mountain
            if len(mountains[0]) == 1:
                index = 0
            else:
                index = random.randint(0, len(mountains[0])-1)
            x = mountains[0][index]
            y = mountains[1][index]

            x = self.game_map.player_position[0] + x - 10
            y = self.game_map.player_position[1] + y - 10

            # Find a walkable cell adjacent to the mountain
            prev_coords = coords
            coords = (x-1, y)

            # This is the same mountain we just tried mining at
            if coords == prev_coords:
                # Check if this was the only visible mountain
                if len(mountains[0]) == 1:
                    # Go back to the starting mining position
                    utils.log("INFO", "Only a single mountain visible, returning to start position")
                    coords = self.MOUNTAIN_RANGE

                # There are other possible mountains, try again
                continue

            mine_at = (192, 176)

            # Walk to the mountain
            utils.log('INFO', F"Moving to mineable rock {coords}")
            arrived_at_destination = self.move_to(coords, True)
        utils.log('INFO', F"Arrived at mineable rock {self.game_map.player_position}")
        return mine_at

    def go_to_furnace(self):
        """
            Moves the player to below the furnace. From here, the player can both
            run the bellow and use the furnace.
            """
        if self.game_map.player_position == self.FURNACE:
            return

        utils.log('INFO', F"Moving to furnace {self.FURNACE}")
        self.move_to(self.FURNACE)
        utils.log(
            'INFO', F"Arrived at furnace {self.game_map.player_position}")
        
    def go_to_anvil(self):
        """
            Moves the player to below the anvil. From here, the player can both
            run the bellow and use the anvil.
            """
        if self.game_map.player_position == self.ANVIL:
            return

        utils.log('INFO', F"Moving to anvil {self.ANVIL}")
        self.move_to(self.ANVIL)
        utils.log(
            'INFO', F"Arrived at anvil {self.game_map.player_position}")
