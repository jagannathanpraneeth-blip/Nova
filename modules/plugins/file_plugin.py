from modules.plugins.base import Plugin
import os
import glob

class FilePlugin(Plugin):
    def handle_command(self, text):
        if "delete" in text and "last" in text and ("file" in text or "download" in text):
            return self.delete_last_download(text)
        return None

    def delete_last_download(self, text):
        """
        Deletes the last downloaded file.
        "Nova delete the last file I downloaded."
        """
        self.core.tts.speak("Checking Downloads folder.")
        
        # 1. Look at Downloads
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        
        # 2. Identify newest file
        # Get list of files with full paths
        files = glob.glob(os.path.join(downloads_path, "*"))
        if not files:
            self.core.tts.speak("Downloads folder is empty.")
            return {"success": False, "message": "No files found", "action": "delete_error"}
            
        # Sort by modification time
        newest_file = max(files, key=os.path.getctime)
        filename = os.path.basename(newest_file)
        
        # 3. Delete it
        # Note: The Safety Layer in AIBrain might catch "delete" before it gets here 
        # if we didn't implement the plugin check *before* the safety check or inside it.
        # In my AIBrain implementation, I put Safety Layer *before* Plugins.
        # So "delete the last file" will trigger the safety check "You are trying to delete...".
        # This is actually DESIRED behavior!
        
        try:
            os.remove(newest_file)
            self.core.tts.speak(f"Deleted {filename}.")
            return {"success": True, "message": f"Deleted {filename}", "action": "delete_file"}
        except Exception as e:
            self.core.logger.error(f"Delete error: {e}")
            self.core.tts.speak("Failed to delete the file.")
            return {"success": False, "message": str(e), "action": "delete_error"}
