# Script to perform random searches on Bing for earning Daily Microsoft Reward Points
# Make sure to monitor progress intially when account created (custom interface and edge cases)

# Import all necessary libraries
import numpy as np
import time
import os
import platform as pl
import argparse
from collections import OrderedDict
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options


def get_word_list(is_windows):
    # Get word list from url and save it locally if not present
    word_list_path = '<windows/path/to/word_list.txt>' if is_windows else 'unix/path/to/word_list.txt'
    if not os.path.exists(word_list_path):
        word_list_url = 'https://svnweb.freebsd.org/csrg/share/dict/words?view=co&content-type=text/plain'
        import requests
        response = requests.get(word_list_url)
        words = response.content.splitlines()
        words = [str(word.decode('utf8')).strip() for word in words if len(word) > 3]
        with open(word_list_path, 'w+') as f:
          for item in words:
              f.write('{}\n'.format(item))
    else:
        # Load word list from local storage
        with open(word_list_path, 'r') as f:
            words = f.readlines()
    return words

def get_bing_credentials(args):
    # Set usernames and (preferably common) password(s) for Microsoft login

    usernames_dict = OrderedDict({
        1: ['<username1@gmail.com>', '<username2@gmail.com>', '<username3@gmail.com>'],
        2: ['<username4@gmail.com>', '<username5@yahoo.com>', '<username6@gmail.com>', '<username7@gmail.com>', '<username8@gmail.com>']
    })

    passwords_dict = OrderedDict({
        1: '<common_password1>',
        2: '<common_password2>'
    })

    assert list(usernames_dict.keys()) == list(passwords_dict.keys())

    if args.usernames:
        usernames = ['{}@gmail.com'.format(username) for username in args.usernames]
        passwords = [passwords_dict[args.username_group]]*len(usernames)
    else:
        if not args.all:
            assert args.username_group in usernames_dict.keys()
            username_groups = [args.username_group]
        else:
            username_groups = usernames_dict.keys()

        usernames, passwords = [], []
        for group in username_groups:
            for username in usernames_dict[group]:
                usernames.append(username)
                passwords.append(passwords_dict[group])

    return usernames, passwords

def get_points_breakdown():
    # Store earned and total pc search points
    for element in browser.find_element_by_id('userPointsBreakdown')\
                          .find_elements_by_class_name('pointsBreakdownCard'):
        if 'pc search' in element.text.lower():
            for i in element.find_element_by_class_name('pointsDetail')\
                            .find_elements_by_tag_name('p'):
                if i.get_attribute('ng-bind-html') == '$ctrl.pointProgressText':
                    earned, total = i.text.strip().replace(' ', '').replace(',', '').split('/')
                    break

    # Print current progress
    print('\rCurrent PC Search Points: {}/{}'.format(earned, total), end='')

    return earned, total

def add_daily_rewards(rewards):
    # Store all (top) daily reward items whose points have not yet been collected in 'rewards'
    daily_rewards = browser.find_element_by_id('daily-sets')\
                           .find_element_by_class_name('m-card-group')
    for item in daily_rewards.find_elements_by_tag_name('mee-card'):
        try:
            item = item.find_element_by_tag_name('mee-rewards-daily-set-item-content')
            if 'mee-icon-AddMedium' in item.find_element_by_tag_name('mee-rewards-points')\
                                           .find_element_by_class_name('points')\
                                           .find_element_by_tag_name('span')\
                                           .get_attribute('class'):
                rewards.append(item)
        except Exception as e:
            print('Daily rewards:\n\t{}\n\t{}'.format(item.text, str(e)))
            continue

