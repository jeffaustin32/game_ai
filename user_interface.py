
"""
    This module handles everything user interface related
    """
import os
from time import sleep
import cv2
import pytesseract
import pyautogui
from utilities import Utilities

class UserInterface:
    """
        This class handles everything user interface related
        """

    def __init__(self):
        self.utils = Utilities()

        # Load all UI element templates
        self.templates = dict()
        for tile in os.listdir('./ui_elements'):
            tile_template = cv2.imread('./ui_elements/' + tile)
            self.templates[tile.split('.')[0]] = tile_template

    def wait_for_ui_element(self, element, exit_on_fail=True):
        """
            Some elements take time to appear after an event, typically a click, was sent.
            This method will attempt to find a UI element on the screen 10 times. After each
            failed attempt, it will delay 0.5 seconds and try again.

            If the element is not found after 10 attempts, it will either quit the game or
            return false depending on the value of exit_on_fail.

            An example of when to use this method is after clicking on a merchant, the "Buy
            or sell" window can take some time to appear on screen.
            """
        attempts = 0
        element_loc = None
        while attempts < 20:
            # Try and click on the merchant
            element_loc = self.get_ui_element(element, exit_on_fail=False)

            # Found the element
            if element_loc:
                return element_loc

            sleep(0.25)
            attempts += 1

        # Failed to find the UI element after 10 attempts
        if not element_loc and exit_on_fail:
            self.utils.log("SEVERE", F"Failed to find {element} after waiting and searching 20 times")
            self.utils.quit_game()

        # Failed to find element but failure will be handled elsewhere
        return False

    def get_ui_element(self, element, screenshot=None, exit_on_fail=True):
        """
            Find a UI element on the screen
            """
        # Move the mouse so it doesn't obstruct search
        pyautogui.moveTo(400, 400)

        # Get a screenshot
        if screenshot is None:
            screenshot = self.utils.take_screenshot(False)

        # Try to match the template in the screenshot
        result = cv2.matchTemplate(screenshot, self.templates[element], cv2.TM_CCORR_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        # Found the element, return the location
        if max_val > 0.9:
            return max_loc

        # Failed to find the element with high enough confidence
        if not exit_on_fail:
            return False

        # Not finding the element is severe enough to quit the game
        self.utils.log("SEVERE", F"Failed to find {element}, max confidence was {max_val}")
        self.utils.quit_game()

    def get_weight(self):
        """
            Gets the player's current and max weight
            """
        # Find the current and total weight
        screenshot = self.utils.take_screenshot(False)
        weight = self.get_ui_element('weight', screenshot)
        weight = screenshot[weight[1]:(weight[1] + 12), (weight[0] + 40):(weight[0] + 84)]

        # Resize and parse the image to a string
        weight = cv2.resize(weight, (0, 0), fx=3, fy=3)
        weight = cv2.cvtColor(weight, cv2.COLOR_BGR2GRAY)
        weight = cv2.bitwise_not(weight)
        weight = cv2.fastNlMeansDenoising(weight, None, 9, 13)
        _, weight = cv2.threshold(weight, 180, 255, cv2.THRESH_BINARY)
        weight = cv2.blur(weight, (4, 2))

        weight_text = ''
        try:
            weight_text = pytesseract.image_to_string(weight, config=self.utils.TESSERACT_CONF)
        except UnicodeDecodeError:
            self.utils.log("SEVERE", "Tesseract failed to parse player weight from screenshot")
            self.utils.quit_game()

        # Split the equation and calculate the difference
        current_weight, max_weight = weight_text.split("/")[0::1]
        return int(current_weight), int(max_weight)

    def get_health(self):
        """
            Gets the player's current health
            """
        # Reduce the screenshot to include only the player's health
        screenshot = self.utils.take_screenshot(False)
        health = self.get_ui_element('health', screenshot)
        health = screenshot[health[1]:(health[1] + 12), (health[0] + 36):(health[0] + 92)]

        # Resize and parse the image to a string
        health = cv2.resize(health, (0, 0), fx=3, fy=3)
        health = cv2.cvtColor(health, cv2.COLOR_BGR2GRAY)
        health = cv2.bitwise_not(health)
        health = cv2.fastNlMeansDenoising(health, None, 9, 13)
        _, health = cv2.threshold(health, 180, 255, cv2.THRESH_BINARY)
        health = cv2.blur(health, (4, 2))

        health_text = ''
        try:
            health_text = pytesseract.image_to_string(health, config=self.utils.TESSERACT_CONF)
        except UnicodeDecodeError:
            self.utils.log("SEVERE", "Tesseract failed to parse player health from screenshot")
            self.utils.quit_game()

        # Split the equation and calculate the difference
        current = health_text.split("/")[0]
        return int(current)
