import os
import time
import datetime
import logging
from typing import List, Dict, Any, Optional

class FileSearcher:
    """
    Searches for files using natural language queries.
    Supports filename matching, content scanning (for text files),
    and basic time constraints.
    """
    
    def __init__(self):
        self.logger = logging.getLogger('FileSearcher')
        # Default search locations
        self.user_home = os.path.expanduser("~")
        self.search_dirs = [
            os.path.join(self.user_home, "Desktop"),
            os.path.join(self.user_home, "Documents"),
            os.path.join(self.user_home, "Downloads")
        ]
        
    def parse_time_constraint(self, text: str) -> Optional[float]:
        """Convert natural language time to timestamp limit"""
        now = time.time()
        one_day = 86400
        
        if "today" in text:
            return now - one_day
        elif "yesterday" in text:
            return now - (one_day * 2)
        elif "this week" in text:
            return now - (one_day * 7)
        elif "last week" in text:
            return now - (one_day * 14)
        elif "this month" in text:
            return now - (one_day * 30)
        
        return None

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for files matching the query.
        Query analysis:
        - Extracts content keywords
        - Checks for time constraints
        """
        self.logger.info(f"Searching for: {query}")
        
        # 1. Parse Time
        min_timestamp = self.parse_time_constraint(query)
        
        # 2. Extract Keywords (naive assumption: words that aren't stop words)
        stop_words = ["the", "a", "an", "in", "on", "at", "for", "with", "file", "open", "find", "search", "where", "i", "wrote", "my", "about", "show", "me"]
        keywords = [w.lower() for w in query.split() if w.lower() not in stop_words]
        
        if not keywords:
            return []
            
        results = []
        
        # 3. Walk directories
        for search_dir in self.search_dirs:
            if not os.path.exists(search_dir):
                continue
                
            for root, dirs, files in os.walk(search_dir):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    
                    # Skip system/hidden files
                    if filename.startswith('.'):
                        continue
                        
                    # Check Time
                    if min_timestamp:
                        try:
                            mtime = os.path.getmtime(filepath)
                            if mtime < min_timestamp:
                                continue
                        except:
                            continue
                    
                    score = 0
                    
                    # A. Filename Match (High Weight)
                    filename_lower = filename.lower()
                    matches_name = sum(1 for k in keywords if k in filename_lower)
                    if matches_name > 0:
                        score += matches_name * 10
                    
                    # B. Content Match (Text files only)
                    if filename.lower().endswith(('.txt', '.md', '.py', '.json', '.bat', '.csv')):
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                # Read first 2KB only for speed
                                content = f.read(2048).lower()
                                matches_content = sum(1 for k in keywords if k in content)
                                if matches_content > 0:
                                    score += matches_content * 2
                        except:
                            pass
                            
                    if score > 0:
                        results.append({
                            "name": filename,
                            "path": filepath,
                            "score": score,
                            "mtime": time.ctime(os.path.getmtime(filepath))
                        })
                        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:5]  # Return top 5