def add_more_rewards(rewards):
    # Store all (bottom) more daily reward items whose points have not yet been collected in 'rewards'
    more_rewards = browser.find_element_by_id('more-activities') \
                          .find_element_by_class_name('m-card-group')
    for item in more_rewards.find_elements_by_tag_name('mee-card'):
        try:
            item = item.find_element_by_tag_name('mee-rewards-more-activities-card-item')
            if 'enter now' in item.text.lower():
                try:
                    item.find_element_by_class_name('points')\
                        .find_element_by_class_name('mee-icon-SkypeCircleCheck')
                except NoSuchElementException:
                    rewards.append(item)

            elif item not in rewards and \
               'mee-icon-AddMedium' in item.find_element_by_tag_name('mee-rewards-points')\
                                           .find_element_by_class_name('points')\
                                           .find_element_by_tag_name('span')\
                                           .get_attribute('class'):
                rewards.append(item)

            elif 'quiz incomplete' in item.text.lower(): # "What's on Top" quiz
                rewards.append(item)

        except Exception as e:
            print('More rewards:\n\t{}\n\t{}'.format(item.text, str(e)))
            continue

def confirm_logged_in():
    # Check if log-in required again (occasional error on Bing)
    try:
        not_signed_in = browser.find_element_by_class_name('simpleSignIn')
        assert not_signed_in.find_element_by_class_name('header').text == 'You are not signed in to Microsoft Rewards.'
        browser.find_element_by_class_name('identityOption').find_element_by_tag_name('a').click() # Sign-in
        time.sleep(1.5)
    except:
        pass

def open_reward_item(item):
    try:
        # Click on reward item
        for e in item.find_elements_by_class_name('actionLink'):
            if e.text:
                e.click()
                break
        time.sleep(1.5)
        # Switch tab to the new tab (next one on the right)
        browser.switch_to.window(browser.window_handles[-1])
        confirm_logged_in()
        time.sleep(2)
    except:
        pass

def identify_item_reward_type(reward_text, mcq_quizzes_text):
    '''
    -1 - Unidentifiable
     0 - Daily poll
     1 - Unknown quiz
     2 - Turbocharge quiz
     3 - Supersonic quiz
     4 - Lightspeed quiz
     5 - Warpspeed quiz
     6 - Short MCQ quiz
     7 - What's on Top?
    '''
    reward_type = -1

    if 'daily poll' in reward_text:
        reward_type = 0
    elif 'turbocharge' in reward_text:
        reward_type = 2
    elif 'supersonic' in reward_text:
        reward_type = 3
    elif 'lightspeed' in reward_text:
        reward_type = 4
    elif 'warpspeed' in reward_text:
        reward_type = 5
    elif any([text in reward_text for text in mcq_quizzes_text]):
        reward_type = 6
    elif 'when you pick which searches were tops' in reward_text:
        reward_type = 7
    elif 'quiz' in reward_text or 'test' in reward_text:
        reward_type = 1

    return reward_type

def solve_reward_item(item, reward_type):
    solve_reward_item_functions = {
        0: solve_daily_poll,
        2: solve_turbocharge_quiz,
        3: solve_supersonic_quiz,
        4: solve_lightspeed_quiz,
        5: solve_warpspeed_quiz,
        6: solve_short_mcq_quiz,
        7: solve_binary_choice_quiz,
        1: attempt_solving_unknown_quiz
    }

    if reward_type == 1:
        # Check if it's a quiz, and if so, solve it
        return attempt_solving_unknown_quiz(item, solve_reward_item_functions)

    # Solve known quiz
    open_reward_item(item)
    if reward_type == -1:
        return True
    return solve_reward_item_functions[reward_type]() # Solve reward item

def solve_daily_poll():
    could_solve_quiz = False
    try:
        browser.find_element_by_id('btoption0').click()
        could_solve_quiz = True
    except: # Could not solve quiz
        pass
    return could_solve_quiz

def solve_turbocharge_quiz():
    # Turbocharge: Long MCQ quiz

    could_solve_quiz = False
    try:
        try:
            browser.find_element_by_id('rqStartQuiz').click() # Start quiz
            time.sleep(1.5)
        except: # Already started earlier
            pass

        current_question, total_questions = get_long_mcq_quiz_progress()
        question_solved = current_question # Separate counter just for checking

        while current_question is not None:
            solve_long_mcq_quiz_question(current_question)
            time.sleep(2)
            current_question = get_long_mcq_quiz_progress()[0]
            question_solved += 1

        assert question_solved == total_questions
        could_solve_quiz = True
    except: # Could not solve quiz
        pass
    return could_solve_quiz

