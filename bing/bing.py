# Script to perform random searches on Bing for earning Daily Microsoft Reward Points
# Make sure to monitor progress intially when account created (custom interface and edge cases)

from __future__ import annotations

import argparse
import os
import platform as pl
import re
import time
import traceback
from collections import OrderedDict
from functools import wraps
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Type, Union
from urllib.parse import quote, unquote_plus, urlsplit, urlunsplit

import numpy as np
import pandas as pd
import yaml
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement

# Set your config variables here
PARENT_DIR = "~/Documents/bing/"
CHROMEDRIVER_PATH = "~/AppData/Local/Programs/Python/Python38-32/chromedriver.exe"  # Only required for Windows
EXTRA_DELAY = 1
MAX_RETRIES = 5

# Set URLs here
BING_URL = "https://www.bing.com/"
REWARDS_URL = "https://account.microsoft.com/rewards/"
POINTS_BREAKDOWN_URL = "https://account.microsoft.com/rewards/pointsbreakdown"
COMMUNITY_URL = "https://account.microsoft.com/rewards/community/"

_Credentials = Tuple[Dict[int, List[str]], Dict[int, List[str]]]
_Cache = Union[str, int]
_CacheDict = Dict[_Cache, _Cache]
_StrFloatDict = Dict[str, float]
_ResultsDict = Dict[str, Union[int, _StrFloatDict]]


class RewardsCache:
    def __init__(self):
        """
        Initialize cache dictionaries for
        saving reward types and correct answers.
        """
        self.reward_types: Dict[str, str] = {}
        self.correct_answers: Dict[str, _CacheDict] = {}

    def save_reward_type(self, reward_text: str, reward_type: str) -> None:
        """
        Save the reward type of an item (indexed by its text).
        """
        self.reward_types[reward_text] = reward_type

    def get_reward_type(self, reward_text: str) -> str:
        """
        Load the reward type of an item
        using its text as the index.
        """
        reward_type = self.reward_types.get(reward_text)
        if reward_type is not None:
            print(f"Found existing reward_type ({reward_type}): {reward_text}")
            return reward_type
        return self.identify_reward_type(reward_text)

    def identify_reward_type(self, reward_text: str) -> str:
        """
        Identify the reward type of a given item.
        Store the identified type in a cache dict
        indexed by the item text for future lookup.
        """
        reward_type = "unidentifiable"  # Initialize with unidentifiable item reward type
        for key, value in REWARD_TYPE_DICT.items():
            match_text = value.get("reward_type")
            if (match_text is None and key in reward_text) or (
                match_text is not None and any([text in reward_text for text in match_text])
            ):
                reward_type = key
                break

        # Set `reward_type` for lookup later
        self.save_reward_type(reward_text, reward_type)

        return reward_type

    def save_answer(self, reward_text: str, cache_dict: _CacheDict) -> None:
        """
        Save correct answer to cache if the reward type
        of answer is one that requires/supports it.

        :param cache_dict: Dictionary with keys as the
                           query by which lookup will be
                           be performed at loading time
                           (e.g. question text)
        """
        reward_type = self.reward_types[reward_text]
        if reward_type in QUIZZES_TO_CACHE:
            for query, value in cache_dict.items():
                if reward_text not in self.correct_answers:
                    self.correct_answers[reward_text] = {}
                self.correct_answers[reward_text].update({query: value})
        else:
            PRINT_WARNING(
                f"`save_answer()` was called but rewards of type {reward_type} don't require/support caching."
            )

    def load_answer(self, reward_text: str, query: _Cache) -> _Cache:
        """
        Load correct answer from cache.
        Return None if not available.

        :param query: Query used as key using which
                      lookup is performed to get
                      correct answer
        """
        if reward_text in self.correct_answers:
            return self.correct_answers[reward_text].get(query)
        return None


def check_if_windows() -> bool:
    """
    Return True if current OS is
    Windows- or False if UNIX-based.
    """
    platform = pl.system()
    if platform not in {"Darwin", "Linux", "Windows"}:
        raise Exception(f"Unknown OS '{platform}'")
    is_windows = platform == "Windows"
    return is_windows


def get_printing_functions() -> Iterable[Callable[[str], None]]:
    """
    Generate printing functions that are properly
    color formatted (if `termcolor` is available).
    """

    def _get_function(color: str) -> Callable[[str], None]:
        """
        Return color formatted printing function.
        """
        return lambda s: print(colored(s, color))

    try:
        from termcolor import colored

        print_id = _get_function("green")
        print_warning = _get_function("red")
        print_success = _get_function("cyan")
    except ImportError:
        print("`termcolor` not available. Printing regularly.")
        print_id = print_warning = print_success = print

    return print_id, print_warning, print_success


def retry_if_exception(
    max_retries: int,
    exception_type: Type[Exception],
    starting_error_message: Optional[str] = "",
    sleep_time: Optional[float] = None,
) -> Callable:
    """
    Decorator for retrying failed function after every `sleep_time`
    seconds if exception type and exception message (if provided)
    match `exception_type` and `starting_error_message` respectively.

    :param max_retries: Max number of retries
    :param exception_type: Exception type (e.g. RuntimeError)
    :param starting_error_message: Starting part of exception error message
    :param sleep_time: Seconds to wait before next retry
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exception_type as e:
                    error_message = str(e)
                    if error_message.startswith(starting_error_message) and attempt < max_retries:
                        traceback.print_exc()
                        if sleep_time is not None:
                            time.sleep(sleep_time)
                        PRINT_WARNING(
                            f"Attempt {attempt+1}: Retrying because {func.__name__} has @retry_if_exception decorator on it."
                        )
                        continue
                    else:
                        raise
                else:
                    raise

        return wrapper

    return decorator


def parse_args() -> argparse.Namespace:
    """
    Return parsed arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--credentials-file",
        dest="credentials_file",
        default="credentials.yaml",
        help="yaml file comprising credentials",
    )
    parser.add_argument(
        "--transfers-file",
        dest="transfers_file",
        default="transfer_points.yaml",
        help="yaml file comprising transfer accounts",
    )
    parser.add_argument("--usernames", dest="usernames", nargs="+", help="list of usernames")
    parser.add_argument(
        "--groups", dest="username_groups", type=int, nargs="+", help="Username groups; choices = 1 | 2 | 3"
    )
    parser.add_argument("--no-search", action="store_true", help="Don't do daily searches")
    parser.add_argument("--no-rewards", action="store_true", help="Don't collect daily/more rewards")
    parser.add_argument("--only-points", action="store_true", help="Only get points tally")
    parser.add_argument("--headless", dest="headless", action="store_true", help="run Chrome in headless mode")
    parser.add_argument("--debug", action="store_true", help="Set breakpoint after logging in")
    parser.add_argument("--delay", dest="extra_delay", type=float, help="Extra wait delay to add (seconds)")
    parser.add_argument("--transfer-points", action="store_true", help="Transfer points within each community")
    args = parser.parse_args()

    if args.only_points:  # Disable unnecessary options
        args.no_search = args.no_rewards = args.headless = True

    assert not (args.headless and args.transfer_points), "Points transfer cannot be performed in headless mode."

    # Override extra delay if provided
    if args.extra_delay:
        global EXTRA_DELAY
        EXTRA_DELAY = args.extra_delay

    return args


