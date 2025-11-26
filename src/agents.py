import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from src.utils import get_robust_transcript, clean_json_text

# 환경변수 로드
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(".env 파일에 GEMINI_API_KEY가 설정되지 않았습니다.")

genai.configure(api_key=API_KEY)

# --- [설정] ---
# gemini-1.5-pro: 창작용
# gemini-1.5-flash: 요약용
CREATIVE_MODEL_NAME = 'gemini-1.5-pro'
SUMMARY_MODEL_NAME = 'gemini-1.5-flash' 

class VideoAnalyst:
    def __init__(self):
        # 안전 설정을 낮춰서 거부되는 답변을 줄임
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

    def summarize(self, video_id):
        """[Module 1] 요약 에이전트 (Flash 사용)"""
        text = get_robust_transcript(video_id)
        if not text:
            return {"error": "자막을 추출할 수 없는 영상입니다. (자막이 아예 없거나 제한된 영상)"}

        model = genai.GenerativeModel(SUMMARY_MODEL_NAME)
        
        prompt = f"""
        너는 전문적인 영상 콘텐츠 분석가야.
        아래 자막 텍스트를 분석해서 JSON 포맷으로 응답해줘.
        
        [입력 텍스트]
        {text}

        [요구사항]
        1. summary_3lines: 영상의 핵심 내용을 3문장으로 요약 (배열)
        2. chapters: 영상의 흐름에 따라 주요 주제가 바뀌는 지점을 3~5개로 구분 (time은 "00:00" 형식이 아니라 대략적인 흐름 설명으로, title은 소제목)
        3. keywords: 영상의 핵심 키워드 5개 (해시태그용)

        응답은 오직 JSON 형식만 반환해.
        """
        
        try:
            response = model.generate_content(prompt, safety_settings=self.safety_settings)
            json_str = clean_json_text(response.text)
            return json.loads(json_str)
        except Exception as e:
            return {"error": f"AI 분석 실패: {str(e)}"}

    def create_content(self, video_id):
        """[Module 2] 창작 에이전트 (Pro 사용 - 고성능)"""
        text = get_robust_transcript(video_id)
        if not text:
            return {"error": "자막 데이터가 없어 콘텐츠를 생성할 수 없습니다."}

        model = genai.GenerativeModel(CREATIVE_MODEL_NAME)
        
        prompt = f"""
        너는 100만 구독자를 보유한 파워 인플루언서야.
        아래 영상 내용을 바탕으로 2차 창작물을 만들어야 해.
        말투는 매우 친근하고, 이모지를 적절히 사용하며, 독자의 흥미를 유발해야 해.
        
        [입력 텍스트]
        {text}

        [요구사항 - JSON 형식 반환]
        1. blog_post: 
           - title: 클릭을 유도하는 자극적인 제목 (Clickbait 스타일)
           - content: 서론(HOOK)-본론(정보)-결론(인사이트) 구조의 마크다운 형식 글. 중요 단어는 볼드체 처리.
        2. shorts_script:
           - 60초 분량의 숏폼 영상 대본
           - 시청 지속 시간을 늘리기 위한 오프닝 멘트 필수
           - (화면 설명)과 [나레이션]을 명확히 구분

        응답은 오직 JSON 형식만 반환해.
        """
        
        try:
            response = model.generate_content(prompt, safety_settings=self.safety_settings)
            json_str = clean_json_text(response.text)
            return json.loads(json_str)
        except Exception as e:
            return {"error": f"콘텐츠 생성 실패: {str(e)}"}