def get_long_mcq_quiz_progress():
    current_question, total_questions = None, None
    try:
        earned_points, total_points = browser.find_element_by_class_name('rqPoints').text.strip().split('/')
        current_question, total_questions = int(earned_points)//10, int(total_points)//10
    except:
        time.sleep(2)
        assert browser.find_element_by_id('quizCompleteContainer')
    return current_question, total_questions

def solve_long_mcq_quiz_question(current_question_old):
    '''
    :param current_question_old - question to be solved
    :param current_question_new - current question (different if `current_question_old` is already solved)
    '''

    option_num, current_question_new = 0, current_question_old

    # Check if moved on to new question
    while current_question_old == current_question_new:
        # Click on option
        options = browser.find_element_by_class_name('textBasedMultiChoice')\
                         .find_elements_by_class_name('rq_button')
        options[option_num].find_element_by_tag_name('input').click()
        option_num = (option_num+1) % len(options)
        time.sleep(1.5)
        current_question_new = get_long_mcq_quiz_progress()[0]

def solve_supersonic_quiz():
    # Supersonic: Tile selection

    could_solve_quiz = False
    try:
        try:
            browser.find_element_by_id('rqStartQuiz').click() # Start quiz
            time.sleep(1.5)
        except: # Already started earlier
            pass

        current_question, total_questions = get_long_mcq_quiz_progress()
        question_solved = current_question # Separate counter just for checking

        while current_question is not None:
            solve_tile_selection_question(current_question)
            time.sleep(2)
            current_question = get_long_mcq_quiz_progress()[0]
            question_solved += 1

        assert question_solved == total_questions
        could_solve_quiz = True
    except: # Could not solve quiz
        pass
    return could_solve_quiz

def solve_tile_selection_question(current_question_old):
    '''
    :param current_question_old - question to be solved
    :param current_question_new - current question (different if `current_question_old` is already solved)
    '''
    option_num, current_question_new = 0, current_question_old

    # Perform dummy click (necessary to be able to click options)
    for e in browser.find_element_by_class_name('btListicle').find_elements_by_xpath('*'):
        if e.get_attribute('id') != 'questionId': # 'slideexp1_BC5E45c'
            e.click()
            time.sleep(1.5)
            break

    # Check if moved on to new question
    while current_question_old == current_question_new:
        # Click on option
        options = browser.find_element_by_id('currentQuestionContainer')\
                         .find_element_by_class_name('btOptions')\
                         .find_elements_by_xpath('*')
        try:
            # Dummy click will sometimes result in clicking one of the options
            # If so, 'rqAnswerOption{}' id no longer remains, and the option can be safely ignored
            option = options[option_num].find_element_by_id('rqAnswerOption{}'.format(option_num))
            if option.get_attribute('iscorrectoption') == 'True':
                option.click()
        except:
            continue
        finally:
            option_num = (option_num+1) % len(options)
            time.sleep(1.5)
            current_question_new = get_long_mcq_quiz_progress()[0]

def solve_lightspeed_quiz():
    return solve_turbocharge_quiz()

def solve_warpspeed_quiz():
    return solve_supersonic_quiz()

def solve_short_mcq_quiz():
    could_solve_quiz = False
    try:
        question_answer_pane = browser.find_element_by_id('ListOfQuestionAndAnswerPanes')
        for e in question_answer_pane.find_elements_by_xpath('*'):
            if 'QuestionPane' in e.get_attribute('id'):
                question_pane = e
                break

        quiz_progress = question_pane.find_element_by_class_name('b_footnote').text
        current_question, total_questions = quiz_progress.replace('(', '').replace(')', '').split(' of ')
        current_question, total_questions = int(current_question)-1, int(total_questions)
        for i in range(current_question, total_questions):
            time.sleep(1.5)
            browser.find_element_by_id('QuestionPane{}'.format(current_question))\
                   .find_element_by_id('ChoiceText_{}_0'.format(current_question)).click()
            time.sleep(1.5)

            # Click on 'Next question' / 'Get your score' button
            next_question = browser.find_element_by_id('AnswerPane{}'.format(current_question)).find_element_by_class_name('cbtn')
            next_question.click()
            current_question += 1
        could_solve_quiz = True
    except: # Could not solve quiz
        pass
    return could_solve_quiz

