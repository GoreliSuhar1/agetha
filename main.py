import os
import sys
import platform
import json
import threading
import random
import time
import pygame
from pathlib import Path
from PIL import Image, ImageSequence

# Настройка драйвера
if platform.system() != "Windows" and platform.system() != "Darwin":
    os.environ["SDL_VIDEODRIVER"] = "wayland"

pygame.init()

# КОНСТАНТЫ
WINDOW_W, WINDOW_H = 340, 510
GIF_W, GIF_H = 340, 300
BASE_DIR = Path(__file__).parent
ASSETS = BASE_DIR / "assets"

from ai_engine import AIEngine
from screen_reader import ScreenReader

class AgethaApp:
    def __init__(self):
        self.ai = AIEngine()
        self.screen_reader = ScreenReader()
        self.pg_screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption("Agetha")
        self.pg_clock = pygame.time.Clock()
        
        self.load_fonts()
        self.load_all_animations()
        
        self.full_text = ""
        self.current_text = ""
        self.char_index = 0
        self.last_char_time = 0
        self.typing_speed = 40
        self.target_mood = "idle-1"
        self.thinking_start_time = 0
        self.is_thinking = False
        
        self.speech_queue = []
        self.is_typing = False
        self.input_text = ""
        self.text_start_time = pygame.time.get_ticks()
        self.set_mood("idle")

        # ЗАПУСК НАБЛЮДАТЕЛЯ (раз в 60 секунд)
        threading.Thread(target=self.screen_observer, daemon=True).start()

    def screen_observer(self):
        """Фоновый поток: читает экран и комментирует (запросы на английском)"""
        while True:
            time.sleep(60) 
            text_on_screen = self.screen_reader.capture_text()
            
            if len(text_on_screen) > 100:
                # Промпт теперь строго на английском
                prompt = f"I am Agetha. I see this on your screen: '{text_on_screen[:500]}'. Briefly comment on this in a friendly way."
                threading.Thread(target=self.ai.get_response, args=(prompt, "", self.on_ai_response), daemon=True).start()

    def check_screen_now(self):
        """Ручная проверка экрана (по F3)"""
        text_on_screen = self.screen_reader.capture_text()
        if len(text_on_screen) > 20:
            prompt = f"Agetha, I asked you to look at my screen. You see: '{text_on_screen[:500]}'. Tell me what you think about this."
            threading.Thread(target=self.ai.get_response, args=(prompt, "thinking", self.on_ai_response), daemon=True).start()
        else:
            self.on_ai_response(json.dumps({"segments": [{"text": "I'm looking, but I don't see anything interesting on the screen.", "mood": "idle"}]}))

    def load_fonts(self):
        self.pg_font = pygame.font.SysFont(None, 24)

    def load_all_animations(self):
        self.pg_animations = {}
        # Загружаем всё, что лежит в папке assets
        for p in ASSETS.glob("*.gif"):
            name = p.stem  # Имя файла без .gif
            self.pg_animations[name] = self._parse_gif_pg(p)
            print(f"[Agetha] Loaded mood: {name}")
        
        self.pg_active_frames = self.pg_animations.get("idle-1", [pygame.Surface((GIF_W, GIF_H))])
        self.frame_idx = 0

    def _parse_gif_pg(self, path):
        im = Image.open(path)
        frames = []
        for f in ImageSequence.Iterator(im):
            f = f.convert("RGBA").resize((GIF_W, GIF_H))
            frames.append(pygame.image.fromstring(f.tobytes(), f.size, "RGBA"))
        return frames

    def set_mood(self, mood):
        if mood == "idle":
            mood = random.choice(["idle-1", "idle-2", "idle-3"])
        elif mood == "talking":
            mood = random.choice(["talking-1", "talking-2", "talking-3"])
            
        new_frames = self.pg_animations.get(mood, self.pg_animations.get("idle-1"))
        if self.pg_active_frames != new_frames:
            self.pg_active_frames = new_frames
            self.frame_idx = 0

    def process_next(self):
        if self.speech_queue:
            seg = self.speech_queue.pop(0)
            self.full_text = seg.get("text", "")
            
            # Получаем эмоцию от нейросети
            mood_from_ai = seg.get("mood", "idle-1").lower()
            
            # Проверяем, есть ли такой файл. Если нет — возвращаем idle-1
            if mood_from_ai in self.pg_animations:
                self.target_mood = mood_from_ai
            else:
                self.target_mood = "idle-1"
            
            self.is_thinking = True
            self.thinking_start_time = pygame.time.get_ticks()
            self.set_mood("thinking") 
            
            self.current_text = ""
            self.char_index = 0
            self.last_char_time = pygame.time.get_ticks()
        else:
            self.full_text = ""
            self.current_text = ""
            self.is_thinking = False
            self.set_mood("idle")

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                    self.is_typing = not self.is_typing
                    self.input_text = ""
                if self.is_typing and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN: self.submit_input()
                    elif event.key == pygame.K_BACKSPACE: self.input_text = self.input_text[:-1]
                    else: self.input_text += event.unicode
            self.draw()
            self.pg_clock.tick(30)

    def submit_input(self):
        threading.Thread(target=self.ai.get_response, args=(self.input_text, "", self.on_ai_response), daemon=True).start()
        self.is_typing = False
        self.input_text = ""

    def on_ai_response(self, json_str):
        try:
            data = json.loads(json_str)
            self.speech_queue = data.get("segments", [])
            self.process_next()
        except: pass

    def draw(self):
        self.pg_screen.fill((30, 30, 46))
        if self.pg_active_frames:
            self.frame_idx = (self.frame_idx + 1) % len(self.pg_active_frames)
            self.pg_screen.blit(self.pg_active_frames[self.frame_idx], (0, 0))

        if self.is_thinking:
            if pygame.time.get_ticks() - self.thinking_start_time > 1000:
                self.is_thinking = False
                self.set_mood("talking")
                self.last_char_time = pygame.time.get_ticks()
        
        elif self.full_text and self.char_index < len(self.full_text):
            now = pygame.time.get_ticks()
            if now - self.last_char_time > self.typing_speed:
                self.char_index += 1
                self.current_text = self.full_text[:self.char_index]
                self.last_char_time = now
                if self.char_index >= len(self.full_text):
                    self.text_start_time = pygame.time.get_ticks()
        
        elif self.full_text and self.char_index >= len(self.full_text):
            self.set_mood(self.target_mood)
            if pygame.time.get_ticks() - self.text_start_time > 10000:
                self.full_text = ""
                self.current_text = ""
                self.set_mood("idle")

        if self.current_text:
            max_width = WINDOW_W - 40
            words = self.current_text.split(' ')
            lines = []
            current_line = ""
            for word in words:
                if self.pg_font.size(current_line + word + " ")[0] < max_width:
                    current_line += word + " "
                else:
                    lines.append(current_line)
                    current_line = word + " "
            lines.append(current_line)
            
            y = GIF_H + 20
            for line in lines:
                if line.strip():
                    surf = self.pg_font.render(line, True, (0, 255, 204))
                    self.pg_screen.blit(surf, (20, y))
                    y += 25

        if self.is_typing:
            pygame.draw.rect(self.pg_screen, (20, 20, 30), (10, WINDOW_H - 40, WINDOW_W - 20, 30))
            t = self.pg_font.render(self.input_text + "_", True, (0, 255, 204))
            self.pg_screen.blit(t, (20, WINDOW_H - 35))
            
        pygame.display.flip()

if __name__ == "__main__":
    AgethaApp().run()