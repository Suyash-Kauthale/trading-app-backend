# app/routes/llm_chat.py

"""
Multi-Provider LLM Chat Assistant Routes

Supports: OpenAI, Google Gemini, Perplexity
Endpoints:
- POST /api/llm/chat - Chat with selected LLM provider
"""

from fastapi.middleware.cors import CORSMiddleware  
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Literal, Dict
from datetime import datetime
import httpx
import os
from collections import defaultdict
import time

from app.auth import get_current_user_id

router = APIRouter(prefix="/api/llm", tags=["llm-chat"])

# ============ CONFIGURATION ============

class Settings:
    """LLM API Settings from environment variables"""
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
    
    # API Endpoints
    OPENAI_URL = "https://api.openai.com/v1/chat/completions"
    GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"
    
    # Rate limiting: max requests per user per minute
    RATE_LIMIT_PER_MINUTE = 10
    RATE_LIMIT_PER_DAY = 100

settings = Settings()

# ============ RATE LIMITING ============

class RateLimiter:
    """Simple in-memory rate limiter"""
    def __init__(self):
        self.minute_tracker: Dict[int, list] = defaultdict(list)
        self.day_tracker: Dict[int, list] = defaultdict(list)
    
    def check_limit(self, user_id: int) -> tuple[bool, str]:
        """Check if user is within rate limits"""
        now = time.time()
        
        # Clean old entries (older than 1 minute)
        self.minute_tracker[user_id] = [
            ts for ts in self.minute_tracker[user_id] 
            if now - ts < 60
        ]
        
        # Clean old entries (older than 24 hours)
        self.day_tracker[user_id] = [
            ts for ts in self.day_tracker[user_id] 
            if now - ts < 86400
        ]
        
        # Check minute limit
        if len(self.minute_tracker[user_id]) >= settings.RATE_LIMIT_PER_MINUTE:
            return False, f"Rate limit exceeded: {settings.RATE_LIMIT_PER_MINUTE} requests per minute"
        
        # Check day limit
        if len(self.day_tracker[user_id]) >= settings.RATE_LIMIT_PER_DAY:
            return False, f"Daily limit exceeded: {settings.RATE_LIMIT_PER_DAY} requests per day"
        
        # Add current timestamp
        self.minute_tracker[user_id].append(now)
        self.day_tracker[user_id].append(now)
        
        return True, ""

rate_limiter = RateLimiter()

# ============ SCHEMAS ============

class ChatRequest(BaseModel):
    provider: Literal["openai", "gemini", "perplexity"] = Field(
        ..., 
        description="LLM provider to use"
    )
    question: str = Field(
        ..., 
        min_length=1, 
        max_length=2000,
        description="User question"
    )

class ChatResponse(BaseModel):
    provider: str
    answer: str
    timestamp: datetime
    tokens_used: int = 0

# ============ LLM PROVIDER HELPERS ============

class OpenAIProvider:
    """OpenAI/ChatGPT API Integration"""
    
    @staticmethod
    async def chat(question: str) -> dict:
        """Call OpenAI Chat Completions API"""
        if not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured"
            )
        
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o-mini",  # Cost-effective model
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant for a trading platform. Provide clear, concise answers."
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    settings.OPENAI_URL,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 401:
                    raise HTTPException(status_code=500, detail="Invalid OpenAI API key")
                elif response.status_code == 429:
                    raise HTTPException(status_code=429, detail="OpenAI rate limit exceeded")
                elif response.status_code != 200:
                    raise HTTPException(
                        status_code=500,
                        detail=f"OpenAI API error: {response.text}"
                    )
                
                data = response.json()
                answer = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", 0)
                
                return {
                    "answer": answer.strip(),
                    "tokens_used": tokens
                }
        
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="OpenAI request timeout")
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"OpenAI network error: {str(e)}")


class GeminiProvider:
    """Google Gemini API Integration"""
    
    @staticmethod
    async def chat(question: str) -> dict:
        """Call Google Gemini API"""
        if not settings.GEMINI_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="Gemini API key not configured"
            )
        
        # ✅ SUCCESS: Using the working Lite model
        MODEL_NAME = "gemini-2.5-flash-lite"
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={settings.GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"You are a helpful AI assistant for a trading platform. Answer this question concisely:\n\n{question}"
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 500
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                
                # specific error handling for debugging
                if response.status_code == 404:
                     raise HTTPException(status_code=500, detail=f"Model {MODEL_NAME} not found. Check API key.")
                elif response.status_code == 429:
                    raise HTTPException(status_code=429, detail="Gemini rate limit exceeded")
                elif response.status_code != 200:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Gemini API error: {response.text}"
                    )
                
                data = response.json()
                
                # Extract answer safely
                try:
                    answer = data["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError):
                    raise HTTPException(status_code=500, detail="Invalid response structure from Gemini")
                
                # Estimate tokens
                tokens = len(answer.split()) * 1.3
                
                return {
                    "answer": answer.strip(),
                    "tokens_used": int(tokens)
                }
        
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Gemini request timeout")
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Gemini network error: {str(e)}")

class PerplexityProvider:
    """Perplexity AI API Integration"""
    
    @staticmethod
    async def chat(question: str) -> dict:
        """Call Perplexity Chat API"""
        if not settings.PERPLEXITY_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="Perplexity API key not configured"
            )
        
        headers = {
            "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-sonar-small-128k-online",  # Online model for real-time info
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant for a trading platform. Provide accurate, up-to-date information."
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    settings.PERPLEXITY_URL,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 401:
                    raise HTTPException(status_code=500, detail="Invalid Perplexity API key")
                elif response.status_code == 429:
                    raise HTTPException(status_code=429, detail="Perplexity rate limit exceeded")
                elif response.status_code != 200:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Perplexity API error: {response.text}"
                    )
                
                data = response.json()
                answer = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", 0)
                
                return {
                    "answer": answer.strip(),
                    "tokens_used": tokens
                }
        
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Perplexity request timeout")
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Perplexity network error: {str(e)}")


# ============ MAIN ENDPOINT ============

@router.post("/chat", response_model=ChatResponse)
async def chat_with_llm(
    request: ChatRequest,
    user_id: int = Depends(get_current_user_id)
):
    """
    Chat with selected LLM provider
    
    Supports:
    - openai: GPT-4o-mini (fast, cost-effective)
    - gemini: Google Gemini Pro
    - perplexity: Llama 3.1 Sonar (online, real-time info)
    
    Rate limits: 10/min, 100/day per user
    """
    
    # Rate limiting check
    allowed, error_msg = rate_limiter.check_limit(user_id)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_msg
        )
    
    # Route to appropriate provider
    try:
        if request.provider == "openai":
            result = await OpenAIProvider.chat(request.question)
        elif request.provider == "gemini":
            result = await GeminiProvider.chat(request.question)
        elif request.provider == "perplexity":
            result = await PerplexityProvider.chat(request.question)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider: {request.provider}"
            )
        
        return ChatResponse(
            provider=request.provider,
            answer=result["answer"],
            timestamp=datetime.now(),
            tokens_used=result["tokens_used"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/status")
async def check_api_status():
    """Check which LLM providers are configured"""
    return {
        "openai": bool(settings.OPENAI_API_KEY),
        "gemini": bool(settings.GEMINI_API_KEY),
        "perplexity": bool(settings.PERPLEXITY_API_KEY),
        "rate_limits": {
            "per_minute": settings.RATE_LIMIT_PER_MINUTE,
            "per_day": settings.RATE_LIMIT_PER_DAY
        }
    }