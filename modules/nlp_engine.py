import spacy
import logging
import json
import os
from modules.utils import load_json, DATA_DIR

class NLPEngine:
    def __init__(self):
        self.logger = logging.getLogger('NLPEngine')
        self.intents = load_json(os.path.join(DATA_DIR, 'intents.json'))
        self.commands = load_json(os.path.join(DATA_DIR, 'commands.json'))
        
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.logger.info("Spacy model loaded successfully.")
        except OSError:
            self.logger.warning("Spacy model 'en_core_web_sm' not found. Please download it using: python -m spacy download en_core_web_sm")
            self.nlp = None

    def classify_intent(self, text):
        text = text.lower()
        
        # 1. Check exact command mappings first (highest priority)
        for intent_name, phrases in self.commands.items():
            for phrase in phrases:
                if phrase in text:
                    return intent_name, 1.0

        # 2. Check general intents
        best_intent = None
        max_score = 0
        
        for intent in self.intents.get('intents', []):
            for pattern in intent['patterns']:
                # Simple similarity score (Jaccard or substring)
                # For better results, use spacy similarity if model is loaded
                score = self._calculate_similarity(text, pattern)
                if score > max_score:
                    max_score = score
                    best_intent = intent['tag']
        
        if max_score > 0.5:
            return best_intent, max_score
            
        return "unknown", 0.0

    def _calculate_similarity(self, text1, text2):
        if self.nlp:
            doc1 = self.nlp(text1)
            doc2 = self.nlp(text2)
            return doc1.similarity(doc2)
        else:
            # Fallback: simple word overlap
            words1 = set(text1.split())
            words2 = set(text2.split())
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            return len(intersection) / len(union) if union else 0

    def extract_entities(self, text):
        if not self.nlp:
            return {}
            
        doc = self.nlp(text)
        entities = {}
        for ent in doc.ents:
            entities[ent.label_] = ent.text
        return entities
