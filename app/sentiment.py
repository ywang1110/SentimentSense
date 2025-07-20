"""
情感分析核心逻辑模块
"""
import time
import logging
from typing import List, Tuple
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch

from .config import settings

# 配置日志
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """情感分析器类"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.classifier = None
        self.model_loaded = False
        self._load_model()
    
    def _load_model(self):
        """Load HuggingFace model"""
        try:
            logger.info(f"Loading model: {settings.MODEL_NAME}")
            start_time = time.time()
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(settings.MODEL_NAME)
            self.model = AutoModelForSequenceClassification.from_pretrained(settings.MODEL_NAME)
            
            # Create classification pipeline
            self.classifier = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1,  # Use GPU if available
                return_all_scores=True
            )
            
            self.model_loaded = True
            load_time = time.time() - start_time
            logger.info(f"Model loaded successfully in {load_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            self.model_loaded = False
            raise
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text"""
        # Basic text cleaning
        text = text.strip()
        
        # Limit text length
        if len(text) > settings.MAX_TEXT_LENGTH:
            text = text[:settings.MAX_TEXT_LENGTH]
            logger.warning(f"Text truncated to {settings.MAX_TEXT_LENGTH} characters")
        
        return text
    
    def _postprocess_result(self, result: List[dict]) -> Tuple[str, float]:
        """Post-process model output results"""
        # Get scores for all labels
        scores = {item['label']: item['score'] for item in result}
        
        # Map labels to standard format
        label_mapping = {
            'LABEL_0': 'NEGATIVE',
            'LABEL_1': 'NEUTRAL',
            'LABEL_2': 'POSITIVE',
            'NEGATIVE': 'NEGATIVE',
            'POSITIVE': 'POSITIVE',
            # Handle lowercase labels
            'negative': 'NEGATIVE',
            'positive': 'POSITIVE',
            'neutral': 'NEUTRAL'
        }
        
        # Find the label with highest score
        best_label = max(scores.keys(), key=lambda k: scores[k])
        best_score = scores[best_label]
        
        # Map to standard label
        sentiment = label_mapping.get(best_label, best_label)
        
        # Special handling for neutral labels
        if 'NEUTRAL' in [label_mapping.get(k, k) for k in scores.keys()]:
            # For three-class models, classify neutral as positive or negative with lower confidence
            if sentiment == 'NEUTRAL':
                pos_score = scores.get('LABEL_2', scores.get('POSITIVE', scores.get('positive', 0)))
                neg_score = scores.get('LABEL_0', scores.get('NEGATIVE', scores.get('negative', 0)))
                
                if pos_score > neg_score:
                    sentiment = 'POSITIVE'
                    best_score = pos_score
                else:
                    sentiment = 'NEGATIVE'
                    best_score = neg_score
        
        return sentiment, best_score
    
    def analyze_single(self, text: str) -> Tuple[str, float, float]:
        """
        Analyze sentiment of a single text

        Args:
            text: Text to analyze

        Returns:
            Tuple[sentiment, confidence, processing_time]
        """
        if not self.model_loaded:
            raise RuntimeError("Model not loaded")
        
        start_time = time.time()
        
        try:
            # Preprocess text
            processed_text = self._preprocess_text(text)
            
            # Perform sentiment analysis
            result = self.classifier(processed_text)
            
            # Post-process results
            sentiment, confidence = self._postprocess_result(result[0])
            
            processing_time = time.time() - start_time
            
            logger.debug(f"Analysis completed: '{text[:50]}...' -> {sentiment} ({confidence:.4f})")
            
            return sentiment, confidence, processing_time
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            raise
    
    def analyze_batch(self, texts: List[str]) -> List[Tuple[str, float, float]]:
        """
        Batch analyze text sentiment

        Args:
            texts: List of texts to analyze

        Returns:
            List[Tuple[sentiment, confidence, processing_time]]
        """
        if not self.model_loaded:
            raise RuntimeError("Model not loaded")

        if len(texts) > settings.BATCH_SIZE_LIMIT:
            raise ValueError(f"Batch size exceeds limit: {len(texts)} > {settings.BATCH_SIZE_LIMIT}")
        
        results = []
        
        for text in texts:
            try:
                sentiment, confidence, processing_time = self.analyze_single(text)
                results.append((sentiment, confidence, processing_time))
            except Exception as e:
                logger.error(f"Single text failed in batch analysis: {str(e)}")
                # Return default values for failed text
                results.append(("NEGATIVE", 0.0, 0.0))
        
        return results
    
    def is_healthy(self) -> bool:
        """Check if analyzer is healthy"""
        return self.model_loaded and self.classifier is not None


# Global analyzer instance
analyzer = SentimentAnalyzer()
