"""
    This module performs mining related tasks
    """
import cv2
from utilities import Utilities
from move import Move
from user_interface import UserInterface
from merchant import Merchant


class Mine():
    """
        This class performs mining related tasks
        """

    def __init__(self, player, game_map):
        self.utils = Utilities()
        self.move = Move(game_map)
        self.user_interface = UserInterface()
        self.merchant = Merchant(game_map, self.move)
        self.player = player
        self.mining_coords = None

        # Load templates
        self.templates = dict()
        template = cv2.imread('./ui_elements/nothingToMine.png')
        self.templates['nothingToMine'] = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        template = cv2.imread('./ui_elements/cannotMineThere.png')
        self.templates['cannotMineThere'] = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    def mine(self):
        """
            Mine ore until weight is nearing full.  If player destroys all pickaxes,
            another will be purchased and mining will continue.
            """
        # Get player's weight
        if self.player.is_weight_below_threshold(50):
            self.utils.log("INFO", F"Weight is below threshold, switching task to smelting")
            return self.player.TASKS.SMELT

        # No pickaxes left, buy one
        if not self.player.backpack.get_item('pickaxe'):
            self.merchant.buy_item('pickaxe', self.merchant.MERCHANTS.BLACKSMITH)
            self.mining_coords = self.move.go_to_mine()
        
        # First time mining, move to the mining region
        if self.mining_coords is None:
            self.mining_coords = self.move.go_to_mine()

        # Check if there is still ore to mine here
        screenshot = self.utils.take_screenshot()
        self.resolve_nothing_to_mine(screenshot)
        self.resolve_cannot_mine(screenshot)

        # Use pickaxe
        self.player.backpack.use_item('pickaxe', (self.mining_coords[0], self.mining_coords[1]), (9, 4))

        # Continue mining
        return self.player.TASKS.MINE

    def resolve_cannot_mine(self, screenshot):
        """
            Examines current screenshot to see if "You cannot mine there."
            message has been displayed. If so, finds a rock to mine from and moves.
            """
        # Find a new rock to mine
        if self.check_last_message_for('cannotMineThere', screenshot):
            self.utils.log("INFO", "Cannot mine there")
            self.mining_coords = self.move.go_to_mine()

    def resolve_nothing_to_mine(self, screenshot):
        """
            Examines current screenshot to see if "There is nothing to mine here."
            message has been displayed. If so, finds a new rock to mine from and moves.
            """
        # Find a new rock to mine
        if self.check_last_message_for('nothingToMine', screenshot):
            self.utils.log("INFO", "Nothing to mine here")
            self.mining_coords = self.move.go_to_mine()

    def check_last_message_for(self, message, screenshot):
        """
            Check if the specified message was appended to the chat window
            """
        # Trim screenshot to just show last message
        screenshot = screenshot[450: 480, 0: 170]

        # Find macro template
        result = cv2.matchTemplate(screenshot, self.templates[message], cv2.TM_CCORR_NORMED)
        max_val = cv2.minMaxLoc(result)[1]

        # Message is displayed
        if max_val > 0.9:
            return True

        # No message
        return False
