"""
    This module performs weapon selling related tasks
    """
from time import sleep
import re
import cv2
import pyautogui
from utilities import Utilities
from move import Move
from backpack import Backpack
from user_interface import UserInterface

# TODO: Encorporate all class logic into merchant
class Sell():
    """
        This class performs weapon selling related tasks
        """

    def __init__(self, game_map):
        self.utils = Utilities()
        self.move = Move(game_map)
        self.game_map = game_map
        self.user_interface = UserInterface()
        self.backpack = Backpack()

    def click_shopkeeper(self, screenshot):
        """
            Take a screenshot and find the shopkeeper. Returns coords to click
            """

    def sell(self):
        """
            Sell all great daggers to the shop keeper
            """
        # Check if the sextant is visible, it may be obscured by forged items
        if self.backpack.get_item('sextant'):
            # Move to the shopkeeper, if already there, nothing happens
            self.move.go_to_weapon_shopkeeper()
        elif not self.game_map.player_position == self.move.WEAPON_SHOPKEEPER:
            # Not at the shopkeeper and no sextant, move left 4 times
            for _ in range(4):
                pyautogui.press('a')
                sleep(0.3)

        shopkeeper = None
        buy_or_sell = False
        errors = 0
        while not buy_or_sell:
            # Get the area where shopkeeper moves
            for template in self.game_map.npc_templates:
                # This template is not for the shopkeeper
                if not re.search(r'shopkeeper', template[1], re.M | re.I):
                    continue

                screenshot = self.utils.take_screenshot()
                result = cv2.matchTemplate(
                    screenshot, template[0], cv2.TM_CCORR_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)

                # High confidence of a match
                if max_val > 0.90:              
                    shopkeeper = (max_loc[0] + 7, max_loc[1] + 7)
                    break

            # Failed to find the shopkeeper
            if shopkeeper is None:
                self.utils.log("SEVERE", "Failed to find shopkeeper")
                self.utils.quit_game()

            # Click the shopkeeper
            pyautogui.moveTo(shopkeeper[0], shopkeeper[1], 0.15)
            pyautogui.doubleClick()
            sleep(1.5)

            # Check that the buy or sell window was opened
            buy_or_sell = self.user_interface.get_ui_element('buyOrSell', exit_on_fail=False)
            if not buy_or_sell:
                errors += 1
                self.utils.log("INFO", F"Shopkeeper supposed to be at {shopkeeper} but buy/sell window didn't open")
                screenshot = self.utils.take_screenshot()
            
            if errors == 10:
                self.utils.log("SEVERE", "Failed to open the buy/sell window 10 times")
                self.utils.quit_game()

        # Click the sell button
        sell_button = self.user_interface.get_ui_element('sell')
        pyautogui.moveTo(sell_button[0] + 10, sell_button[1] + 10, 0.15)
        pyautogui.click()
        sleep(1.5)        

        # If the player has no more daggers, time to switch tasks
        switch_task = False

        # Offer up to 12 great daggers
        daggers_sold = 0
        for i in range(12):
            # Move the cursor away so it will register an "hover" event when move back
            pyautogui.moveTo(330, 206)

            # Find a dagger to sell
            dagger = self.user_interface.get_ui_element(
                'greatDaggerMenu', exit_on_fail=False)

            # No daggers left to sell
            if not dagger:
                self.utils.log("INFO", "No daggers left to offer shopkeeper")
                switch_task = True
                break
            daggers_sold += 1
            pyautogui.moveTo(dagger[0] + 6, dagger[1] + 12, 0.15)
            pyautogui.doubleClick()
            sleep(0.5)

        # Confirm the sale
        check_mark = self.user_interface.get_ui_element('checkMark')
        pyautogui.moveTo(check_mark[0] + 5, check_mark[1] + 5, 0.15)
        pyautogui.click()
        sleep(0.5)
        self.utils.log("INFO", F"Sold {daggers_sold} great daggers")

        # Click cancel to leave the window
        cancel = self.user_interface.get_ui_element('cancel')
        pyautogui.moveTo(cancel[0] + 5, cancel[1] + 5, 0.15)
        pyautogui.click()
        sleep(1)

        # Move mouse to a neutral position that won't obstruct template matching
        pyautogui.moveTo(400, 400)

        if switch_task:
            # Find the ingots in the player's backpack
            if self.backpack.get_item('ingot'):
                self.utils.log("INFO", "Ingots still remain, switching task to forging")
                return self.utils.TASKS.forge

            # No ingots and no daggers, back to mining!
            self.utils.log("INFO", "All Great Daggers sold, switching task back to mining")
            return self.utils.TASKS.mine

        # Continue selling daggers
        return self.utils.TASKS.sell
