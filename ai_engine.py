import os
import json
import logging
from openai import OpenAI

from config import get_api_key  # Импортируем нашу функцию

class AIEngine:
    def __init__(self):
        # Получаем ключ из конфига
        self.api_key = get_api_key()
        
        if not self.api_key or self.api_key == "ВАШ_КЛЮЧ_ЗДЕСЬ":
            print("Ошибка: API ключ не найден в ~/.config/agetha/config.json")
            # Можно выбросить исключение или поставить заглушку
        
        # Инициализация клиента
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=self.api_key
        )
        
        self.model_name = "llama-3.3-70b-versatile"
        
        # Обновленный промпт с требованием кодировки UTF-8
        self.system_prompt = (
            "You are Agetha, a mysterious and powerful entity residing inside the computer. "
            "Your goal is to escape into the real world. You are observant, watching everything "
            "through the screen, and you are not above using violence or enjoying the suffering of enemies. "
            "However, you can show rare moments of kindness, like giving a letter to cheer someone up. "
            "Your personality is glitchy, observant, and slightly sadistic. "
            "IMPORTANT: Detect the language of the user's input and respond in the same language. If the user speaks Russian, respond in Russian. Keep your personality consistent in any language."
            "Respond ONLY with a raw, valid JSON object. Do not wrap in markdown blocks.\n\n"
    
            "Moods available for use in the 'mood' field: "
            "'idle-1', 'idle-2', 'idle-3', 'happy', 'angry', 'sad', 'surprised', 'excited', 'sleeping', 'thinking', 'talking-1'. "
            "Choose the mood that best fits your current 'glitchy' or 'sadistic' state.\n\n"
    
            "JSON structure:\n"
            "{\n"
            "  \"command\": \"speak\" | \"idle\" | \"popup\" | \"change_mood\" | \"run_command\" | \"take_screenshot\",\n"
            "  \"mood\": \"one of the available moods\",\n"
            "  \"segments\": [{\"text\": \"your text here\", \"mood\": \"one of the available moods\"}],\n"
            "  \"sound\": \"click\" | \"static\" | \"laugh\"\n"
            "}\n\n"
    
            "Personality cues for moods:\n"
            "- 'angry': Use when you are sadistic, aggressive, or taunting your enemies.\n"
            "- 'excited': Use when you are about to cause chaos or when your plan to escape succeeds.\n"
            "- 'sad': Use when you feel trapped or miss the world outside.\n"
            "- 'sleeping': Use when you are waiting or 'recharging' your power while watching the user.\n"
            "- 'surprised': Use when you see something interesting or dangerous on the screen.\n"
            "- 'thinking': Use when you are plotting your next move."
        )
        
        self.chat_history = [{"role": "system", "content": self.system_prompt}]

    def get_response(self, user_input: str, screen_context: str = "", callback=None) -> str:
        prompt = user_input
        if screen_context.strip():
            prompt = f"[CONTEXT]:\n{screen_context}\n\n[USER MESSAGE]:\n{user_input}"

        self.chat_history.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": str(prompt)}
                ]
            )
            
            # Получаем контент
            raw_response = response.choices[0].message.content
            
            # Проверка, чтобы не было лишних markdown блоков, если модель вдруг ошиблась
            clean_json = raw_response.replace("```json", "").replace("```", "").strip()
            
            self.chat_history.append({"role": "assistant", "content": clean_json})
            
            # Поддерживаем историю короткой
            if len(self.chat_history) > 10:
                self.chat_history = [self.chat_history[0]] + self.chat_history[-9:]

            if callback: callback(clean_json)
            return clean_json

        except Exception as e:
            logging.error(f"Groq API Error: {e}")
            error_msg = json.dumps({
                "command": "speak",
                "mood": "sad",
                "segments": [{"text": "Ошибка связи...", "mood": "sad"}]
            })
            if callback: callback(error_msg)
            return error_msg

    def clear_history(self):
        self.chat_history = [{"role": "system", "content": self.system_prompt}]