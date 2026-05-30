# Rosetta AFK

A lightweight, fully automated injection bot for Rosetta Stone (Foundations).

Shoutout to the `RosettaStonks` repository for the initial API research, but **we automated everything**. 

There is no need to install any browser extensions, click around, or manually intercept requests. This script uses a headless browser to log in, grabs your official session tokens, and directly injects the time into the API using pure Python. Clean, fast, and zero-interaction.

### Requirements
* **Google Chrome** installed on your machine.
* **Python 3.x** (Yes, you need that too, crazy right?).

### How to use

1. **Clone the repository**
2. **Install the dependencies:**
```bash
   pip install -r requirements.txt
```

3. **Run the script:**
```bash
python rosetta.py <rosetta_email> <rosetta_password> <time_in_seconds>
```
4. **Leave it in the background and go back to doing more useful stuff**