def get_regexes() -> Dict[str, re.Pattern]:
    """
    Get a dictionary of all compiled regexes.
    """
    regexes = {
        "points": re.compile(r"(\d+)\s?(/|of)\s?(\d+)", re.IGNORECASE),
        "points_per_search": re.compile(r"(\d+) point[s]{,1} per search", re.IGNORECASE),
        "transfer_points": re.compile(
            r"you can give ([0-9]{1,3}(,[0-9]{3})*(\.[0-9]+)?) more point[s]{,1} this month", re.IGNORECASE
        ),
        "available_points": re.compile(r"^([0-9]{1,3}(,[0-9]{3})*(\.[0-9]+)?)\s+available point[s]{,1}", re.IGNORECASE),
    }
    return regexes


def get_chrome_kwargs(args: argparse.Namespace) -> Dict[str, Options]:
    """
    Return the required chrome arguments.
    """
    options = Options()

    if args.headless:  # Run headless
        options.add_argument("--headless")

    if IS_WINDOWS:  # Add chromedriver path
        options.add_argument(f"executable_path={CHROMEDRIVER_PATH}")

    chrome_kwargs = {"options": options}
    return chrome_kwargs


def click(element: WebElement) -> None:
    """
    Attempt performing a clicking action
    using 3 different methods. Each has
    its own failure cases; this method
    is written with the intention that
    at least one of them work.
    """
    try:
        # Regular click
        element.click()
    except:
        try:
            # Click using ActionChains
            ActionChains(BROWSER).move_to_element(element).click(element).perform()
        except:
            # Click using JS
            BROWSER.execute_script("arguments[0].click();", element)


def delay(seconds: float) -> None:
    """
    Time delay of `seconds` plus an added
    `EXTRA_DELAY` seconds across the board
    to account for slow internet
    """
    time.sleep(seconds + EXTRA_DELAY + np.random.normal(0, 0.1))  # Add small random noise to emulate human behavior


def reload_page() -> None:
    """
    Refresh a page (and add a small delay).
    """
    BROWSER.get(BROWSER.current_url)
    delay(1)


def get_word_list() -> List[str]:
    """
    Read (download first if required) the
    list of words in current dictionary.
    """
    # Get word list from url and save it locally if not present
    word_list_path = get_file_path(PARENT_DIR, "word_list.txt")
    if not os.path.exists(word_list_path):
        word_list_url = "https://svnweb.freebsd.org/csrg/share/dict/words?view=co&content-type=text/plain"
        import requests

        response = requests.get(word_list_url)
        words = response.content.splitlines()
        words = [str(word.decode("utf8")).strip() for word in words if len(word) > 3]
        with open(word_list_path, "w+") as f:
            for item in words:
                f.write(f"{item}\n")
    else:
        # Load word list from local storage
        with open(word_list_path, "r") as f:
            words = f.readlines()
    return words


@retry_if_exception(MAX_RETRIES, Exception)
def log_in(username: str, password: str) -> None:
    """
    Login to Microsoft account.
    """
    BROWSER.get("https://login.live.com/")
    delay(1)
    BROWSER.find_element_by_id("i0116").send_keys(username)
    click(BROWSER.find_element_by_id("idSIButton9"))
    delay(1)
    BROWSER.find_element_by_id("i0118").send_keys(password)
    click(BROWSER.find_element_by_id("idSIButton9"))
    delay(1)


def load_credentials_file(file_name: str) -> _Credentials:
    """
    Load the credentials file comprising all
    Microsoft accounts for which the script
    is to be run.
    """
    # Load usernames and (preferably common) password(s) for Microsoft login
    credentials_dict = load_yaml(PARENT_DIR, file_name)

    usernames_dict, passwords_dict = {}, {}
    for group, credentials in credentials_dict.items():
        # Set usernames
        emails = credentials["emails"]
        assert isinstance(emails, list)
        usernames_dict[group] = emails

        # Set passwords
        passwords = credentials["passwords"]
        # If string, it's assumed that it's a common password
        # and expanded to the length of the usernames
        if isinstance(passwords, str):
            passwords_dict[group] = [passwords] * len(credentials["emails"])
        else:  # Otherwise individual passwords must be specified
            assert isinstance(passwords, list) and len(passwords) == len(credentials["emails"])
            passwords_dict[group] = passwords

    assert list(usernames_dict.keys()) == list(passwords_dict.keys())
    return usernames_dict, passwords_dict


def get_bing_credentials(
    credentials: _Credentials,
    usernames: Optional[List[str]] = None,
    username_groups: Optional[List[int]] = None,
) -> Tuple[List[str], List[str]]:
    """
    Load credentials and return
    in the required format.
    """
    # Get usernames and passwords dicts
    usernames_dict, passwords_dict = credentials

    # Run only for provided usernames if specified
    if usernames is not None:
        passwords = []
        for username in usernames:
            for group in passwords_dict:
                if username in usernames_dict[group]:
                    index = usernames_dict[group].index(username)
                    passwords.append(passwords_dict[group][index])
                    break
        assert len(usernames) == len(passwords)
    else:  # Run for all usernames
        groups = username_groups
        if groups is not None:
            if not isinstance(groups, list):
                groups = [groups]
            assert all([group in usernames_dict.keys() for group in groups])
        else:
            groups = list(usernames_dict.keys())  # Run for all groups

        usernames, passwords = [], []
        for group in groups:
            for username, password in zip(usernames_dict[group], passwords_dict[group]):
                usernames.append(username)
                passwords.append(password)

    return usernames, passwords


