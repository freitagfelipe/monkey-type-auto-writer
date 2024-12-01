import time
import sys
import os
from loguru import logger
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver

log_level = os.environ["LOG_LEVEL"] if "LOG_LEVEL" in os.environ else "INFO"
logger.configure(handlers=[{"sink": sys.stderr, "level": log_level}])


def get_text(driver: WebDriver, ignore_first_word: bool) -> str:
    html = driver.page_source

    soup = BeautifulSoup(html, "html.parser")

    word_divs = soup.select("div.word:not(.typed)")

    words = []

    for idx, word_div in enumerate(word_divs):
        if ignore_first_word and idx == 0:
            continue

        letters = []

        for letter in word_div.find_all("letter"):
            letters.append(letter.text)

        words.append("".join(letters))

    return " ".join(words)


def get_game_mode(driver: WebDriver) -> str:
    html = driver.page_source

    soup = BeautifulSoup(html, "html.parser")

    mode_button = soup.select_one("div button.active")

    if mode_button is None:
        logger.error("Game mode button not found")

        driver.close()

        exit()

    game_mode = mode_button.get("mode")

    if not isinstance(game_mode, str):
        logger.critical("Game mode attribute is not an instance of str")

        exit()

    return game_mode


def is_in_game(driver: WebDriver) -> bool:
    logger.trace("Checking if is in game")

    html = driver.page_source

    soup = BeautifulSoup(html, "html.parser")

    tag = soup.select_one("div#testConfig:not(.invisible)")

    return tag is not None


def type_text(
    driver: WebDriver, text: str, type_interval: float, is_time_game_mode: bool
) -> bool:
    logger.debug("Starting typing text")

    body = driver.find_element(By.TAG_NAME, "body")

    for char in text:
        if is_time_game_mode and not is_in_game(driver):
            logger.debug("Exiting type text prematurely")

            return False

        body.send_keys(char)

        time.sleep(type_interval)

    return True


def main():
    driver = webdriver.Firefox()
    driver.get("https://monkeytype.com")

    driver.find_element(By.CSS_SELECTOR, "button.rejectAll").click()

    config_interval = float(
        os.environ["CONFIG_INTERVAL"] if "CONFIG_INTERVAL" in os.environ else 10
    )

    logger.info(
        f"You have {config_interval} seconds to change and configure the game mode and accept the cookies"
    )

    time.sleep(config_interval)

    game_mode = get_game_mode(driver)

    if game_mode == "zen":
        logger.error("Game mode not allowed")

        driver.close()

        exit()

    type_interval = (
        float(os.environ["TYPE_INTERVAL"]) if "TYPE_INTERVAL" in os.environ else 0.05
    )

    logger.info(f"The interval between letters is {type_interval}")

    if game_mode == "words":
        text = get_text(driver, False)

        logger.trace(f"Text to type: {text}")

        type_text(driver, text, type_interval, False)
    else:
        get_text_counter = 0

        while True:
            if game_mode == "time" and not is_in_game(driver):
                break

            text = get_text(driver, True if get_text_counter >= 1 else False)

            logger.trace(f"Text to type: {text}")

            if len(text) == 0:
                break

            if get_text_counter >= 1:
                text = f" {text}"

            if not type_text(driver, text, type_interval, game_mode == "time"):
                break

            get_text_counter += 1

    logger.success("Finished the challenge")


if __name__ == "__main__":
    main()
