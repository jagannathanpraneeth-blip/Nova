# Architecture

## Overview
Nova is a desktop AI assistant built around a GUI shell, assistant runtime loop, voice input/output modules, and a plugin-based execution system.

## Core Components
### 1. GUI Layer
- Main window (`gui/main_window.py`)
- Dashboard / command center (`gui/dashboard.py`)
- Settings dialog (`gui/settings_dialog.py`)
- Diagnostics dialog (`gui/diagnostics_dialog.py`)

### 2. Voice Layer
- Speech recognition module
- Text-to-speech module
- Wake word handling in the assistant loop

### 3. Intelligence Layer
- NLP / intent handling
- AI brain / LLM integration
- command routing and fallback logic

### 4. Plugin System
- Plugin manager loads and registers plugins
- Plugins expose specific assistant capabilities
- Commands can be routed to plugin handlers

## Agent / Plugin Types
Current system behaves more like a plugin-driven assistant than a strict multi-agent architecture.

Examples include:
- installer-related functionality
- project-related functionality
- social-media-related functionality
- AI / assistant reasoning features

## Execution Flow
1. App starts
2. GUI initializes
3. Core modules initialize (speech, TTS, AI, plugins)
4. Assistant enters listening mode
5. Wake word is detected
6. Spoken input is converted to text
7. Command is classified
8. Built-in logic or plugin executes the task
9. Result is spoken and displayed in the UI

## Communication Model
### Internal flow
- GUI ⇄ Assistant thread
- Assistant thread ⇄ speech/TTS/NLP modules
- Assistant thread ⇄ plugin manager
- Plugin manager ⇄ plugins
- Assistant thread ⇄ AI/LLM layer

## Current Strengths
- modular structure
- plugin-based extensibility
- real desktop runtime
- voice + GUI combination

## Current Weaknesses
- still evolving product focus
- setup/config experience needs more work
- reliability under real-world desktop usage still needs deeper testing
- some legacy identity/logic traces may still exist deeper in the codebase

## Recommended Next Architecture Steps
1. plugin health reporting
2. interactive settings persistence
3. cleaner command execution contracts
4. structured diagnostics and error reporting
5. stronger product focus around one primary use case
