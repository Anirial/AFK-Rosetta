from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver
from sys import argv
from time import time, sleep
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
import json
import requests
from random import randint

class Rosetta:
    def __init__(self, timeout: int = 10, course_time: int = 30, headless: bool = True):
        self.timeout = timeout
        self.course_time = course_time
        self.options = webdriver.ChromeOptions()
        
        if headless:
            self.options.add_argument("--headless=new")
        
        self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
        self.options.add_argument("--window-size=1920,1080")
        self.options.add_argument("--mute-audio")
        self.options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        prefs = {
            "profile.default_content_setting_values.media_stream_mic": 2
        }
        self.options.add_experimental_option("prefs", prefs)

    def login(self, email: str, password: str) -> bool:
        try:
            self.driver.get("https://login.rosettastone.com/login")

            # Wait for a button that loads after all the element we need to load to make sure that every element we need are loaded
            selector = "input[data-qa='RememberMeCheckbox']"
            self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))

            email_field = self.driver.find_element(By.CSS_SELECTOR, "input[data-qa='Email']")
            password_field = self.driver.find_element(By.CSS_SELECTOR, "input[data-qa='Password']")

            email_field.send_keys(email)
            password_field.send_keys(password)

            sign_in_button = self.driver.find_element(By.CSS_SELECTOR, "button[data-qa='SignInButton']")
            sign_in_button.click()
            

            self.wait.until_not(EC.title_is("Welcome to Rosetta Stone®!"))
            return self.driver.title != "Welcome to Rosetta Stone®!"
        
        except Exception:
            return False


    def start_lesson(self) -> bool:
        try:
            # Go to the learning page
            selector = "div[data-qa='ProductName-Foundations']"
            element = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
            element.click()

            # Go to unit selector menu
            unit_selector = "span[data-qa='zoom_course_menu_unit_menu_open']"
            unit_element = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, unit_selector)))
            self.driver.execute_script("arguments[0].click();", unit_element)

            # Select first unit
            unit_one_selector = "div[data-qa='UnitItem-1']"
            unit_one_element = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, unit_one_selector)))
            self.driver.execute_script("arguments[0].click();", unit_one_element)

            # Select the first lesson
            lesson_selector = "div[data-qa='lesson-number-0']"
            lesson_element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, lesson_selector)))
            self.driver.execute_script("arguments[0].click();", lesson_element)

            # Select the first course
            course_selector = "button[data-qa^='PathButtonCourseMenu-PATH_']"
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, course_selector))) # Wait for at least one button to load

            all_course_element = self.driver.find_elements(By.CSS_SELECTOR, course_selector)
            course_element = all_course_element[0]
            self.driver.execute_script("arguments[0].click();", course_element)

            end_time = time() + self.timeout
            
            while time() < end_time:
            
                reset_selector = "div[data-qa='ResetPathModal'] button[data-qa='PromptButton'][type='default']"
                error_selector = "span[data-qa='error_5414']"
                microphone_selector = "button[data-qa='PromptButton'][type='default']"
                voice_type_selector = "span[data-qa='misc_cancel']"
                skip_selector = "div[data-qa='skip']"
                
                
                reset_elements = self.driver.find_elements(By.CSS_SELECTOR, reset_selector)
                error_elements = self.driver.find_elements(By.CSS_SELECTOR, error_selector)
                microphone_elements = self.driver.find_elements(By.CSS_SELECTOR, microphone_selector)
                voice_type_elements = self.driver.find_elements(By.CSS_SELECTOR, voice_type_selector)
                skip_elements = self.driver.find_elements(By.CSS_SELECTOR, skip_selector)

                # Check if the lesson was started successfuly
                if skip_elements and skip_elements[0].is_displayed():
                    return True
                
                # Check if the user has multiple sessions running
                if error_elements and error_elements[0].is_displayed():
                    print("Please disconnect from all your sessions and try again in a few minutes")
                    return False
                

                # Reset the score if asked to by rosetta
                if reset_elements and reset_elements[0].is_displayed():
                    try:
                        reset_elements[0].click()
                        sleep(0.5)
                    except Exception:
                        pass # Rosetta did not asked us to reset

                    continue
                
                # Refuse the use of microphone
                if microphone_elements and microphone_elements[0].is_displayed() and not reset_elements:
                    try:
                        microphone_elements[0].click()
                        sleep(0.5)
                    except Exception:
                        pass # Rosetta did not asked us to allow the use of the microphone (Tho i blocked it in the chrome options so thats weird)

                    continue

                # Select voice type if asked
                if voice_type_elements and voice_type_elements[0].is_displayed():
                    try:
                        self.driver.execute_script("arguments[0].click();", voice_type_elements[0])
                        sleep(0.5)
                    except Exception:
                        pass # We were not asked to select voice type
                    continue

                
                sleep(0.5)
            
            print("The page took too long to load, please check your internet connection and try again")
            return False
                
        except Exception as e:
            print(f"An error occured while starting the lesson : {e}")
            return False

    def parse_request(self, request: dict[str, str]) -> dict | None:
        url = request.get("url")
        post_data = request.get("postData")

        if not (url.startswith("https://tracking.rosettastone.com/") and url.endswith("&_method=put") and "path_scores" in url) or post_data is None:
            return None
        
        headers = request.get("headers")
        
        selenium_cookies = self.driver.get_cookies()
        session_cookies = None

        if selenium_cookies is not None:
            session_cookies = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
        
        if not all([lambda x: x is not None for x in [url, post_data, headers, session_cookies]]):
            return None
        
        return {"headers": headers, "payload": post_data, "url": url, "cookies": session_cookies}


    def generate_original_request(self, timeout: int, max_retries: int) -> dict[str, str] | None:
        skip_selector = "div[data-qa='skip']"
        repeat_selector = "button[data-qa='RepeatButton']"
       
        wait = WebDriverWait(self.driver, timeout)
        
        print("Listening to traffic via CDP")
        while max_retries > 0:
            print("Generating original request")

            try:
                try: # Rosetta ask us to re-do the course
                    repeat_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, repeat_selector)))
                    repeat_element.click()
                    
                except Exception: # Rosetta didn't asked us to re-do the course
                    skip_element = self.driver.find_element(By.CSS_SELECTOR, skip_selector)
                    skip_element.click()

                sleep(0.5)
                end_time = time() + 5
                while time() < end_time:
                    logs = self.driver.get_log("performance")
                    
                    for entry in logs:
                        log_data = json.loads(entry["message"])["message"]
            
                        if log_data["method"] == "Network.requestWillBeSent":
                            res = self.parse_request(log_data["params"]["request"])
                            if res is not None:
                                print("Original request generated")
                                return res
                    sleep(0.5)

            except Exception:
                pass

            max_retries -= 1
            sleep(1)
            print("Failed to generate the request")

        return None

    def build_root(self, data: dict[str, str]) -> Element | None:
        if data is not None:
            headers = data.get("headers")
            if "Content-Length" in headers:
                del headers["Content-Length"]
            if "Accept-Encoding" in headers:
                del headers["Accept-Encoding"]
            
            try:
                root = ET.fromstring(data.get("payload"))
                return root
            except Exception:
                print("Unable to parse original XML payload.")
        return 
    
    def send_payload(self, data: dict[str, str], root: Element, overrides: dict[str, str]) -> int:
        for tag, new_val in overrides.items():
            element = root.find(tag)
            element.text = str(new_val)

        updated_at_element = root.find('updated_at')
        if updated_at_element is not None:
            updated_at_element.text = str(int(time() * 1000))
            
        new_payload: str = ET.tostring(root, encoding='utf-8').decode('utf-8')
        if not new_payload.startswith('<path_score>'):
            new_payload = f"<path_score>{new_payload}</path_score>"
        
        response = requests.post(data.get("url"), headers=data.get("headers"), cookies=data.get("cookies"), data = new_payload)
        return response.status_code

    def build_override(self, challenges_count: int) -> dict:
        overrides = {
            "delta_time": 480000,
            "complete": "true",
            "score_correct": challenges_count,
            "score_incorrect": 0,
            "score_skipped": 0
        }
        return overrides
    
    def main(self, email: str, password: str, params: dict):
        self.driver = webdriver.Chrome(options=self.options)
        self.wait = WebDriverWait(self.driver, self.timeout)
        self.wait_course = WebDriverWait(self.driver, self.course_time)
        
        try:
            print("Login in Rosetta Stone.")
            if not self.login(email, password):
                print("Unable to login.")
                return
            
            print("Starting the lesson.")
            if not self.start_lesson(): 
                print("Unable to start the lesson.")
                return
          
            data = self.generate_original_request(3, 3)
            self.driver.get("https://totale.rosettastone.com/sign_out")
            self.driver.quit()

            if data is None:
                print("The program was not able to generate the original request.")
                return
            
            root = self.build_root(data)
            if root is None:
                return
            
            challenges = root.find("number_of_challenges")
            if challenges is None or challenges.text is None:
                print("The original payload seems corrumpted. Aborting")
                return
            
            try:
                chal_num = int(challenges.text)
            except Exception:
                print("The original payload seems corrumpted. Aborting")
                return
            
            overrides = self.build_override(chal_num)
            missing_tags: list[str] = []

            for tag in list(overrides.keys()):
                element = root.find(tag)
                if element is None:
                    missing_tags.append(tag)
                    overrides.pop(tag)
            
            if len(missing_tags) != 0:
                print("Warning, the following tags are not in the original payload : ")
                for tag in missing_tags:
                    print(tag)
                print("These tags will be ignored")
            
            try:
                requested_time = int(params.get("time", 0))
            except:
                print("The amount of time specified is not valid")
                return
            
            sent = 0
            error = 0

            iterations = requested_time // 480000
            remaining_time = requested_time % 480000
            display_iterations = iterations + (1 if remaining_time > 0 else 0)

            for i in range(iterations):
                status = self.send_payload(data, root, overrides)
                if status in [200, 201, 204]:
                    print(f"[+] Request {i+1}/{display_iterations} sent successfully !")
                    sent += 1
                else:
                    print(f"[-] Request {i+1} was not successful (HTTP Code {status})")
                    error += 1
                    

                if i < iterations:
                    sleep(randint(10, 20) / 10)

            if remaining_time > 0:
                overrides["delta_time"] = remaining_time
                status = self.send_payload(data, root, overrides)
                if status in [200, 201, 204]:
                    print(f"[+]Request {display_iterations}/{display_iterations} sent successfully !")
                    sent += 1
                else:
                    print(f"[-] Request {i+1} was not successful (HTTP Code {status})")
                    error += 1
            
            print(f"{sent} packets were correctly sent and {error} encountered an error for a total of {sent+ error} packet sent. Average : {round(sent / (sent + error), 2) * 100}%")
            print("Thanks for playing !")
        except Exception as e:
            print(f"Global error : {e}")



if __name__ == "__main__":
    if len(argv) == 4:
        rosetta = Rosetta()
        params = {"time": int(argv[3]) * 1000}
        rosetta.main(argv[1], argv[2], params)

    elif "help" in argv:
        print("Usage : python <path_to_rosetta.py> <email> <password> <time_in_seconds>")
        print("<path_to_rosetta.py> : The absolute path to this script")
        print("<email> : Your Rosetta Stone account email")
        print("<password> : Your Rosetta Stone account password")
        print("<time> : The amount of time you want to add to your account, in seconds")
    else:
        print("Usage : python <path_to_rosetta.py> <email> <password> <time_in_seconds>\n Type 'path_to_rosetta.py help' for more informations")
