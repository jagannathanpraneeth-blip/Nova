"""
Nova Autonomous Loop
====================
A background supervisor loop that runs autonomously.
Monitors system resources, tracks active goals, suggests proactive tasks,
and runs self-healing diagnostics to revive failed agents.
"""

import time
import logging
import threading
from typing import Dict, Any, List

from modules.agents.agent_base import AgentState
from modules.agents.agent_registry import AgentRegistry
from modules.agents.memory import SharedMemory
from modules.task_queue import execute_async
from config import APP_NAME


class AutonomousLoop:
    """
    Background supervisor thread running autonomous checks.
    Proactively checks system status and updates memory/agent state.
    """

    def __init__(self, tts_engine=None, orchestrator=None):
        self.logger = logging.getLogger("AutonomousLoop")
        self.tts = tts_engine
        self.orchestrator = orchestrator
        self.registry = AgentRegistry()
        self.memory = SharedMemory()
        
        self.running = False
        self.thread = None
        self.interval = 30  # seconds between health checks
        self.proactive_interval = 300  # seconds between suggestions (5 mins)
        self.last_proactive = time.time()

    def start(self):
        """Start the background autonomous loop."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True, name="AutonomousSupervisor")
        self.thread.start()
        self.logger.info("Autonomous Loop supervisor started.")

    def stop(self):
        """Stop the background autonomous loop."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        self.logger.info("Autonomous Loop supervisor stopped.")

    def _run(self):
        """Main execution loop for background supervision."""
        while self.running:
            try:
                # 1. Self-Healing: Check registry for error states and recover agents
                self._run_self_healing()

                # 2. System Resource Diagnostics
                self._check_system_health()

                # 3. Goal Tracking
                self._check_goals()

                # 4. Proactive suggestions (runs less frequently)
                now = time.time()
                if now - self.last_proactive >= self.proactive_interval:
                    self._generate_proactive_suggestions()
                    self.last_proactive = now

            except Exception as e:
                self.logger.error(f"Supervisor error: {e}", exc_info=True)

            # Sleep in small increments to respond to stop commands quickly
            for _ in range(self.interval):
                if not self.running:
                    break
                time.sleep(1)

    def _run_self_healing(self):
        """Finds agents in ERROR state and resets them to IDLE."""
        for agent_info in self.registry.list_all():
            agent_id = agent_info["agent_id"]
            agent = self.registry.get_agent(agent_id)
            if agent and agent.state == AgentState.ERROR:
                self.logger.warning(f"Supervisor: Healing agent {agent.name} from ERROR state.")
                try:
                    # Reset the error count and try reinitializing
                    agent._error_count = 0
                    agent.initialize()
                    self.logger.info(f"Supervisor: Successfully healed agent {agent.name}.")
                    if self.tts:
                        self.tts.speak(f"System warning resolved. Resurrected agent {agent.name}.")
                except Exception as e:
                    self.logger.error(f"Supervisor: Healing failed for {agent.name}: {e}")

    def _check_system_health(self):
        """Logs CPU and RAM metrics and updates shared memory."""
        import psutil
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent

        self.memory.store("system.metrics", {
            "cpu_percent": cpu,
            "ram_percent": ram,
            "disk_percent": disk,
            "timestamp": time.time()
        })

        # Alert if resources are dangerously high
        if cpu > 90.0:
            self.logger.warning(f"High CPU utilization: {cpu}%")
            self.memory.add_conversation("system", f"High CPU usage warning: {cpu}%")
            if self.tts:
                self.tts.speak("Warning, CPU usage is exceeding ninety percent.")

        if ram > 90.0:
            self.logger.warning(f"High Memory utilization: {ram}%")
            self.memory.add_conversation("system", f"High Memory usage warning: {ram}%")
            if self.tts:
                self.tts.speak("Warning, virtual memory is nearly full.")

    def _check_goals(self):
        """Scans active goals from memory and logs updates."""
        active_goals = self.memory.get_active_goals()
        if not active_goals:
            return

        for gid, goal in active_goals.items():
            self.logger.debug(f"Supervisor checking goal {gid}: {goal['description']}")
            # Simple simulation of goal validation
            # E.g. check tasks completed by agents
            pass

    def _generate_proactive_suggestions(self):
        """Uses LLM to think of helpful suggestions based on system state/history."""
        if not self.orchestrator or not self.orchestrator.llm_engine.provider:
            return

        # Fetch recent metrics and conversation context
        metrics = self.memory.retrieve("system.metrics", {})
        convo_context = self.memory.get_conversation_context(limit=3)
        history = self.memory.get_task_history(limit=5)

        system_prompt = f"""
        You are the proactive thinking module of {APP_NAME}.
        Analyze the current system state, recent user interactions, and tasks.
        Suggest ONE helpful proactive action or advice for the user (Sir).
        Keep it to 1 sentence, witty, concise, and helpful.
        If system metrics look fine, make a suggestion based on task history or workflow automation (e.g. organizing files, checking email).
        Return JSON with:
        {{
            "suggestion": "string suggestion text",
            "trigger_action": "optional_action_name_or_none"
        }}
        """

        prompt = f"System metrics: {metrics}\nRecent context: {convo_context}\nTask history: {history}"

        try:
            decision = self.orchestrator.llm_engine.decide_action(prompt, system_prompt)
            # If a suggestion is returned, log it as an alert
            suggestion = decision.get("response") or decision.get("suggestion")
            if suggestion:
                self.logger.info(f"Proactive advice: {suggestion}")
                self.memory.add_conversation("system", f"Proactive advice: {suggestion}")
                # We can choose to alert the user via voice if they are active,
                # but to avoid being annoying, we just output it to the log and speak it subtly.
                if self.tts:
                    self.tts.speak(f"Suggestion: {suggestion}")
        except Exception as e:
            self.logger.error(f"Failed to generate proactive advice: {e}")
