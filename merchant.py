"""
    This module handles all merchant related actions
    """
from enum import Enum
from time import sleep
import numpy as np
import pyautogui
from utilities import Utilities
from backpack import Backpack
from user_interface import UserInterface

class Merchant:
    """
        This class handles all merchant related actions including
        buying and selling as well as depositing gold
        """
    MERCHANTS = Enum('Merchants', 'WEAPONS, BLACKSMITH, POTIONS, ITEMS, BANKER')

    def __init__(self, game_map, move):
        self.user_interface = UserInterface()
        self.utils = Utilities()
        self.backpack = Backpack()
        self.move = move
        self.game_map = game_map

    def move_to_merchant(self, merchant_type):
        """
            Move to a merchant
            """
        # Move to the appropriate merchant
        merchant_tile = None
        # Weapons shopkeeper
        if merchant_type == self.MERCHANTS.WEAPONS:
            merchant_tile = self.game_map.TILES.WEAPON_SHOPKEEPER.value
            self.move.move_to(self.move.WEAPON_SHOPKEEPER)
        # Blacksmith
        elif merchant_type == self.MERCHANTS.BLACKSMITH:
            merchant_tile = self.game_map.TILES.BLACKSMITH.value
            self.move.move_to(self.move.FURNACE)
        # Potions shopkeeper
        elif merchant_type == self.MERCHANTS.POTIONS:
            merchant_tile = self.game_map.TILES.POTIONS_SHOPKEEPER.value
            self.move.move_to(self.move.POTIONS_SHOPKEEPER)
        # Items shopkeeper
        elif merchant_type == self.MERCHANTS.ITEMS:
            merchant_tile = self.game_map.TILES.ITEM_SHOPKEEPER.value
            self.move.move_to(self.move.ITEMS)
        # Banker
        elif merchant_type == self.MERCHANTS.BANKER:
            merchant_tile = self.game_map.TILES.BANKER.value
            self.move.move_to(self.move.BANKER)
        else:
            self.utils.log("SEVERE", "Invalid merchant_type supplied to move_to_merchant")
            self.utils.quit_game()

        # Update map so merchant's position will be current
        self.game_map.update_map()

        # Get the 5x5 matrix of tiles surrounding the player
        clickable_tiles = self.game_map.game_map[
            (self.game_map.player_position[0] - 2): (self.game_map.player_position[0] + 3),
            (self.game_map.player_position[1] - 2): (self.game_map.player_position[1] + 3)
        ]

        # Find the index where merchant is located
        merchant_indices = np.argwhere(clickable_tiles == merchant_tile)
        if merchant_indices.size == 0:
            return False

        # Get the merchant index
        merchant_index = merchant_indices[0]

        # Calculate where to click (2 because player is in center of 5x5 matrix that is 0 indexed)
        x_coord = merchant_index[0] - 2
        y_coord = merchant_index[1] - 2
        return (176 + (x_coord * 16), 176 + (y_coord * 16))

    def click_on_merchant(self, merchant_type):
        """
            Move to the specified merchant type and double click them
            """
        # Move to the merchant
        attempts = 0
        while attempts < 10:
            # Find where to click on the merchant
            click_at = self.move_to_merchant(merchant_type)

            if not click_at:
                continue

            # Click on the merchant
            pyautogui.moveTo(click_at[0], click_at[1], 0.15)
            pyautogui.doubleClick()

            # Check that the buy or sell window was opened
            buy_or_sell = self.user_interface.wait_for_ui_element('buyOrSell', exit_on_fail=False)

            # Buy and sell window is open
            if buy_or_sell:
                return True
            
            # Still not open
            sleep(1)
            attempts += 1

        # Never opened
        return False


    def open_merchant_window(self, merchant_type):
        """
            Open the "Buy or Sell" window or return False is unable to
            """
        attempts = 0
        while attempts < 10:
            # Try and click on the merchant
            window_is_open = self.click_on_merchant(merchant_type)

            if window_is_open:
                return window_is_open

            sleep(1)
            attempts += 1

        return False

    def buy_item(self, item, merchant_type):
        """
            Move to a merchant and buy an item
            """
        # Open the "Buy or Sell" window
        buy_or_sell = self.open_merchant_window(merchant_type)
        if not buy_or_sell:
            self.utils.log("SEVERE", F"Failed to click on {merchant_type} and open 'Buy or Sell' after 10 attempts")
            self.utils.quit_game()

        # Click the buy button
        buy_button = self.user_interface.wait_for_ui_element('buy')
        pyautogui.moveTo(buy_button[0] + 10, buy_button[1] + 10, 0.15)
        pyautogui.click()

        # Wait for the buy menu to open
        self.user_interface.wait_for_ui_element('buyMenu')

        # Find the item to buy
        item_loc = self.user_interface.wait_for_ui_element(item)
        pyautogui.moveTo(item_loc[0] + 6, item_loc[1] + 6, 0.15)
        pyautogui.doubleClick()

        # Confirm the sale
        check_mark = self.user_interface.wait_for_ui_element('checkMark')
        pyautogui.moveTo(check_mark[0] + 5, check_mark[1] + 5, 0.15)
        pyautogui.click()

        # Click cancel to leave the window
        cancel = self.user_interface.wait_for_ui_element('cancel')
        pyautogui.moveTo(cancel[0] + 5, cancel[1] + 5, 0.15)
        pyautogui.click()

        pyautogui.moveTo(400, 400)
        self.utils.log("INFO", F"Bought a {item}")

    def sell_item(self, item, merchant_type):
        """
            Move to a merchant and sell an item
            """
        # Open the "Buy or Sell" window
        buy_or_sell = self.open_merchant_window(merchant_type)
        if not buy_or_sell:
            self.utils.log("SEVERE", F"Failed to click on {merchant_type} and open 'Buy or Sell' after 10 attempts")
            self.utils.quit_game()

        # Click the sell button
        sell_button = self.user_interface.wait_for_ui_element('sell')
        pyautogui.moveTo(sell_button[0] + 10, sell_button[1] + 10, 0.15)
        pyautogui.click()

        # Wait for the sell menu to open
        self.user_interface.wait_for_ui_element('sellMenu')

        # Offer up to 12 items
        items_sold = 0
        for _ in range(12):
            # Move the cursor away so it will register an "hover" event when move back
            pyautogui.moveTo(330, 206)

            # Find a item to sell
            item_loc = self.user_interface.get_ui_element(item, exit_on_fail=False)

            # No item_locs left to sell
            if not item_loc:
                self.utils.log("INFO", F"No {item} left to offer shopkeeper")
                break

            items_sold += 1
            pyautogui.moveTo(item_loc[0] + 6, item_loc[1] + 12, 0.15)
            pyautogui.doubleClick()
            sleep(0.5)

        # Confirm the sale
        check_mark = self.user_interface.wait_for_ui_element('checkMark')
        pyautogui.moveTo(check_mark[0] + 5, check_mark[1] + 5, 0.15)
        pyautogui.click()

        # Click cancel to leave the window
        cancel = self.user_interface.wait_for_ui_element('cancel')
        pyautogui.moveTo(cancel[0] + 5, cancel[1] + 5, 0.15)
        pyautogui.click()

        self.utils.log("INFO", F"Sold {items_sold} {item}(s)")
        return items_sold


    # def deposit_gold(self):
    #     """
    #         Move to a banker and deposit all but 1,000 gold to keep as float
    #         """
    #     click_at = self.move_to_merchant(self.MERCHANTS.BANKER)
    #     return click_at