def get_point_transfer_accounts(
    args: argparse.Namespace, credentials: _Credentials
) -> Optional[List[Dict[str, Dict[str, str]]]]:
    """
    Load file comprising all Microsoft
    accounts for which point transfers
    are to be performed.
    """
    file_path = get_file_path(PARENT_DIR, args.transfers_file)
    transfer_accounts_list = load_yaml(file_path)

    if transfer_accounts_list is None:
        PRINT_WARNING(f"{file_path} is empty/missing.")
        return

    usernames_dict = credentials[0]
    inverse_usernames_dict = {}
    for group, emails in usernames_dict.items():
        for email in emails:
            inverse_usernames_dict[email] = group

    for transfers_pair in transfer_accounts_list:
        source_dict, dest_dict = transfers_pair["source"], transfers_pair["dest"]
        source_account, dest_account = source_dict["email"], dest_dict["email"]
        assert ("name" in source_dict) and ("name" in dest_dict)
        for account in [source_account, dest_account]:
            assert account in inverse_usernames_dict, f"Credentials for {account} not found in {args.credentials_file}."
            source_account_group, dest_account_group = (
                inverse_usernames_dict[source_account],
                inverse_usernames_dict[dest_account],
            )
        assert (
            source_account_group == dest_account_group
        ), f"{source_account} (group: {source_account_group}) and {dest_account} (group: {dest_account_group}) must be in the same community group."

    return transfer_accounts_list


def load_yaml(primary_path: str, file_name: Optional[str] = None) -> Any:
    """
    Loads a given yaml file.
    Returns an empty dictionary if file is missing/empty.
    """
    obj = None
    file_path = get_file_path(primary_path, file_name)
    if os.path.isfile(file_path):
        with open(file_path, "r") as f:
            obj = yaml.safe_load(f)
    return obj


def get_file_path(primary_path: str, file_name: Optional[str] = None) -> str:
    """
    Generate appropriate full file path:
      - If `file_name` is None, it's assumed that the full
        path to the file is provided in `primary_path`.
      - Otherwise, it's assumed that `primary_path` is the
        path to the folder where a file named `file_name`
        exists.
    """
    return primary_path if file_name is None else os.path.join(primary_path, file_name)


def transfer_points_in_community(args: argparse.Namespace, credentials: _Credentials, source_account: str) -> None:
    """
    Transfer points from accounts with
    least points to accounts with most
    points within each community.
    """

    def extract_points_from_text(item: WebElement, regex="transfer_points") -> int:
        """
        Extract (potentially comma separated) points from an `item`.
        """
        points = REGEXES[regex].search(get_reward_text(item))
        points = int(points.group(1).replace(",", "").strip())
        return points

    # Get information about point transfers
    transfer_accounts_list = get_point_transfer_accounts(args, credentials)

    if transfer_accounts_list is None:
        return

    # Check if current account pair present
    transfers_pair = None
    for pair in transfer_accounts_list:
        if source_account == pair["source"]["email"]:
            transfers_pair = pair
            break

    if transfers_pair is None:
        PRINT_WARNING("No points are to be transferred from this account.")
        return

    BROWSER.get(COMMUNITY_URL)
    delay(1)
    click(BROWSER.find_element_by_id("rx-gift-points"))
    delay(1)

    # Get source and destination account information
    source_name = transfers_pair["source"]["name"]
    dest_account = transfers_pair["dest"]["email"]
    dest_name = transfers_pair["dest"]["name"]

    # Check if monthly sending/receiving limit already reached.
    dialog = BROWSER.find_element_by_id("gift-point")
    limit_reached = ["you've reached your monthly limit"]
    for text in limit_reached:
        if text in get_reward_text(dialog):
            PRINT_WARNING(f"Could not transfer points from {source_account} to {dest_account}: {text}.")
            return

    # Get number of points to be transferred
    transfer_points = transfers_pair.get("points")
    transfer_points = extract_points_from_text(dialog) if transfer_points is None else int(transfer_points)

    for account in dialog.find_element_by_tag_name("mee-card-group").find_elements_by_tag_name("mee-card"):
        account_name = (
            account.find_element_by_class_name("contentContainer").find_element_by_class_name("c-subheading").text
        )
        if account_name == dest_name:
            click(account.find_element_by_tag_name("button"))
            delay(0.5)

            # Get maximum available points
            available_points = extract_points_from_text(
                dialog.find_element_by_class_name("sender"), regex="available_points"
            )
            transfer_points = min(transfer_points, available_points)

            # Perform transfer if > 0 points available
            if transfer_points > 0:
                dialog.find_element_by_tag_name("input").send_keys(transfer_points)
                click(dialog.find_element_by_id("nextButton"))
                delay(0.5)
                click(dialog.find_element_by_id("nextButton"))
                delay(2)
                PRINT_SUCCESS(
                    f"{transfer_points} points were successfully transferred from {source_account} to {dest_account}."
                )
            else:
                PRINT_WARNING("No points were transferred since the account has 0 points.")
            BROWSER.get(REWARDS_URL)  # Reset back homepage
            return


@retry_if_exception(MAX_RETRIES, Exception)
def get_points_breakdown() -> Tuple[int, int, int]:
    """
    Go to Rewards homepage and get the
    earned and total points for today,
    and the points earned per search.
    """
    # Go to Rewards homepage
    BROWSER.get(POINTS_BREAKDOWN_URL)
    delay(2)

    found_points_earned, found_points_per_search = False, False

    # Store earned and total pc search points, and points earned per search
    for element in BROWSER.find_element_by_id("userPointsBreakdown").find_elements_by_class_name("pointsBreakdownCard"):
        if "pc search" in get_reward_text(element):
            for i in element.find_element_by_class_name("title-detail").find_elements_by_tag_name("p"):
                if i.get_attribute("ng-bind-html") == "$ctrl.pointProgressText":
                    points = REGEXES["points"].search(get_reward_text(i))
                    earned, total = points.group(1), points.group(3)
                    found_points_earned = True

                elif i.get_attribute("mee-caption") == "caption1":
                    points_per_search = REGEXES["points_per_search"].search(get_reward_text(i)).group(1)
                    found_points_per_search = True

                if found_points_earned and found_points_per_search:
                    break

    # Print current progress
    print(f"\rCurrent PC Search Points: {earned}/{total}", end="")

    return int(earned), int(total), int(points_per_search)


