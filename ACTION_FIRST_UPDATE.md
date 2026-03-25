# 🧠 The "Literally Everything" Update

Nova has been upgraded to be an **Action-First** AI. 

## 🚫 No More "Here's how to do it..."
Nova will no longer give you a step-by-step guide on how to install something or change a setting.
**It will just do it.**

## ⚡ New Capabilities

1.  **Unlimited Shell Access**:
    -   Nova can now run **ANY** PowerShell command via the LLM.
    -   "Install Flask" -> Runs `pip install flask`
    -   "Create a new folder called Projects" -> Runs `mkdir Projects`
    -   "Clone this repo..." -> Runs `git clone ...`

2.  **Complex Multitasking**:
    -   "Open Notepad, type a poem, and save it to the desktop."
    -   Nova breaks this down into 3 distinct actions and executes them one by one.

3.  **Direct Execution**:
    -   If you ask "How do I check my IP address?", Nova won't tell you.
    -   It will run `ipconfig` and show you the result.

## 🛡️ Safety Note
Nova now has the power to run any command.
-   Be careful with commands like "Delete everything".
-   The Safety Layer still protects against obvious keywords like `format` or `wipe`.

## 🎮 How to Test
-   "Nova, install the requests library for python"
-   "Nova, create a file called hello.txt with the text 'I am alive'"
-   "Nova, what is my IP address?"
