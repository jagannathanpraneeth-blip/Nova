# 🧠 Nova LLM Upgrade Complete!

Nova is now powered by **Large Language Models (LLMs)**!

## 🌟 What's New?
1.  **Universal Decision Engine**: Nova now uses an LLM (OpenAI or Gemini) to understand *any* command, not just hardcoded ones.
2.  **Multi-Model Support**: You can use **Google Gemini** (Free tier available) or **OpenAI GPT-4o**.
3.  **Vision Upgrade**: Screen analysis now works with Gemini too.
4.  **Complex Reasoning**: Nova can now plan multiple steps ("Open Chrome and search for cats") using its new brain.

## 🛠️ How to Enable
1.  **Install Requirements**:
    ```powershell
    pip install -r requirements.txt
    ```
2.  **Add Your Key**:
    - For **Gemini**: Run `setup_gemini_key.bat`
    - For **OpenAI**: Run `setup_api_key.bat`

## 🤖 How it Works
- **Processing**: Every command is sent to the LLM.
- **Decision**: The LLM decides which tool to use (Open App, Search, Mouse, System, etc.).
- **Execution**: The mapped tool is executed.

## 📝 Example Commands
- "Nova, open Chrome and find the best pizza place nearby" (Multitask + Search)
- "Nova, analyze this screen" (Vision)
- "Nova, what should I do next?" (Task Suggestion via LLM)
- "Nova, turn up the volume" (System Command)

Enjoy your super-smart assistant! 🚀
