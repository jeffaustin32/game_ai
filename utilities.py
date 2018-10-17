"""
    A collection of useful utility functions
    """
import datetime
from time import sleep
import numpy as np
import pyautogui
import cv2
import pytesseract

NORMALIZATION_CONSTANT = 3156
TESSERACT_CONF = "--psm 6 -c tessedit_char_whitelist=0123456789"

def log(severity, string):
    """
        Prints a log message prepended with the date and time
        """
    output = F"{datetime.datetime.now()}: {severity}: {string}"
    print(output)

    with open("log.txt", "a") as log_file:
        log_file.write(output+"\n")

def bring_game_to_foreground():
    """
        This method will ensure game is in the foreground
        """
    screenshot = take_screenshot(False)

    # Look for game icon
    icon_template = cv2.imread('./ui_elements/icon.png')
    result = cv2.matchTemplate(screenshot, icon_template, cv2.TM_CCORR_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    # Found game icon with high confidence
    if max_val > 0.9:
        click_at = (max_loc[0] + 12, max_loc[1] + 12)
        log("INFO", F"Found icon, launching game")
        pyautogui.moveTo(click_at[0], click_at[1], 0.15)
        pyautogui.click()
        sleep(1)

        # If backpack is found then the game is open
        screenshot = take_screenshot(False)
        backpack_template = cv2.imread('./ui_elements/backpack.png')
        result = cv2.matchTemplate(screenshot, backpack_template, cv2.TM_CCORR_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)

        errors = 0
        while max_val < 0.9:
            sleep(1)
            # Check for backpack. If foundmeans game is open
            screenshot = take_screenshot(False)
            result = cv2.matchTemplate(screenshot, backpack_template, cv2.TM_CCORR_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            errors += 1

            # Game should open in less than 10 seconds
            if errors == 10:
                quit_game()

    # Look for CMD icon
    cmd_template = cv2.imread('./ui_elements/cmd.png')
    result = cv2.matchTemplate(screenshot, cmd_template, cv2.TM_CCORR_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    # Found CMD icon with high confidence
    if max_val > 0.9:
        click_at = (max_loc[0] + 12, max_loc[1] + 12)
        log("INFO", F"Found CMD icon, game must have closed")
        raise SystemExit

    # Game must be open
    return True

def quit_game():
    """
        Quitting will ensure game is in the foreground
        then send the quit command and end the python script
        """
    bring_game_to_foreground()
    log("SEVERE", "Quitting game\n\n\n\n")
    pyautogui.hotkey('alt', 'x')
    raise SystemExit

def take_screenshot(grayscale=True):
    """
        Returns a screenshot of the game
        """
    pyautogui.screenshot("screenshot.png")
    screenshot = cv2.imread("screenshot.png")
    if grayscale:
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    return screenshot

def get_macro_window(image):
    # Load macro template and convert it to grayscale
    template = cv2.imread('./ui_elements/macro.png')
    template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    # Find macro template
    result = cv2.matchTemplate(image, template, cv2.TM_CCORR_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    # Unlikely there is a macro check occurring
    if max_val < 0.9:
        return None
    
    log("INFO", "A macro challenge is occurring")
    return max_loc

def resolve_macro_check():
    """
        Checks for and resolves a macro challenge
        """
    # Sleep for a moment to give the window time to open
    sleep(0.5)

    # Move mouse to a neutral position that won't obstruct template matching
    pyautogui.moveTo(400, 400)
    image = take_screenshot()

    attempts = 0
    window_loc = get_macro_window(image)
    while not window_loc is None:
        # A macro check is occurring, find the question
        question = image[window_loc[1]:(window_loc[1] + 12),
                            (window_loc[0] + 81):(window_loc[0] + 133)]

        # Parse the macro question from the image
        try:
            # Resize and parse the image to a string
            question = cv2.resize(question, (0, 0), fx=3, fy=3)
            question = cv2.blur(question, (3, 1))
            question = cv2.bitwise_not(question)
            question = pytesseract.image_to_string(question, config=TESSERACT_CONF)
        except UnicodeDecodeError:
            log("SEVERE", "Tesseract failed to parse macro question from screenshot")
            quit_game()

        # Split the equation on the equals and evaluate it
        expression, consequent = question.split('=')[0::1]
        term1, term2 = expression.split('+')[0::1]

        # Load the template of the button to press
        button_template = 'no.png'
        if int(term1) + int(term2) == int(consequent):
            button_template = 'yes.png'

        # Load button template and convert it to grayscale
        button_template = cv2.imread('./ui_elements/' + button_template)
        button_template = cv2.cvtColor(button_template, cv2.COLOR_BGR2GRAY)

        # Find button template
        result = cv2.matchTemplate(image, button_template, cv2.TM_CCORR_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        # Found the button with high confidence
        if max_val > 0.9:
            # Click the "yes" or "no" button to resolve the macro check
            pyautogui.moveTo(max_loc[0] + 14, max_loc[1] + 7, 0.15)
            pyautogui.click()
            sleep(1)

        # If macro resolution fails after this many attempts, something is clearly wrong
        attempts += 1
        if attempts == 10:
            log("SEVERE", F"Failed to resolve macro after {attempts} attempts")
            quit_game()

        # Check for the window again to confirm it was closed
        image = take_screenshot()
        window_loc = get_macro_window(image)
        log("INFO", "Resolved macro challenge")

        # Move mouse to a neutral position that won't obstruct template matching
        pyautogui.moveTo(400, 400)

def debug_show_image(image):
    """
        Shows a picture for debugging purposes
        """
    image = cv2.resize(image, (0, 0), fx=5, fy=5)
    cv2.imshow("Result", image)
    cv2.waitKey(0)

def debug_print_matrix(matrix):
    """
        Prints entire numpy matrix for debugging purposes
        """
    np.set_printoptions(threshold=np.inf)
    print(matrix)
