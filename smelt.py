"""
    This module performs smelting related tasks
    """
from time import sleep
import pyautogui
import cv2
import utilities as utils
from move import Move


class Smelt():
    """
        This class performs smelting related tasks
        """
    def __init__(self, player, game_map):
        self.move = Move(game_map)
        self.player = player

        # Load smelter template
        cold_forge_template = cv2.imread('./inaccessible_tiles/coldForge.png')
        self.cold_forge_template = cv2.cvtColor(
            cold_forge_template, cv2.COLOR_BGR2GRAY)

    def fire_smelter(self):
        """
            Check if the forge has gone cold. If so, fires it
            """
        # Get the smelter
        screenshot = utils.take_screenshot()
        forge = screenshot[152:168, 168:184]

        # Check if the cold forge exists
        result = cv2.matchTemplate(forge, self.cold_forge_template, cv2.TM_CCORR_NORMED)
        max_val = cv2.minMaxLoc(result)[1]

        # Found cold forge, light it and wait
        if max_val > 0.9:
            pyautogui.moveTo(192, 159, 0.15)
            pyautogui.doubleClick()
            sleep(1.5)

    def smelt(self):
        """
            Perform the smelting task
            """
        # Move to the furnace, if already there, nothing happens
        self.move.go_to_furnace()

        # Find the ore in the player's backpack
        ore = self.player.backpack.get_item('ore')
        if not ore:
            utils.log("INFO", "No ore remain, switching task to forging")
            return self.player.TASKS.FORGE

        # Fire the smelter if it is cold
        self.fire_smelter()

        # Smelt the ore
        self.player.backpack.use_item('ore', (176, 161), (8, 6))

        # Continue smelting
        return self.player.TASKS.SMELT