@retry_if_exception(MAX_RETRIES, Exception)
def perform_daily_searches(args: argparse.Namespace, words: List[str]) -> None:
    ##### Get Search Points #####
    earned, total, points_per_search = get_points_breakdown()

    # Store local point counter of earned points to optimize checking
    points_counter = earned

    # Initialize counter for checking how many times "Sign in" button has been clicked
    login_check_counter = 0

    # Make initial check if all rewards already collected
    if earned < total:
        # Keep searching till PC daily search limit reached
        while 1:
            query = np.random.choice(words, size=3, replace=True)
            query = " ".join(query)
            query_url = f"{BING_URL}search?q={query}"
            BROWSER.get(query_url)

            # Click on "Sign in" button twice on the search page
            # At times it shows not logged in
            while login_check_counter < 2:
                try:
                    delay(2)
                    click(BROWSER.find_element_by_id("b_header").find_element_by_id("id_l"))
                    delay(2)
                    BROWSER.get(query_url)
                finally:
                    login_check_counter += 1

            delay(1)

            print(f"\rCurrent PC Search Points: {points_counter}/{total}", end="")

            try:
                # Check local point counter against total points
                if points_counter >= total:
                    # Update local pc search point counter
                    earned, total, _ = get_points_breakdown()
                    points_counter = earned

                    # Now check against actual earned and total PC search points
                    if earned >= total:
                        break
                else:
                    # Increment local pointer by `points_per_search` points
                    points_counter += points_per_search
            except Exception as e:
                print(str(e))
                pass

    print("\nDaily goal reached.")


@retry_if_exception(MAX_RETRIES, Exception)
def solve_daily_and_extra_rewards(quit_current_window: bool, quit_all_windows: bool) -> Tuple[bool, bool]:
    """
    Solve all daily and "more" reward items.
    """
    # Go to Rewards homepage
    BROWSER.get(REWARDS_URL)
    delay(2)

    # Store main window handle and initialize arrays for rewards
    main_window = BROWSER.current_window_handle
    rewards: List[WebElement] = []

    # Get daily and more/other rewards
    add_daily_rewards(rewards)
    add_more_rewards(rewards)

    # Open all items (except quizzes) in `rewards` in new tabs and then close them
    for item in rewards:
        reward_text = get_reward_text(item)
        reward_type = REWARDS_CACHE.get_reward_type(reward_text)
        if reward_type != "ignore":
            try:
                could_solve_quiz = solve_reward_item(item, reward_type, reward_text)
                if could_solve_quiz:
                    delay(2)
                    BROWSER.close()  # Close current tab
                else:
                    quit_current_window = False  # Don't close current window
                    quit_all_windows = False  # Don't quit browser at the end

                # Switch focus back to main window
                BROWSER.switch_to.window(main_window)
            except Exception as e:
                print(f"Quizzes:\n\t{item.text}\n\tQuiz type: {reward_type}\n\t{e}")
                continue

    return quit_current_window, quit_all_windows


def get_reward_text(item: WebElement) -> str:
    """
    Get the text for a reward item.
    """
    return item.text.lower()


def confirm_logged_in() -> None:
    """
    Login again if required.
    Required because occasionally there's
    an error on bing when a new quiz item
    is clicked which fails to identify
    that user is already logged in.
    """
    # Check if log-in required again (occasional error on Bing)
    try:
        not_signed_in = BROWSER.find_element_by_class_name("simpleSignIn")
        assert not_signed_in.find_element_by_class_name("header").text == (
            "You are not signed in to Microsoft Rewards."
        )

        # Sign-in
        click(BROWSER.find_element_by_class_name("identityOption").find_element_by_tag_name("a"))
        delay(2)
    except:
        pass


def fix_item_url(url: str):
    """
    Properly decode `url` to remove sign-up page.
    Removes unnecessary stuff from a given URL
    and attempts to convert it so that the confirm
    log-in page isn't shown, since confirming often
    results in the page throwing an error.

    Three main steps are performed here:
    1. Remove unnecessary stuff, replace `%xx` characters into their single-character equivalents, and split the URL.
    2. Encode back just the query part of the split URL.
    3. To construct the correct URL, replace the original query with the fixed one.

    E.g.
    Given URL: "https://www.bing.com/rewards/signin?ru=https%3a%2f%2fwww.bing.com%2fsearch%3fq%3dthe+chicken+or+egg+dilemma%26rnoreward%3d1%26mkt%3dEN-US%26skipopalnative%3dtrue%26form%3dML17QA%26filters%3dIsConversation%3a%22true%22+PollScenarioId%3a%22POLL_ENUS_RewardsHotTakes_20201109%22+BTROID%3a%22Gamification_DailySet_20201109_Child3%22+BTROEC%3a%220%22+BTROMC%3a%2210%22&vt=Signin&ra="
    Fixed URL: "https://www.bing.com/search?q=the%20chicken%20or%20egg%20dilemma&rnoreward=1&mkt=EN-US&skipopalnative=true&form=ML17QA&filters=IsConversation:%22true%22%20PollScenarioId:%22POLL_ENUS_RewardsHotTakes_20201109%22%20BTROID:%22Gamification_DailySet_20201109_Child3%22%20BTROEC:%220%22%20BTROMC:%2210%22"
    """
    url_split = urlsplit(
        unquote_plus(url).replace("https://www.bing.com/rewards/signin?ru=", "").replace("&vt=Signin&ra=", "")
    )
    query_fixed = quote(url_split.query, safe="/&=:")
    url = urlunsplit(url_split._replace(query=query_fixed))
    return url


def open_reward_item(item: WebElement) -> None:
    """
    Click on a given `item` and
    switch focus to that tab.
    """
    try:
        # Click on reward item
        for e in item.find_elements_by_class_name("actionLink"):
            if e.text:
                click(e)
                break
        delay(2)
        BROWSER.switch_to.window(BROWSER.window_handles[-1])  # Switch tab to the new tab (next one on the right)
        BROWSER.get(
            fix_item_url(BROWSER.current_url)
        )  # Sometimes confirmation leads to error; try fixing the URL beforehand to avoid it
        confirm_logged_in()
        delay(2)
    except:
        pass


