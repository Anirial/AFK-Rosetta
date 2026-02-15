from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver
from threading import Thread
from sys import argv
from time import time, sleep


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

        prefs = {
            "profile.default_content_setting_values.media_stream_mic": 2  # Block the microphone to prevent Rosetta from asking
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

            # Reset the score if asked to by rosetta
            reset_selector = "div[data-qa='ResetPathModal'] button[data-qa='PromptButton'][type='default']"
            try:
                reset_element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, reset_selector)))

                reset_element.click()
            except Exception:
                pass # Rosetta did not asked us to reset
            
            error_selector = "span[data-qa='error_5414']"
            try:
                self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, error_selector)))
                print("Please disconnect from all your sessions and try again in a few minutes")
                return False
            
            except Exception:
                pass

            # Refuse the use of microphone
            microphone_selector = "button[data-qa='PromptButton'][type='default']"
            microphone_element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, microphone_selector)))
            microphone_element.click()
            
            try:
                # Select voice type if asked
                voice_type_selector = "span[data-qa='misc_cancel']"
                voice_type_element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, voice_type_selector)))
                self.driver.execute_script("arguments[0].click();", voice_type_element)
            except Exception:
                # We were not asked to select voice type, pass
                pass

            # Check if the lesson was started successfuly
            skip_selector = "div[data-qa='skip']"
            try:
                self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, skip_selector)))
                return True
            
            except Exception:
                return False
        except Exception:
            return False

    def loop(self) -> None:
        skip_selector = "div[data-qa='skip']"
        repeat_selector = "button[data-qa='RepeatButton']"

        while self.looping:
            try:
                try: # Rosetta ask us to re-do the course
                    repeat_element = self.wait_course.until(EC.element_to_be_clickable((By.CSS_SELECTOR, repeat_selector)))
                    repeat_element.click()
                    
                except Exception: # Rosetta didn't asked us to re-do the course
                    skip_element = self.driver.find_element(By.CSS_SELECTOR, skip_selector)
                    skip_element.click()

            except Exception: # Avoid using all CPU while page is loading
                sleep(1)

        return
        
    def get_run_time_str(self) -> str:
        run_time = round(time() - self.start_time)

        hours = run_time // 3600
        mins = (run_time % 3600) // 60
        secs = run_time % 60
        
        return f"{hours}h:{mins}m:{secs}s"
        
    def main(self, email: str, password: str):
        self.driver = webdriver.Chrome(options=self.options)
        self.wait = WebDriverWait(self.driver, self.timeout)
        self.wait_course = WebDriverWait(self.driver, self.course_time)
        try:
            print("Attempting to login into Rosetta (This can take up to 20sec with default timeout)")
            if not self.login(email, password):
                print("Login was unsuccessful, maybe the email or password is incorrect. You can also try to increase the timeout.")
                return
            print("Login to Rosetta was successful !")

            print("Attempting to start the lesson (This can take up to 40sec with default timeout)")
            if not self.start_lesson():
                print("Could not start the lesson, try increasing the timeout")
                return
            print("The lesson was successfuly started !")

            print("Starting the lesson loop")

            self.looping = True
            loop_thread = Thread(target=self.loop)
            loop_thread.start()

            
            self.start_time = time()
            while self.looping:
                inp = input("Type 'q' to quit or 't' to display how long the program has been running : ")
                if  inp == "q":
                    print("Exiting")
                    self.looping = False
                    loop_thread.join()

                elif inp == "t":
                    print(f"The program has been running for {self.get_run_time_str()}.")

            self.driver.quit()
            
        except Exception as e:
            print(f"There was an error while looping throught the courses. Error : {e}")


if __name__ == "__main__":
    if len(argv) == 3:
        rosetta = Rosetta()
        rosetta.main(argv[1], argv[2])
    else:
        print("Usage : path_to_rosetta.py email password")

