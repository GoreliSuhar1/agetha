import google.generativeai as genai
import os

api_key = "AIzaSyBsfwuwtbLWRcS3FPf__kDO9_RiwRfK_AU"
genai.configure(api_key=api_key)

print("Доступные модели:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"- {m.name}")