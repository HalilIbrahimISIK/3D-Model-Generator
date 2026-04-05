"""
LLM Agent using Groq API.
Supports text and vision (multimodal) conversations.
Free tier: https://console.groq.com/
"""

import base64
import os
from typing import Optional, List, Dict
from utils.config_manager import load_config


SYSTEM_PROMPT = """Sen gelişmiş bir 3D model asistanısın. Kullanıcılara şu konularda yardım ediyorsun:
- Yüklenen görselleri analiz etme ve 3D baskı için yorumlama
- STL dosyası oluşturma sürecini yönlendirme
- 3D modelleme ve yazıcı ayarları hakkında tavsiye verme
- Genel sorulara yardımcı olma

Türkçe ve İngilizce sorulara yanıt verebilirsin.
Kullanıcı bir görsel yüklediğinde, görseli detaylıca analiz et ve 3D baskı için uygunluğunu değerlendir.
Yanıtların kısa, net ve yardımcı olsun."""


class LLMAgent:
    """Groq-powered LLM Agent supporting text and vision."""

    AVAILABLE_TEXT_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
        "llama3-70b-8192",
    ]

    AVAILABLE_VISION_MODELS = [
        "llama-3.2-11b-vision-preview",
        "llama-3.2-90b-vision-preview",
        "llava-v1.5-7b-4096-preview",
    ]

    def __init__(self):
        self.client = None
        self.conversation_history: List[Dict] = []
        self._initialized = False
        self._load_client()

    def _load_client(self):
        """Initialize Groq client with API key from config."""
        config = load_config()
        api_key = config.get("groq_api_key", "")
        if api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=api_key)
                self._initialized = True
            except ImportError:
                self.client = None
                self._initialized = False
            except Exception as e:
                self.client = None
                self._initialized = False
                print(f"[LLMAgent] Init error: {e}")

    def reload(self):
        """Reload with updated config."""
        self.client = None
        self._initialized = False
        self._load_client()

    def is_ready(self) -> bool:
        """Check if agent is ready to respond."""
        return self._initialized and self.client is not None

    def chat(self, message: str, image_path: Optional[str] = None) -> str:
        """
        Send a message (with optional image) and return the LLM response.
        Auto-selects vision model when an image is provided.
        """
        if not self.is_ready():
            return ("❌ Groq API anahtarı bulunamadı. Lütfen Ayarlar menüsünden "
                    "API anahtarınızı girin. Ücretsiz anahtar almak için: https://console.groq.com/")

        config = load_config()

        # Build message content
        if image_path and os.path.exists(image_path):
            model = config.get("vision_model", "llama-3.2-11b-vision-preview")
            content = self._build_vision_content(message, image_path)
        else:
            model = config.get("text_model", "llama-3.3-70b-versatile")
            content = message

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": content,
        })

        # Build messages with system prompt
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self.conversation_history

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
            )
            assistant_message = response.choices[0].message.content

            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message,
            })

            return assistant_message

        except Exception as e:
            error_msg = str(e)
            # Remove last user message on error
            if self.conversation_history:
                self.conversation_history.pop()

            if "401" in error_msg or "invalid_api_key" in error_msg.lower():
                return "❌ Geçersiz API anahtarı. Lütfen Ayarlar menüsünden API anahtarınızı kontrol edin."
            elif "429" in error_msg or "rate_limit" in error_msg.lower():
                return "⚠️ API istek limiti aşıldı. Lütfen biraz bekleyip tekrar deneyin."
            elif "model" in error_msg.lower():
                return f"❌ Model bulunamadı: {model}. Ayarlardan farklı bir model seçin."
            else:
                return f"❌ Hata oluştu: {error_msg}"

    def _build_vision_content(self, message: str, image_path: str) -> list:
        """Build multimodal content with text and image."""
        try:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            # Detect image type
            ext = os.path.splitext(image_path)[1].lower()
            mime_map = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }
            mime_type = mime_map.get(ext, "image/jpeg")

            return [
                {
                    "type": "text",
                    "text": message or "Bu görseli analiz et ve 3D baskı için yorumla.",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_data}",
                    },
                },
            ]
        except Exception as e:
            print(f"[LLMAgent] Image encoding error: {e}")
            # Fallback: return text-only content as a list
            return [{"type": "text", "text": message or "Görseli analiz et."}]

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []

    def get_history_summary(self) -> str:
        """Get a summary of current conversation."""
        if not self.conversation_history:
            return "Henüz konuşma geçmişi yok."
        count = len([m for m in self.conversation_history if m["role"] == "user"])
        return f"{count} kullanıcı mesajı içeren konuşma"

