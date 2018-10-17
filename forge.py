"""
    This module performs forging related tasks
    """
from time import sleep
import pyautogui
import utilities as utils
from move import Move
from user_interface import UserInterface
from merchant import Merchant

class Forge():
    """
        This class performs forging related tasks
        """

    ITEM = 'dagger'

    def __init__(self, player, game_map):
        self.user_interface = UserInterface()
        self.game_map = game_map
        self.move = Move(game_map)
        self.merchant = Merchant(game_map, self.move)
        self.player = player
        self.errors = 0

    def sell_items(self):
        """
            Sell all instances of the forged item
            """
        # Check if the sextant is visible, it may be obscured by forged items
        if not self.player.backpack.get_item('sextant'):
            # Not at the shopkeeper and no sextant, move left 4 times
            for _ in range(4):
                pyautogui.press('a')
                sleep(0.3)
            self.game_map.player_position = self.move.WEAPON_SHOPKEEPER

        # Sell items
        items_sold = self.merchant.sell_item(self.ITEM, self.merchant.MERCHANTS.WEAPONS)
        while items_sold > 0:
            items_sold = self.merchant.sell_item(self.ITEM, self.merchant.MERCHANTS.WEAPONS)

    def forge(self):
        """
            Forge all ingots into Battle Axes
            """
        # Get player's weight
        if self.player.is_weight_below_threshold(15):
            utils.log("INFO", F"Weight is below threshold, selling {self.ITEM}s")
            self.sell_items()

        # Buy a hammer if player has none
        if not self.player.backpack.get_item('hammer'):
            # Hammer hay be obscured by a forged weapon, sell first
            self.sell_items()

            # Still no hammer, buy one
            if not self.player.backpack.get_item('hammer'):
                utils.log("INFO", "No hammers remain, buying a hammer")
                self.merchant.buy_item('hammer', self.merchant.MERCHANTS.BLACKSMITH)

        # Move to the anvil, if already there, nothing happens
        self.move.go_to_anvil()

        # Find the ingots in the player's backpack
        ingot = self.player.backpack.get_item('ingot')
        if not ingot:
            utils.log("INFO", F"No ingots remain, selling {self.ITEM}s")
            self.sell_items()
            self.move.go_to_anvil()

            # Check again to see if there are ingots, may have been obscurred
            ingot = self.player.backpack.get_item('ingot')
            if not ingot:
                return self.player.TASKS.MINE

        # Use the hammer on the ingots
        self.player.backpack.use_item('hammer', (ingot[0] + 6, ingot[1] + 6), (7, 3))

        # Allow the blacksmith menu to fail a few times
        if not self.user_interface.wait_for_ui_element('blacksmithMenu', False):
            self.errors += 1

            # Something must actually be wrong
            if self.errors == 5:
                utils.log("SEVERE", "Failed to open blacksmith menu after 5 attempts")
                utils.quit_game()

            # Start the forge task over again
            return self.player.TASKS.FORGE
        
        # Found the menu, reset error count
        self.errors = 0

        # Forge a Battle Axe
        weapon = self.user_interface.wait_for_ui_element(self.ITEM)
        pyautogui.moveTo(weapon[0] + 9, weapon[1] + 10, 0.15)
        pyautogui.doubleClick()

        # Continue forging
        return self.player.TASKS.FORGE