def add_daily_rewards(rewards: List[WebElement]) -> None:
    """
    Add all daily reward items
    to the given list.
    """
    # Store all (top) daily reward items whose points have not yet been collected in `rewards`
    daily_rewards = BROWSER.find_element_by_id("daily-sets").find_element_by_class_name("m-card-group")
    for item in daily_rewards.find_elements_by_tag_name("mee-card"):
        item = item.find_element_by_tag_name("mee-rewards-daily-set-item-content")
        try:
            if is_quiz_incomplete(item):
                rewards.append(item)
        except Exception as e:
            print(f"Daily rewards:\n\t{item.text}\n\t{e}")
            continue


def add_more_rewards(rewards: List[WebElement]) -> None:
    """
    Add all "more" reward items
    to the given list.
    """
    # Store all (bottom) more daily reward items whose points have not yet been collected
    more_rewards = BROWSER.find_element_by_id("more-activities").find_element_by_class_name("m-card-group")
    for item in more_rewards.find_elements_by_tag_name("mee-card"):
        item = item.find_element_by_tag_name("mee-rewards-more-activities-card-item")
        reward_text = get_reward_text(item)
        try:
            if "enter now" in reward_text:
                try:
                    item.find_element_by_class_name("points").find_element_by_class_name("mee-icon-SkypeCircleCheck")
                except NoSuchElementException:
                    rewards.append(item)

            elif item not in rewards and is_quiz_incomplete(item):
                rewards.append(item)

            elif "quiz incomplete" in reward_text:  # "What's on Top" quiz
                rewards.append(item)

        except Exception as e:
            print(f"More rewards:\n\t{item.text}\n\t{e}")
            continue


def is_quiz_incomplete(item: WebElement) -> bool:
    """
    Return True if a quiz `item` is still pending, or False if complete.
    """
    incomplete_indicators = ["mee-icon-AddMedium", "mee-icon-HourGlass"]

    completion_container = (
        item.find_element_by_tag_name("mee-rewards-points")
        .find_element_by_class_name("points")
        .find_element_by_tag_name("span")
    )
    if any([indicator in completion_container.get_attribute("class") for indicator in incomplete_indicators]):
        return True
    return False


def solve_reward_item(item: WebElement, reward_type: str, reward_text: str) -> bool:
    """
    Solve the given item, e.g. an MCQ
    quiz, tile quiz, daily poll, etc.
    """
    assert reward_type != "ignore"
    if reward_type == "unknown_quiz":  # Check if it's a quiz, and if so, solve it
        return attempt_solving_unknown_quiz(item, reward_text)
    else:  # Solve known quiz
        open_reward_item(item)  # Open item
        if reward_type == "unidentifiable":  # Return without doing anything if unidentifiable
            return True
        return REWARD_TYPE_DICT[reward_type]["solve_fn"](reward_text)  # Solve reward item


def solve_daily_poll(reward_text: str) -> bool:
    """
    Solve daily poll.
    """
    could_solve_quiz = False

    options = BROWSER.find_element_by_class_name("bt_pollOptions").find_elements_by_xpath("*")
    option_idx = np.random.choice(range(len(options)))
    try:
        click(options[option_idx])
        could_solve_quiz = True
    except:  # Could not solve quiz
        pass
    return could_solve_quiz


def solve_turbocharge_quiz(reward_text: str) -> bool:
    """
    Solve long MCQ quiz.
    Aka Turbocharge quiz.
    """
    could_solve_quiz = False
    try:
        try:
            click(BROWSER.find_element_by_id("rqStartQuiz"))  # Start quiz
        except:  # Already started earlier
            pass
        delay(2)

        current_question, total_questions = get_long_mcq_quiz_progress()
        question_solved = current_question  # Separate counter just for checking

        while current_question is not None:
            solve_long_mcq_quiz_question(reward_text, current_question)
            delay(2)
            current_question = get_long_mcq_quiz_progress()[0]
            question_solved += 1

        assert question_solved == total_questions
        could_solve_quiz = True
    except:  # Could not solve quiz
        pass
    return could_solve_quiz


@retry_if_exception(MAX_RETRIES, Exception)
def get_long_mcq_quiz_progress() -> Tuple[int, int]:
    """
    Get the number of questions solved
    and in total of a long MCQ quiz.
    """
    current_question, total_questions = None, None
    try:
        points = REGEXES["points"].search(get_reward_text(BROWSER.find_element_by_class_name("rqPoints")))
        earned_points, total_points = int(points.group(1)), int(points.group(3))
        current_question, total_questions = earned_points // 10, total_points // 10
    except:
        delay(2)
        assert BROWSER.find_element_by_id("quizCompleteContainer")
    return current_question, total_questions


@retry_if_exception(MAX_RETRIES, Exception)
def solve_long_mcq_quiz_question(reward_text: str, current_question: int) -> None:
    """
    Solve one question of a long MCQ quiz.
    """
    options = BROWSER.find_element_by_class_name("textBasedMultiChoice").find_elements_by_class_name(
        "rq_button"
    )  # Get options
    correct_answer = get_long_mcq_quiz_question_correct_answer(reward_text, options)  # Get correct answer
    click(options[correct_answer].find_element_by_tag_name("input"))  # Click on correct option
    delay(1)
    reload_page()
    delay(1)


@retry_if_exception(MAX_RETRIES, Exception)
def get_long_mcq_quiz_question_correct_answer(reward_text: str, options: List[WebElement]) -> int:
    """
    Get the index of correct option of a long MCQ quiz question.
    """
    # Load correct answer from cache if available
    cache_query = BROWSER.find_element_by_id("currentQuestionContainer").text
    correct_answer = REWARDS_CACHE.load_answer(reward_text, cache_query)
    if correct_answer is not None:
        return correct_answer

    # Otherwise compute and store it
    html = BROWSER.page_source
    for option_idx, option in enumerate(options):
        option_text = option.find_element_by_tag_name("input").get_attribute("value")
        if f'"correctAnswer":"{option_text}"' in html:
            correct_answer = option_idx
            REWARDS_CACHE.save_answer(reward_text, {cache_query: correct_answer})
            return correct_answer

    return 0