def solve_binary_choice_quiz():
    # "What's on Top?" Binary choice questions

    could_solve_quiz = False
    try:
        try:
            browser.find_element_by_id('rqStartQuiz').click() # Start quiz
            time.sleep(1.5)
        except: # Already started earlier
            pass

        current_question, total_questions = get_binary_choice_quiz_progress()
        question_solved = current_question-1 # Separate counter just for checking

        while current_question is not None:
            solve_binary_choice_quiz_question()
            while 1:
                next_question = get_binary_choice_quiz_progress()[0]
                if next_question != current_question:
                    break
                time.sleep(2)
            current_question = next_question
            question_solved += 1

        assert question_solved == total_questions
        could_solve_quiz = True
    except: # Could not solve quiz
        pass
    return could_solve_quiz

def get_binary_choice_quiz_progress():
    current_question, total_questions = None, None
    try:
        current_question, total_questions = browser.find_element_by_class_name('bt_Quefooter').text.strip().split(' of ')
        current_question, total_questions = int(current_question), int(total_questions)
    except:
        try:
            browser.find_element_by_id('quizCompleteContainer')
        except NoSuchElementException:
            return get_binary_choice_quiz_progress()
    return current_question, total_questions

def solve_binary_choice_quiz_question():
    # Click on option
    options = [browser.find_element_by_id('rqAnswerOption{}'.format(i)) for i in range(2)]
    option_num = np.random.choice(range(2))
    options[option_num].click()
    time.sleep(2)

