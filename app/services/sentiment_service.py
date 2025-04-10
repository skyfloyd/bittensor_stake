import aiohttp
import json
from typing import Dict, List, Any
from datetime import datetime, timedelta
from ..core.config import get_settings

settings = get_settings()

class SentimentError(Exception):
    """Base exception for sentiment analysis errors."""
    pass

class TwitterAPIError(SentimentError):
    """Raised when there are issues with the Twitter API."""
    pass

class LLMAPIError(SentimentError):
    """Raised when there are issues with the LLM API."""
    pass

class SentimentService:
    def __init__(self):
        self.datura_api_key = settings.DATURA_API_KEY
        self.datura_api_url = settings.DATURA_API_URL
        self.chutes_api_key = settings.CHUTES_API_KEY
        self.chutes_api_url = settings.CHUTES_API_URL
        
    async def get_twitter_sentiment(self, search_term: str) -> Dict[str, Any]:
        """
        Get sentiment data from Twitter for a specific search term.
        
        Args:
            search_term: The term to search for on Twitter
            
        Returns:
            Dict containing sentiment data and tweets
        """
        try:
            if not self.datura_api_key:
                raise TwitterAPIError("Datura API key not found in settings")
            
            # Calculate date range (last 7 days)
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": self.datura_api_key,
                    "Content-Type": "application/json"
                }
                
                params = {
                    "query": search_term
                }
                
                async with session.get(self.datura_api_url, headers=headers, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise TwitterAPIError(f"Twitter API error: {error_text}")
                    
                    data = await response.json()
                    
                    if not data:
                        return {
                            "success": False,
                            "search_term": search_term,
                            "sentiment_score": 0,
                            "tweet_count": 0,
                            "tweets": [],
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "error": "No tweets found for this search term"
                        }
                    
                    # Extract tweets for LLM analysis
                    tweets = [tweet["text"] for tweet in data]
                    
                    # Get sentiment score from LLM
                    sentiment_score = await self._analyze_sentiment_with_llm(tweets)
                    
                    return {
                        "success": True,
                        "search_term": search_term,
                        "sentiment_score": sentiment_score,
                        "tweet_count": len(tweets),
                        "tweets": tweets,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                    
        except Exception as e:
            raise SentimentError(f"Error getting Twitter sentiment: {str(e)}")
    
    async def _analyze_sentiment_with_llm(self, tweets: List[str]) -> int:
        """
        Analyze sentiment of tweets using Chutes.ai LLM.
        
        Args:
            tweets: List of tweet texts to analyze
            
        Returns:
            Sentiment score from -100 to +100
        """
        try:
            if not self.chutes_api_key:
                raise LLMAPIError("Chutes API key not found in settings")
                
            # Prepare the prompt for sentiment analysis
            prompt = f"""
            Analyze the sentiment of the following tweets and provide a sentiment score from -100 to +100.
            -100 means extremely negative sentiment
            0 means neutral sentiment
            +100 means extremely positive sentiment
            
            Tweets:
            {json.dumps(tweets, indent=2)}
            
            Provide only a number as your response, representing the sentiment score.
            """
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.chutes_api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "llama-3-8b-instruct",
                    "messages": [
                        {"role": "system", "content": "You are a sentiment analysis expert. Analyze the sentiment of tweets and provide a score from -100 to +100."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 10
                }
                
                async with session.post(self.chutes_api_url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        error_data = json.loads(error_text) if error_text else {}
                        
                        # Check for specific error about no matching chute
                        if "detail" in error_data and "No matching chute found" in error_data["detail"]:
                            # Fallback to simple sentiment analysis
                            return self._simple_sentiment_analysis(tweets)
                        
                        raise LLMAPIError(f"LLM API error: {error_text}")
                    
                    data = await response.json()
                    
                    if "choices" not in data or not data["choices"]:
                        raise LLMAPIError("No response from LLM API")
                    
                    # Extract the sentiment score from the LLM response
                    sentiment_text = data["choices"][0]["message"]["content"].strip()
                    
                    try:
                        # Try to parse the sentiment score as an integer
                        sentiment_score = int(sentiment_text)
                        
                        # Ensure the score is within the valid range
                        sentiment_score = max(-100, min(100, sentiment_score))
                        
                        return sentiment_score
                    except ValueError:
                        # If the response is not a valid integer, try to extract a number
                        import re
                        numbers = re.findall(r'-?\d+', sentiment_text)
                        if numbers:
                            sentiment_score = int(numbers[0])
                            sentiment_score = max(-100, min(100, sentiment_score))
                            return sentiment_score
                        else:
                            # Fallback to simple sentiment analysis
                            return self._simple_sentiment_analysis(tweets)
                    
        except LLMAPIError:
            raise
        except Exception as e:
            # Fallback to simple sentiment analysis
            return self._simple_sentiment_analysis(tweets)
    
    def _simple_sentiment_analysis(self, tweets: List[str]) -> int:
        """
        Simple fallback sentiment analysis when LLM API fails.
        
        Args:
            tweets: List of tweet texts to analyze
            
        Returns:
            Sentiment score from -100 to +100
        """
        # Simple keyword-based sentiment analysis
        positive_keywords = ["good", "great", "amazing", "excellent", "love", "best", "awesome", "perfect", "happy", "positive"]
        negative_keywords = ["bad", "terrible", "awful", "worst", "hate", "disappointed", "negative", "sad", "angry", "frustrated"]
        
        total_score = 0
        tweet_count = len(tweets)
        
        if tweet_count == 0:
            return 0
        
        for tweet in tweets:
            tweet_lower = tweet.lower()
            
            # Count positive keywords
            positive_count = sum(1 for keyword in positive_keywords if keyword in tweet_lower)
            
            # Count negative keywords
            negative_count = sum(1 for keyword in negative_keywords if keyword in tweet_lower)
            
            # Calculate tweet score (-100 to 100)
            if positive_count == 0 and negative_count == 0:
                tweet_score = 0
            else:
                tweet_score = int((positive_count - negative_count) / (positive_count + negative_count) * 100)
            
            total_score += tweet_score
        
        # Calculate average score
        avg_score = total_score / tweet_count
        
        # Ensure score is within range
        return max(-100, min(100, int(avg_score)))
    
    async def get_stake_amount(self, sentiment_score: int) -> float:
        """
        Calculate stake amount based on sentiment score.
        
        Args:
            sentiment_score: Sentiment score from -100 to +100
            
        Returns:
            Stake amount in TAO (0.01 TAO * sentiment score)
        """
        # Convert sentiment score to stake amount (0.01 TAO * sentiment score)
        return 0.01 * abs(sentiment_score) 