def solve_supersonic_quiz(reward_text: str) -> bool:
    """
    Solve tile selection quiz.
    Aka Supersonic quiz.
    """
    # return solve_turbocharge_quiz()

    could_solve_quiz = False
    try:
        try:
            click(BROWSER.find_element_by_id("rqStartQuiz"))  # Start quiz
        except:  # Already started earlier
            pass
        delay(2)

        current_question, total_questions = get_long_mcq_quiz_progress()
        question_solved = current_question  # Separate counter just for checking

        while current_question is not None:
            solve_tile_selection_question(reward_text, current_question)
            delay(2)
            current_question = get_long_mcq_quiz_progress()[0]
            question_solved += 1

        assert question_solved == total_questions
        could_solve_quiz = True
    except:  # Could not solve quiz
        pass
    return could_solve_quiz


@retry_if_exception(MAX_RETRIES, Exception)
def solve_tile_selection_question(reward_text: str, current_question_old: int) -> None:
    """
    Solve one question of a tile selection quiz.

    :param current_question_old: question to be solved
    """
    option_idx, current_question_new = 0, current_question_old

    # Perform dummy click (necessary to be able to click options)
    for e in BROWSER.find_element_by_class_name("btListicle").find_elements_by_xpath("*"):
        if e.get_attribute("class") == "b_slideexp":
            click(e)
            delay(2)
            break

    # Check if moved on to new question
    while current_question_old == current_question_new:
        # Click on option
        options = (
            BROWSER.find_element_by_id("currentQuestionContainer")
            .find_element_by_class_name("btOptions")
            .find_elements_by_xpath("*")
        )
        try:
            # Dummy click will sometimes result in clicking one of the options
            # If so, "rqAnswerOption{}" id no longer remains, and the option can be safely ignored
            option = options[option_idx].find_element_by_id(f"rqAnswerOption{option_idx}")
            if option.get_attribute("iscorrectoption") == "True":
                click(option)
        except:
            continue
        finally:
            option_idx = (option_idx + 1) % len(options)
            delay(2)
            current_question_new = get_long_mcq_quiz_progress()[0]


def solve_lightspeed_quiz(reward_text: str) -> bool:
    """
    Solve long MCQ quiz.
    Aka Turbocharge quiz.
    """
    return solve_turbocharge_quiz(reward_text)


def solve_warpspeed_quiz(reward_text: str) -> bool:
    """
    Solve tile selection quiz.
    Aka Supersonic quiz.
    """
    return solve_supersonic_quiz(reward_text)
    # return solve_turbocharge_quiz(reward_text)


def solve_short_mcq_quiz(reward_text: str) -> bool:
    """
    Solve short MCQ quiz.
    """
    could_solve_quiz = False
    try:
        while 1:
            current_question, total_questions = get_short_mcq_quiz_progress()

            # Get and click correct answer
            correct_answer = get_short_mcq_quiz_question_correct_answer(reward_text, current_question)
            click(BROWSER.find_element_by_id(f"ChoiceText_{current_question}_{correct_answer}"))
            delay(1)

            # Click on "Next question" / "Get your score" button
            click_short_mcq_quiz_next_question_button(current_question, total_questions)

            # Break if it was last question
            if current_question == total_questions - 1:
                break
        could_solve_quiz = True
    except:  # Could not solve quiz
        pass
    return could_solve_quiz


@retry_if_exception(MAX_RETRIES, Exception)
def get_short_mcq_quiz_progress() -> Tuple[int, int]:
    """
    Get the number of questions solved
    and in total of a short MCQ quiz.
    """
    question_answer_pane = BROWSER.find_element_by_id("ListOfQuestionAndAnswerPanes")
    points = REGEXES["points"].search(get_reward_text(question_answer_pane))
    current_question, total_questions = int(points.group(1)) - 1, int(points.group(3))
    return current_question, total_questions


@retry_if_exception(MAX_RETRIES, Exception)
def get_short_mcq_quiz_question_correct_answer(reward_text: str, current_question: int) -> int:
    """
    Get the index of correct option of a short MCQ quiz question.
    """
    # Load correct answer from cache if available
    question_answer_pane = BROWSER.find_element_by_id("ListOfQuestionAndAnswerPanes")
    cache_query = get_reward_text(question_answer_pane)
    correct_answer = REWARDS_CACHE.load_answer(reward_text, cache_query)
    if correct_answer is not None:
        return correct_answer

    # Otherwise compute and store it
    options = BROWSER.find_element_by_id(f"QuestionPane{current_question}").find_elements_by_class_name("wk_paddingBtm")
    for option in options:
        option = option.find_element_by_class_name("wk_choiceMaxWidth")
        option_id_name = option.get_attribute("id")
        try:
            assert option_id_name.startswith(f"ChoiceText_{current_question}")
            correct_answer = int(option_id_name.split("_")[-1])

            # This element exists only for the correct answer
            option.find_element_by_id(f"wk_statistics_{current_question}_{correct_answer}")

            # Save to cache (indexed by question text)
            REWARDS_CACHE.save_answer(reward_text, {cache_query: correct_answer})
            return correct_answer
        except:
            continue

    return 0


@retry_if_exception(MAX_RETRIES, Exception)
def click_short_mcq_quiz_next_question_button(current_question: int, total_questions: int) -> None:
    """
    Click on "Next question" / "Get your score" button
    """

    def click_next_question() -> None:
        click(BROWSER.find_element_by_id(f"AnswerPane{current_question}").find_element_by_class_name("wk_button"))

    click_next_question()
    delay(1)

    if current_question < total_questions - 1:
        attempt = 1
        # Try refreshing first if clicking doesn't work
        next_question = get_short_mcq_quiz_progress()[0]
        while (attempt <= 5) and (current_question == next_question):
            reload_page()
            delay(1)
            click_next_question()
            next_question = get_short_mcq_quiz_progress()[0]
            attempt += 1