def attempt_solving_unknown_quiz(item, solve_reward_item_functions):
    main_window = browser.current_window_handle
    unique_quizzes = [v for k, v in solve_reward_item_functions.items() if k not in (0,1)]
    could_solve_quiz = False
    for solve_quiz in unique_quizzes:
        open_reward_item(item)
        try:
            could_solve_quiz = solve_quiz()
            if could_solve_quiz:
                break
        except:
            browser.close() # Close current tab

            # Switch focus back to main window
            browser.switch_to.window(main_window)
    return could_solve_quiz


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--usernames', dest='usernames', nargs='+', help='list of usernames')
    parser.add_argument('--group', dest='username_group', help='Username group; 1 | 2', type=int, default=1)
    parser.add_argument('--all', action='store_true', help="Run for all groups")
    parser.add_argument('--no-search', action='store_true', help="Don't do daily searches")
    parser.add_argument('--no-rewards', action='store_true', help="Don't collect daily/more rewards")
    parser.add_argument('--headless', dest='headless', action='store_true', help='run Chrome in headless mode')
    args = parser.parse_args()

    platform = pl.system()
    if platform not in {'Darwin', 'Linux', 'Windows'}:
        raise Exception('Unknown OS "{}"'.format(platform))
    is_windows = platform == 'Windows'

    # Get word list
    words = get_word_list(is_windows)

    # Get login credentials
    usernames, passwords = get_bing_credentials(args)

    options = Options()
    if args.headless: # Run headless
        options.add_argument("--headless")
    chrome_kwargs = {'options': options}

    quit_all_windows, total_points = 1, 0
    bing_url = 'https://www.bing.com/'
    rewards_url = 'https://account.microsoft.com/rewards/'
    points_breakdown_url = 'https://account.microsoft.com/rewards/pointsbreakdown'
    mcq_quizzes_text = ['test your smarts', 'show what you know', 'a, b, or c?']

    global browser

    for username, password in zip(usernames, passwords):
        print('Account: {}'.format(username))

        # Initialize chromedriver
        if is_windows:
            chrome_kwargs['executable_path'] = '<path_to_webdriver.exe>' # Replace path to webdriver
        browser = webdriver.Chrome(**chrome_kwargs)

        browser.maximize_window()
        browser.get('https://login.live.com/')

        # Login with Microsoft account
        time.sleep(1)
        browser.find_element_by_id('i0116').send_keys(username)
        browser.find_element_by_id('idSIButton9').click()
        time.sleep(1)
        browser.find_element_by_id('i0118').send_keys(password)
        browser.find_element_by_id('idSIButton9').click()
        time.sleep(1)

        ##### Get Search Points #####
        if not args.no_search:
            # Go to Rewards homepage
            browser.get(points_breakdown_url)
            time.sleep(2)

            earned, total = get_points_breakdown()

            # Store local point counter of earned points to optimize checking
            points_counter = int(earned)

            # Make initial check if all rewards already collected
            if int(earned) < int(total):
                # Keep searching till PC daily search limit reached
                while 1:
                    query = np.random.choice(words, size=3, replace=True)
                    query = ' '.join(query)
                    browser.get('{}search?q={}'.format(bing_url, query))
                    time.sleep(1)

                    print('\rCurrent PC Search Points: {}/{}'.format(points_counter, total), end='')

                    try:
                        # Check local point counter against total points
                        if points_counter >= int(total):
                            # Go to Rewards homepage and open points breakdown
                            browser.get(points_breakdown_url)
                            time.sleep(2)

                            # Update local pc search point counter
                            earned = get_points_breakdown()[0]
                            points_counter = int(earned)

                            # Now check against actual earned and total PC search points
                            if int(earned) >= int(total):
                                break
                        else:
                            # Increment local pointer by 5 points
                            points_counter += 5
                    except Exception as e:
                        print(str(e))
                        pass

            print('\nDaily goal reached.')


        ##### Get Reward Points #####
        # Go to Rewards homepage
        browser.get(rewards_url)
        time.sleep(2)

        # Store main window handle and initialize arrays for rewards and quizzes
        main_window = browser.current_window_handle
        quit_current_window = 1
        rewards, other_rewards = [], []

        try:
            if not args.no_rewards:
                # Get daily and more/other rewards
                add_daily_rewards(rewards)
                add_more_rewards(rewards)

                # Open all items (except quizzes) in 'rewards' in new tabs and then close them
                for item in rewards:
                    reward_text = item.text.lower()
                    reward_type = identify_item_reward_type(reward_text, mcq_quizzes_text)

                    if not args.headless: # Solve quiz
                        try:
                            could_solve_quiz = solve_reward_item(item, reward_type)
                            if could_solve_quiz:
                                time.sleep(3)
                                browser.close() # Close current tab
                            else:
                                quit_current_window = 0 # Don't close current window
                                quit_all_windows = 0 # Don't quit browser at the end

                            # Switch focus back to main window
                            browser.switch_to.window(main_window)
                        except Exception as e:
                            print('Quizzes:\n\t{}\n\tQuiz type: {}\n\t{}'.format(item.text, reward_type, str(e)))
                            continue

        except:
            continue

        finally:
            # Go to Rewards homepage
            browser.get(rewards_url)
            time.sleep(3)

            # Get available and total point tally
            header = browser.find_element_by_tag_name('mee-banner')
            for element in header.find_elements_by_class_name('info-columns'):
                if 'available points' in element.text.lower():
                    available_points = element.find_element_by_tag_name('mee-rewards-counter-animation').text
                    available_points = int(available_points.replace(',', ''))
                    print('Available Points: {} (${:.2f})\n'.format(available_points, available_points/1300))
                    total_points += available_points
                    break

            # Close current tab
            if quit_current_window:
                browser.close()

    # Quit browser if no windows to be kept open
    if quit_all_windows:
        browser.quit()

    print('Total Point Tally: {} (${:.2f})\n'.format(total_points, total_points/1300))


if __name__ == '__main__':
    main()
