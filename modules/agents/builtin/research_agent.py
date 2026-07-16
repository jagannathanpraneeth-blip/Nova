"""
Nova Research Agent
===================
Performs deep research on topics by query lookup, scraping wikipedia,
and synthesizing cohesive reports using LLM reasoning.
"""

import logging
import requests
import json
from typing import Dict, Any

from modules.agents.agent_base import Agent

try:
    import wikipedia
    WIKIPEDIA_AVAILABLE = True
except ImportError:
    WIKIPEDIA_AVAILABLE = False


class ResearchAgent(Agent):
    """Agent responsible for conducting information lookup, scraping wikipedia, and preparing research briefs."""

    def __init__(self, tts=None, **kwargs):
        super().__init__(
            name="ResearchAgent",
            description="Deep information gatherer. Scrapes Wikipedia and web sources, summarizing them into structured research briefs.",
            **kwargs
        )
        self.tts = tts
        self.capabilities = ["research_topic", "summarize_web"]

    def _do_execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = task.get("action", "")
        params = task.get("parameters", {})
        raw_text = params.get("raw_text", task.get("original_text", ""))

        if action == "research_topic":
            topic = params.get("topic", raw_text)
            return self._research_topic(topic)
        elif action == "summarize_web":
            url = params.get("url", "")
            return self._summarize_web(url)

        return {"success": False, "message": f"Unknown action: {action}", "action": action}

    def _research_topic(self, topic: str) -> Dict[str, Any]:
        """Researches a topic using Wikipedia and synthesizes a brief report using the LLM."""
        # Clean trigger phrases
        for trigger in ["research about", "tell me about", "research", "what is", "who is"]:
            if trigger in topic.lower():
                topic = topic.lower().split(trigger, 1)[1].strip()
                break

        if not topic:
            return {"success": False, "message": "No topic specified for research", "action": "research_topic"}

        self.logger.info(f"Researching topic: {topic}")
        if self.tts:
            self.tts.speak(f"Doing some research on {topic}. One moment.")

        summary_text = ""
        source_used = ""

        # 1. Try Wikipedia
        if WIKIPEDIA_AVAILABLE:
            try:
                # Find best page
                search_results = wikipedia.search(topic)
                if search_results:
                    page = wikipedia.page(search_results[0], auto_suggest=False)
                    summary_text = page.content[:4000] # Limit to first 4000 chars for LLM context
                    source_used = page.url
                    self.logger.info(f"Retrieved Wikipedia article: {page.title}")
            except Exception as e:
                self.logger.error(f"Wikipedia search failed: {e}")

        # 2. If Wikipedia failed/unavailable, fall back to duckduckgo search html scrape or direct LLM general knowledge
        if not summary_text:
            # We will query duckduckgo instant answer API or simple JSON API
            try:
                url = f"https://api.duckduckgo.com/?q={topic}&format=json"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    summary_text = data.get("AbstractText", "")
                    if summary_text:
                        source_used = data.get("AbstractURL", "DuckDuckGo Instant Answer")
            except Exception as e:
                self.logger.error(f"DuckDuckGo API search failed: {e}")

        # 3. Use LLM to synthesize report from retrieved summary context, or fallback to LLM direct knowledge
        system_prompt = f"""
        You are an expert researcher. The user wants to know about '{topic}'.
        Synthesize the retrieved raw research data below into a professional, structured research brief.
        Format your response nicely with Markdown, including sections like "Overview", "Key Facts", and "Implications".
        If the data is empty or irrelevant, use your own internal knowledge base to write the brief, but mention you did so.
        Keep it concise and clear.
        """

        prompt = f"Retrieved raw data:\n{summary_text}\n\nSource: {source_used}"

        report = self.ask_llm(prompt, system_prompt)

        if not report:
            # Fallback
            report = f"Research report on {topic}:\nNo details could be fetched. Please check internet connection."

        if self.tts:
            # Speak the first paragraph
            first_para = report.split('\n\n')[0].replace('#', '').strip()
            self.tts.speak(first_para[:150])

        return {
            "success": True,
            "message": report,
            "action": "research_topic",
            "source": source_used
        }

    def _summarize_web(self, url: str) -> Dict[str, Any]:
        """Scrapes a URL and uses LLM to generate a summary."""
        if not url:
            return {"success": False, "message": "No URL provided", "action": "summarize_web"}

        self.logger.info(f"Summarizing web page: {url}")
        if self.tts:
            self.tts.speak("Fetching and summarizing the web page.")

        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                return {"success": False, "message": f"Failed to load page. Status: {response.status_code}", "action": "summarize_web"}

            # Simple html tag stripping to get clean text
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()

            text = soup.get_text()
            # Break into lines and remove leading/trailing whitespace
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            clean_text = "\n".join(chunk for chunk in chunks if chunk)[:3000] # Limit context

            system_prompt = f"You are a summarization bot. Summarize the text from {url} into 3 bullet points."
            summary = self.ask_llm(clean_text, system_prompt)

            if self.tts:
                self.tts.speak("Here is the summary.")

            return {"success": True, "message": summary, "action": "summarize_web"}

        except Exception as e:
            self.logger.error(f"Web scraping error: {e}")
            return {"success": False, "message": str(e), "action": "summarize_web"}