def solve_binary_choice_quiz(reward_text: str) -> bool:
    """
    Solve binary choice based quiz.
    E.g. "What's on Top?" and "This or That?".
    """
    could_solve_quiz = False
    try:
        try:
            click(BROWSER.find_element_by_id("rqStartQuiz"))  # Start quiz
        except:  # Already started earlier
            pass
        delay(2)

        current_question, total_questions = get_binary_choice_quiz_progress()
        question_solved = current_question - 1  # Separate counter just for checking

        while current_question is not None:
            solve_binary_choice_quiz_question(reward_text)
            while 1:
                next_question = get_binary_choice_quiz_progress()[0]
                if next_question != current_question:
                    break
                delay(2)
            current_question = next_question
            question_solved += 1

        assert question_solved == total_questions
        could_solve_quiz = True
    except:  # Could not solve quiz
        pass
    return could_solve_quiz


@retry_if_exception(MAX_RETRIES, NoSuchElementException)
def get_binary_choice_quiz_progress() -> Tuple[int, int]:
    """
    Get the number of questions
    solved and in total of a
    binary choice based quiz.
    """
    delay(1)
    current_question, total_questions = None, None
    try:
        points = REGEXES["points"].search(get_reward_text(BROWSER.find_element_by_class_name("bt_Quefooter")))
        current_question, total_questions = int(points.group(1)), int(points.group(3))
    except:
        # try:
        BROWSER.find_element_by_id("quizCompleteContainer")
        # except NoSuchElementException:
        #     return get_binary_choice_quiz_progress()
    return current_question, total_questions


@retry_if_exception(MAX_RETRIES, Exception)
def solve_binary_choice_quiz_question(reward_text: str) -> None:
    """
    Solve one question of a
    binary choice based quiz.
    """
    num_options = 2

    # Click on option
    options = [BROWSER.find_element_by_id(f"rqAnswerOption{i}") for i in range(num_options)]
    option_idx = np.random.choice(range(num_options))
    click(options[option_idx])
    delay(2)


def solve_true_or_false_quiz(reward_text: str) -> bool:
    """
    Solve "True or false" based quiz.
    It's a different type of quiz but
    can be solved using the same
    implementation as a Turbocharge
    quiz.
    """
    return solve_turbocharge_quiz(reward_text)


def attempt_solving_unknown_quiz(item: WebElement, reward_text: str) -> bool:
    """
    Attempt identifying and solve
    a quiz of unknown type.
    """
    main_window = BROWSER.current_window_handle
    unique_quizzes = {
        k: v["solve_fn"] for k, v in REWARD_TYPE_DICT.items() if k not in ["daily_poll", "unknown_quiz", "ignore"]
    }
    could_solve_quiz = False
    for reward_type, solve_quiz in unique_quizzes.items():
        open_reward_item(item)
        try:
            could_solve_quiz = solve_quiz(reward_text)
            if could_solve_quiz:
                REWARDS_CACHE.save_reward_type(reward_text, reward_type)
                break
        except:
            BROWSER.close()  # Close current tab

            # Switch focus back to main window
            BROWSER.switch_to.window(main_window)
    return could_solve_quiz


def get_points_cash_by_type_str(points: int, cash: _StrFloatDict, diff: Optional[bool] = True) -> str:
    """
    Return a string to print out points and cash by their
    type, i.e., Microsoft vs. third-party sellers, e.g.
    Walmart, Target, etc.

    :param diff: Whether to print out the $ difference
                 between the cash obtained from
                 Microsoft vs. third-party sellers.
    """
    diff_str = f" [${(cash['microsoft'] - cash['non_microsoft']):.2f}]" if diff else ""
    return f"{points:6} [${cash['microsoft']:.2f} / ${cash['non_microsoft']:.2f}]{diff_str}"


@retry_if_exception(MAX_RETRIES, Exception)
def store_and_print_point_tally(results_dict: _ResultsDict, username: str) -> None:
    """
    Store the available and total point
    and cash tallies and print them out.
    """
    # Go to Rewards homepage
    BROWSER.get(REWARDS_URL)
    delay(3)

    for element in BROWSER.find_element_by_tag_name("mee-banner").find_elements_by_class_name("info-columns"):
        if "available points" in get_reward_text(element):
            available_points = element.find_element_by_tag_name("mee-rewards-counter" "-animation").text
            available_points = int(available_points.replace(",", ""))
            available_cash = get_total_cash(available_points)
            break

    # Store and print results
    results_dict[username] = {"points": available_points, "cash": available_cash}
    PRINT_SUCCESS(f"Available Points: {get_points_cash_by_type_str(available_points, available_cash)}")


def get_total_cash(total_points: int) -> _StrFloatDict:
    """
    Get maximum total cash that can be
    obtained for each type in $.
    """
    points_type_cash_dict = {
        "microsoft": OrderedDict({91000: 100, 46000: 50, 23000: 25, 13000: 10, 6500: 5, 2900: 3, 1500: 1.25}),
        "non_microsoft": OrderedDict({32500: 25, 13000: 10, 6500: 5}),
    }

    total_cash = {}
    for points_type, points_cash_dict in points_type_cash_dict.items():
        points_list = list(points_cash_dict.keys())

        # Ensure sorted
        assert all(points_list[i] >= points_list[i + 1] for i in range(len(points_list) - 1))

        # Compute total cash available
        thresholds_crossed: List[int] = []
        get_differential_cash(total_points, points_cash_dict, thresholds_crossed)
        total_cash[points_type] = sum([points_cash_dict[p] for p in thresholds_crossed])
        total_cash[points_type] += (total_points - sum(thresholds_crossed)) / 1300

    return total_cash


def get_differential_cash(points: int, points_cash_dict: Dict[int, float], thresholds_crossed: List[int]) -> None:
    """
    Recursively keep adding cash for each threshold
    of points that is crossed in top-down manner.
    """
    points_cash_dict_modified = points_cash_dict.copy()
    for p, c in points_cash_dict.items():
        points_cash_dict_modified.pop(p)
        if points >= p:
            thresholds_crossed.append(p)
            get_differential_cash(points - p, points_cash_dict_modified, thresholds_crossed)
            break


