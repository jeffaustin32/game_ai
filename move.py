"""
    This module handles all actions related to movement
    """
import random
from time import sleep
import numpy as np
import pyautogui
from astar import AStar
from utilities import Utilities


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
        # Therefore, can normalize by subtracting 3156 from all sextant readings
        # The bounding box then becomes:
        # x-axis: 0 -> 81
        # y-axis: 163 -> 240
        self.astar = AStar()
        self.utils = Utilities()
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
            path = self.astar.astar(
                self.game_map.game_map, self.game_map.player_position, destination)

            # Failed to get a path, retry up to 3 times
            if not path:
                error += 1
                self.utils.log(
                    "WARN", F"Failed to get path from {self.game_map.player_position} to {destination}")
                
                # Update map incase something was mislabeled
                self.game_map.update_map()

                # Try mining at a different mountain
                if mining:
                    return False

                if error == 10:
                    self.utils.log(
                        "SEVERE", "Failed to get path after 10 attempts")
                    self.utils.debug_print_matrix(
                        self.game_map.game_map.T)
                    self.utils.quit_game()

                # Wait for merchant to move
                blacksmith_errors = 0
                while self.game_map.game_map[destination] == self.game_map.TILES.BLACKSMITH.value:
                    # Don't wait forever for him to move
                    blacksmith_errors += 1
                    if blacksmith_errors == 20:
                        self.utils.log(
                            "SEVERE", "Waited 100 seconds for blacksmith to move, suspect error")
                        self.utils.quit_game()

                    self.utils.log(
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
                self.utils.log(
                    "SEVERE", "Failed to move after 10 attempts")
                self.utils.debug_print_matrix(
                    self.game_map.game_map.T)
                self.utils.quit_game()
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
            self.utils.log(
                'SEVERE', F"Invalid step difference. xDiff: {x_diff}, yDiff: {y_diff}")
            self.utils.quit_game()

        # Move along path
        pyautogui.press(direction)
        sleep(0.3)

        # Player moved, re-detect environment
        screenshot = self.utils.take_screenshot()
        self.game_map.update_player_position(screenshot)
        self.game_map.update_map()

    # TODO: Remove this class after merchant class done
    def go_to_weapon_shopkeeper(self):
        """
            Moves player to the Lyrina weapon shopkeeper.
            Player stops at the center tile of the three tile table.
            This way, the player can always reach the shopkeeper
            """
        if self.game_map.player_position == self.WEAPON_SHOPKEEPER:
            return

        self.utils.log('INFO', F"Moving to shopkeeper {self.WEAPON_SHOPKEEPER}")
        self.move_to(self.WEAPON_SHOPKEEPER)
        self.utils.log(
            'INFO', F"Arrived at shopkeeper {self.game_map.player_position}")

    def go_to_mine(self):
        """
            Moves player to a mineable rock and gives the pixel
            coordinates for the pickaxe to be used at. Only consider
            mountains within 10 rows above/below the player
            """
        errors = 0
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
                    self.utils.log("INFO", "Only a single mountain visible, returning to start position")
                    coords = self.MOUNTAIN_RANGE

                # There are other possible mountains, try again
                continue

            mine_at = (192, 176)

            # Walk to the mountain
            self.utils.log('INFO', F"Moving to mineable rock {coords}")
            arrived_at_destination = self.move_to(coords, True)
        self.utils.log(
            'INFO', F"Arrived at mineable rock {self.game_map.player_position}")
        return mine_at

    def go_to_furnace(self):
        """
            Moves the player to below the furnace. From here, the player can both
            run the bellow and use the furnace.
            """
        if self.game_map.player_position == self.FURNACE:
            return

        self.utils.log('INFO', F"Moving to furnace {self.FURNACE}")
        self.move_to(self.FURNACE)
        self.utils.log(
            'INFO', F"Arrived at furnace {self.game_map.player_position}")
        
    def go_to_anvil(self):
        """
            Moves the player to below the anvil. From here, the player can both
            run the bellow and use the anvil.
            """
        if self.game_map.player_position == self.ANVIL:
            return

        self.utils.log('INFO', F"Moving to anvil {self.ANVIL}")
        self.move_to(self.ANVIL)
        self.utils.log(
            'INFO', F"Arrived at anvil {self.game_map.player_position}")

    # TODO: Encorporate all click positioning into merchant class
    def go_to_blacksmith(self):
        """
            Moves the player adjacent to the blacksmith NPC.
            Used to buy pickaxes and hammers.
            """
        # Check if the blacksmith is within the player's sight
        nearby = self.game_map.game_map[
            (self.game_map.player_position[0] - 10): (self.game_map.player_position[0] + 11),
            (self.game_map.player_position[1] - 10): (self.game_map.player_position[1] + 11)
        ]
        index = np.where(nearby == self.game_map.TILES.BLACKSMITH.value)
        if len(index[0]) == 0:
            self.utils.log(
                "INFO", "Blacksmith is not within sight, moving to furnace to find him")
            self.go_to_furnace()

        destination = (0, 0)
        click = None
        steps = 0
        while not self.game_map.player_position == destination:
            # The blacksmith will be nearby
            nearby = self.game_map.game_map[
                (self.game_map.player_position[0] - 10): (self.game_map.player_position[0] + 11),
                (self.game_map.player_position[1] - 10): (self.game_map.player_position[1] + 11)
            ]

            # Find the blacksmith
            index = np.where(
                nearby == self.game_map.TILES.BLACKSMITH.value)
            if len(index[0]) == 0:
                self.game_map.update_map()

            blacksmith = (index[0][0], index[1][0])

            # Find an accessible space beside the blacksmith
            nearby_blacksmith = nearby[
                (blacksmith[0] - 1): (blacksmith[0] + 2),
                (blacksmith[1] - 1): (blacksmith[1] + 2)
            ]

            index = np.where(nearby_blacksmith ==
                             self.game_map.TILES.PLAYER.value)
            if len(index[0]) > 0:
                click = (blacksmith[0] - 10, blacksmith[1] - 10)
                break

            index = np.where(nearby_blacksmith ==
                             self.game_map.TILES.ACCESSIBLE.value)
            destination = (index[0][0], index[1][0])
            destination = (blacksmith[0] + destination[0] - 1,
                           blacksmith[1] + destination[1] - 1)
            # Player is always in the middle
            player = (10, 10)

            # Find path from player to destination
            path = self.astar.astar(nearby, player, destination)
            step_to = path[0]
            step_to = (self.game_map.player_position[0] + step_to[0] - 10,
                       self.game_map.player_position[1] + step_to[1] - 10)

            self.step(step_to)
            steps += 1

            # This has been way too many steps
            if steps == 50:
                self.utils.log(
                    "SEVERE", "Blacksmith was within sight but still took 50 steps")
                self.utils.quit_game()

        # Calculate where to click for blacksmith
        click = (
            (click[0] * 16) + 175,
            (click[1] * 16) + 175
        )

        return click
