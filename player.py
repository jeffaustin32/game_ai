"""
    This module handles everything relating to the player
    """
from enum import Enum
from time import sleep
from utilities import Utilities
from user_interface import UserInterface
from backpack import Backpack
from mine import Mine
from smelt import Smelt
from forge import Forge

class Player():
    """
        This class handles everything relating to the player
        """
    LOW_HEALTH = 150
    TASKS = Enum('Task', 'MINE, SMELT, FORGE')

    def __init__(self, game_map, task=TASKS.MINE):
        self.utils = Utilities()
        self.user_interface = UserInterface()
        self.backpack = Backpack()
        self.mine = Mine(self, game_map)
        self.smelt = Smelt(self, game_map)
        self.forge = Forge(self, game_map)

        # Set the default initial task
        self.task = task
        self.action_count = 0

    def perform_task(self):
        """
            Checks health, organizes backpack and then performs
            one of the following tasks: mine, smelt, or forge
            """
        self.action_count += 1

        # Do pre-task checks
        self.organize_backpack()
        # Only check health every 25 turns (it is a slow process)
        if self.action_count % 25 == 0:
            self.action_count = 0
            self.check_health()

        # Perform task
        if self.task == self.TASKS.MINE:
            self.task = self.mine.mine()
            delay = 0
        elif self.task == self.TASKS.SMELT:
            self.task = self.smelt.smelt()
            delay = 1
        elif self.task == self.TASKS.FORGE:
            self.task = self.forge.forge()
            delay = 2

        # Give the task time to complete
        sleep(delay)

    def check_health(self):
        """
            Checks player's HP and uses a potion if it is low.
            If no potions are found, game will quit
            """
        # Check if HP is low
        if self.user_interface.get_health() < self.LOW_HEALTH:
            # Attempt to use a potion
            self.utils.log("INFO", F"Health dropped below {self.LOW_HEALTH}")
            used_potion = self.backpack.use_item('potion', offset=(4, 9))

            # No potions were found
            if not used_potion:
                self.utils.log("SEVERE", "No potions found")
                self.utils.quit_game()

            # Sleep so that there is no issue using the next item
            self.utils.log("INFO", F"Used a potion")
            sleep(6)

    def is_weight_below_threshold(self, threshold):
        # Calculate how much more weight the player can carry
        current_weight, max_weight = self.user_interface.get_weight()
        difference = max_weight - current_weight

        # Check if the weight the player can carry is below the threshold
        if difference < threshold:
            self.utils.log("INFO", F"Weight is {difference} from max, threshold was set to {threshold}")
            return True

        return False

    def organize_backpack(self):
        """
            Move all items to the correct areas of the backpack
            """
        self.backpack.move_item('ore', self.backpack.ORE_LOC, (8, 6))
        self.backpack.move_item('gem', self.backpack.GEM_LOC, (4, 2))
        self.backpack.move_item('jewel', self.backpack.GEM_LOC, (4, 2))
        self.backpack.move_item('galantine', self.backpack.GEM_LOC, (5, 4))
        self.backpack.move_item('pickaxe', self.backpack.PICKAXE_LOC, (9, 4))
        self.backpack.move_item('dagger', self.backpack.DAGGER_LOC, (4, 6))
        self.backpack.move_item('hammer', self.backpack.HAMMER_LOC, (7, 3))
        self.backpack.move_item('gold', self.backpack.GEM_LOC, (6, 5))
        self.backpack.move_item('ingot', self.backpack.INGOT_LOC)