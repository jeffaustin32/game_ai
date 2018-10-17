"""
    This module handles everything backpack related
    """
import os
import cv2
import numpy as np
import pyautogui
import utilities as utils


class Backpack:
    """
        This class handles everything backpack related
        """
    # Row 1
    SEXTANT_LOC = (18, 40)
    PICKAXE_LOC = (44, 40)
    POTION_LOC = (70, 40)
    HAMMER_LOC = (96, 40)
    # Row 2
    ORE_LOC = (18, 66)
    INGOT_LOC = (44, 66)
    GOLD_LOC = (70, 66)
    GEM_LOC = (96, 66)
    # Row 3
    # Free space = (18, 92)
    # Free space = (44, 92)
    # Free space = (70, 92)
    DAGGER_LOC = (96, 92)

    def __init__(self):
        # Load all backpack item templates
        self.item_templates = dict()
        for item in os.listdir('./backpack_items'):
            item_template = cv2.imread('./backpack_items/' + item)
            self.item_templates[item.split('.')[0]] = item_template

        # Load backpack template
        self.backpack_template = cv2.imread('./ui_elements/backpack.png')

    def get_backpack(self):
        """
            Find and return the player's backpack. Returns a tuple
            containing the backpack and the coordinates
            """
        # Find backpack in screenshot
        screenshot = utils.take_screenshot(False)
        result = cv2.matchTemplate(screenshot, self.backpack_template, cv2.TM_CCORR_NORMED)
        _, max_val, _, backpack_loc = cv2.minMaxLoc(result)

        # Failed to find the backpack with high confidence
        if max_val < 0.9:
            utils.log("SEVERE", "Unable to find backpack in screenshot")
            utils.quit_game()

        # Restrict screenshot to just include the player's backpack
        #backpack_loc = (backpack_loc[0] + 11, backpack_loc[1] + 33)
        backpack = screenshot[(backpack_loc[1]): (backpack_loc[1] + 144),
                              (backpack_loc[0]): (backpack_loc[0] + 128)]

        return (backpack, backpack_loc)

    def move_item(self, item, move_to, offset=(5, 5)):
        """
            Move an item to a different location in the backpack. The search
            for the item will always exclude a 5 pixel margin around the
            destination so the same item isn't moved repeatedly.
            """
        # Move mouse to a neutral position that won't obstruct template matching
        pyautogui.moveTo(400, 400)

        # Get the player's backpack
        backpack, backpack_loc = self.get_backpack()

        # Find all instances of the item in the backpack
        res = cv2.matchTemplate(backpack, self.item_templates[item], cv2.TM_CCORR_NORMED)

        # Only consider high confidence matches
        threshold = 0.9
        loc = np.where(res >= threshold)

        # For each match, move it if it isn't already in the correct area
        for item_loc in zip(*loc[::-1]):
            # Skip items already in the correct area
            if move_to[0] - 12 < item_loc[0] < move_to[0] + 14 and move_to[1] - 12 < item_loc[1] < move_to[1] + 14:
                continue

            # Drag and drop the item to the correct area
            pyautogui.moveTo((backpack_loc[0] + item_loc[0] + offset[0]),
                             (backpack_loc[1] + item_loc[1] + offset[1]), 0.15)
            pyautogui.dragTo((backpack_loc[0] + move_to[0]),
                             (backpack_loc[1] + move_to[1]),
                             2, pyautogui.easeOutQuad, button='left')

        # Move mouse to a neutral position that won't obstruct template matching
        pyautogui.moveTo(400, 400)

    def get_item(self, item, exit_on_failure=False):
        """
            Find an item in the player's backpack and return it's pixel coordinates
            """
        # Get the player's backpack
        backpack, backpack_loc = self.get_backpack()

        # Search the backpack for the item
        result = cv2.matchTemplate(backpack, self.item_templates[item], cv2.TM_CCORR_NORMED)
        _, max_val, _, item_loc = cv2.minMaxLoc(result)

        # Failed to find item in backpack with high confidence
        if max_val < 0.9:
            if exit_on_failure:
                utils.log("SEVERE", F"Unable to find {item} in backpack. max_val: {max_val:3.2f}")
                utils.quit_game()
            else:
                return False

        return (backpack_loc[0] + item_loc[0], backpack_loc[1] + item_loc[1])

    def use_item(self, item, use_at=None, offset=(6, 6), exit_on_failure=False):
        """
            Find an item in the player's backpack, use it, and check/resolve any macro challenge
            """
        # Get the coordinates of the item
        item_loc = self.get_item(item, exit_on_failure)

        if not item_loc:
            return False

        # Double click on the item
        pyautogui.moveTo((item_loc[0] + offset[0]), (item_loc[1] + offset[1]), 0.15)
        pyautogui.doubleClick()

        # Check if a macro challenge occurred
        utils.resolve_macro_check()

        if use_at is None:
            return True

        # Use the item
        pyautogui.moveTo(use_at[0], use_at[1], 0.15)
        pyautogui.click()

        # Move mouse to a neutral position that won't obstruct template matching
        pyautogui.moveTo(400, 400)
        return True
