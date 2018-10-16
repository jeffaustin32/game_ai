"""
    An AI agent that will explore its environment and perform certain tasks (mining, smelting, forging, and buying/selling items)
    """
import sys
from time import sleep
import traceback
import cv2
import pyautogui
from game_map import GameMap
from utilities import Utilities
from user_interface import UserInterface
from player import Player

# Set defaults
task = Player.TASKS.MINE
if len(sys.argv) > 1:
    task = Player.TASKS[sys.argv[1].upper()]

# Initialize classes
game_map = GameMap()
player = Player(game_map, task)
utils = Utilities()
user_interface = UserInterface()

n = 3
for i in range(n):
    # Wait
    print(F"Launching game in {n - i} seconds...")
    sleep(1)

utils.log("====", "====================================================")
utils.log("====", "Starting setup...")
utils.log("SETUP", F"Default task set to {task}")

# Find blocking window in screenshot
screenshot = utils.take_screenshot(False)
result = cv2.matchTemplate(screenshot, user_interface.templates['sponsored'], cv2.TM_CCORR_NORMED)
_, max_val, _, max_loc = cv2.minMaxLoc(result)

# Found the blocking window window with high confidence
if max_val > 0.9:
    click_at = (max_loc[0] + 428, max_loc[1] + 144)
    utils.log("SETUP", "Closed blocking window")
    pyautogui.moveTo(click_at[0], click_at[1], 0.15)
    pyautogui.click()
    sleep(5)

# Bring game to foreground
utils.bring_game_to_foreground()

# Detect environment
screenshot = utils.take_screenshot()
game_map.update_player_position(screenshot)
utils.log("SETUP", F"Player location initialized")

game_map.update_map()
utils.log("SETUP", "Field of view mapped")

# Setup complete, starting ai
utils.log("SETUP", "Setup complete")
utils.log("====", "====================================================")
try:
    while utils.bring_game_to_foreground():
        player.perform_task()   
except Exception as exception:
    utils.log("SEVERE", exception)
    utils.log("SEVERE", traceback.format_exc())
    utils.quit_game()
