# model_download.py
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os

# 1) 허깅페이스에 공개되어 있는 감정분석 모델
MODEL_NAME = "nlp04/korean_sentiment_analysis_kcelectra"

# 2) 로컬에 저장할 폴더 경로 (본인이 사용할 로컬 주소로 변경할 것)
SAVE_DIR = r"C:\Users\CGB\korean_sentiment_kcelectra"

os.makedirs(SAVE_DIR, exist_ok=True)

print(f"▼ 모델 다운로드 시작: {MODEL_NAME}")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

tokenizer.save_pretrained(SAVE_DIR)
model.save_pretrained(SAVE_DIR)
print(f"다운로드 완료, 여기 저장됨: {SAVE_DIR}")