def print_summary(results_dict: _ResultsDict, diff: Optional[bool] = True) -> None:
    """
    Print out the points and cash
    for each user and in total.
    """
    # Initialize required variables
    total_points = 0
    total_cash = {"microsoft": 0.0, "non_microsoft": 0.0}
    max_len = max(len(username) for username in results_dict.keys()) + 4  # Max. character length among all usernames

    print()
    for username, results in results_dict.items():
        total_points += results["points"]

        assert sorted(results["cash"].keys()) == sorted(total_cash.keys())
        total_cash = {k: v + results["cash"][k] for k, v in total_cash.items()}

    #     PRINT_SUCCESS(f"{username:{max_len}}: {get_points_cash_by_type_str(results['points'], results['cash'])}")

    # PRINT_SUCCESS(f"\nTotal Point Tally: {get_points_cash_by_type_str(total_points, total_cash)}\n")

    # Prepare summary dataframe
    results_df = pd.DataFrame(results_dict).T
    results_df.index.name = "Email"
    results_df["MS Cash"] = results_df["cash"].apply(lambda row: row["microsoft"])
    results_df["Non-MS Cash"] = results_df["cash"].apply(lambda row: row["non_microsoft"])
    results_df = results_df.drop(columns="cash").reset_index(drop=False)
    to_append = pd.DataFrame(
        [["Total", total_points, total_cash["microsoft"], total_cash["non_microsoft"]]], columns=results_df.columns
    )
    results_df = results_df.append(to_append, ignore_index=True).reset_index(drop=True)
    results_df["Cash Diff"] = results_df["MS Cash"] - results_df["Non-MS Cash"]
    for col in ["MS Cash", "Non-MS Cash", "Cash Diff"]:
        results_df[col] = np.round(results_df[col], 2)
    results_df["points"] = results_df["points"].astype(int).apply(lambda row: f"{row:,}")
    results_df.rename(columns={"points": "Points"}, inplace=True)
    if not diff:
        results_df.drop(columns="Cash Diff", inplace=True)
    PRINT_SUCCESS(results_df)


# Define global variables here
PARENT_DIR = os.path.expanduser(PARENT_DIR)
CHROMEDRIVER_PATH = os.path.expanduser(CHROMEDRIVER_PATH)
IS_WINDOWS = check_if_windows()
PRINT_ID, PRINT_WARNING, PRINT_SUCCESS = get_printing_functions()
REGEXES = get_regexes()
BROWSER: webdriver.Chrome = None

# Define daily/other rewards related global variables here
POLL_TEXT = ["poll", "hot takes"]
TRUE_OR_FALSE_QUIZZES_TEXT = ["true or false", "who said it?"]
MCQ_QUIZZES_TEXT = ["test your smarts", "show what you know", "a, b, or c?"]
BINARY_QUIZZES_TEXT = ["when you pick which searches were tops", "this or that"]
UNKNOWN_QUIZZES_TEXT = ["quiz", "test", "how much do you know"]
IGNORE_LIST = ["take the tour"]
QUIZZES_TO_CACHE = ["turbocharge", "supersonic", "lightspeed", "warpspeed", "mcq_short", "binary"]

# Order important because some text is common
REWARD_TYPE_DICT = OrderedDict(
    {
        # Daily poll
        "daily_poll": {
            "reward_type": POLL_TEXT,
            "solve_fn": solve_daily_poll,
        },
        # Long MCQ quiz
        "turbocharge": {
            "solve_fn": solve_turbocharge_quiz,
        },
        # Tile selection quiz
        "supersonic": {
            "solve_fn": solve_supersonic_quiz,
        },
        # Currently same as turbocharge quiz
        "lightspeed": {
            "solve_fn": solve_lightspeed_quiz,
        },
        # Currently same as supersonic quiz
        "warpspeed": {
            "solve_fn": solve_warpspeed_quiz,
        },
        # True or false quiz
        # Must be placed above "mcq_short" because they
        # share some common text ("show what you know")
        "true_or_false": {
            "reward_type": TRUE_OR_FALSE_QUIZZES_TEXT,
            "solve_fn": solve_true_or_false_quiz,
        },
        # Short MCQ quiz
        "mcq_short": {
            "reward_type": MCQ_QUIZZES_TEXT,
            "solve_fn": solve_short_mcq_quiz,
        },
        # Binary choice based quiz
        "binary": {
            "reward_type": BINARY_QUIZZES_TEXT,
            "solve_fn": solve_binary_choice_quiz,
        },
        # Unknown type, but still a quiz
        "unknown_quiz": {"reward_type": UNKNOWN_QUIZZES_TEXT, "solve_fn": attempt_solving_unknown_quiz},
        # Just ignore because they don't open in new tab and mess things up
        "ignore": {
            "reward_type": IGNORE_LIST,
        },
    }
)
REWARDS_CACHE = RewardsCache()


def main():
    args = parse_args()

    # Get Chrome options
    chrome_kwargs = get_chrome_kwargs(args)

    # Get word list
    words = get_word_list()

    # Get login credentials
    credentials = load_credentials_file(args.credentials_file)
    usernames, passwords = get_bing_credentials(credentials, args.usernames, args.username_groups)

    # Initialize required variables
    quit_all_windows = True
    results_dict = OrderedDict()

    global BROWSER

    for username, password in zip(usernames, passwords):
        PRINT_ID(f"Account: {username}")

        # Initialize chromedriver
        BROWSER = webdriver.Chrome(**chrome_kwargs)

        quit_current_window = True

        try:
            BROWSER.maximize_window()

            # Log-in to Microsoft account
            log_in(username, password)

            # Run in debugging mode
            if args.debug:
                BROWSER.get(REWARDS_URL)
                breakpoint()  # Perform manual actions

            # Transfer points to another account
            if args.transfer_points:
                transfer_points_in_community(args, credentials, username)

            # Get search points
            if not args.no_search:
                perform_daily_searches(args, words)

            # Get rewards points
            if not (args.no_rewards or args.headless):
                try:
                    quit_current_window, quit_all_windows = solve_daily_and_extra_rewards(
                        quit_current_window, quit_all_windows
                    )
                except:
                    pass

            # Store and print out total points and cash
            store_and_print_point_tally(results_dict, username)

            # Close current tab
            if quit_current_window:
                BROWSER.close()

        except Exception as e:
            PRINT_WARNING(f"Skipping account since this exception was raised: {e}")

        finally:
            print("#" * 50 + "\n" * 3 + "#" * 50)

    # Quit browser if no windows to be kept open
    if quit_all_windows:
        BROWSER.quit()

    # Print final summary
    print_summary(results_dict)


if __name__ == "__main__":
    main()
