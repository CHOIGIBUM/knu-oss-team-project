import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Any, Dict

from .utils import get_robust_transcript, clean_json_text

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("경고: .env 파일에 GEMINI_API_KEY가 없습니다.")
else:
    genai.configure(api_key=API_KEY)

# 모델 설정
CREATIVE_MODEL_NAME = "gemini-2.5-pro"
SUMMARY_MODEL_NAME = "gemini-2.5-flash"


class VideoAnalyst:
    """
    유튜브 영상 자막을 기반으로
    - 요약/챕터/키워드 추출
    - 2차 창작(블로그/쇼츠 스크립트) 생성
    을 담당하는 에이전트 클래스
    """

    def __init__(self) -> None:
        self.api_key_exists = bool(API_KEY)

        # 공통 safety 설정
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        # 요약용 / 창작용 따로 온도 설정
        self.summary_generation_config = {
            "temperature": 0.3,  # 요약은 재현성/안정성 위주
            "response_mime_type": "application/json",
        }

        self.creative_generation_config = {
            "temperature": 0.9,  # 창작은 다양성/창의성 위주
            "response_mime_type": "application/json",
        }

    # -------------------------------
    # 내부 유틸: 공통 JSON 파싱 함수
    # -------------------------------
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Gemini 응답을 JSON으로 파싱.
        - 1차: 그대로 json.loads
        - 2차: ```json / ``` 제거 등 clean 후 재시도
        - 실패 시 에러 정보 반환
        """
        try:
            return json.loads(response_text)
        except Exception:
            try:
                cleaned = clean_json_text(response_text)
                return json.loads(cleaned)
            except Exception as e:
                return {
                    "error": f"JSON 파싱 실패: {str(e)}",
                    "raw_response_preview": response_text[:500],
                }

    # -------------------------------
    # [Module 1] 요약 에이전트
    # -------------------------------
    def summarize(self, video_id: str) -> Dict[str, Any]:
        """영상 자막 기반 요약/챕터/키워드 추출"""

        if not self.api_key_exists:
            return {"error": "GEMINI_API_KEY가 설정되지 않았습니다."}

        text = get_robust_transcript(video_id)
        if not text:
            return {"error": "자막을 가져올 수 없습니다. (자막 미지원 영상 또는 추출 실패)"}

        model = genai.GenerativeModel(
            model_name=SUMMARY_MODEL_NAME,
            generation_config=self.summary_generation_config,
            safety_settings=self.safety_settings,
        )

        prompt = f"""
너는 유튜브 영상의 자막을 기반으로 콘텐츠를 분석하는 **전문 영상 분석가**이다.

아래 [TRANSCRIPT] 구간만을 근거로 분석하여, **정확한 JSON만** 출력하라.
- 자막에 명시되지 않은 정보는 추측해서 만들지 말 것.
- 설명 문장, 마크다운, ```json 등의 코드블록은 절대 포함하지 말 것.
- 모든 값은 **자연스러운 한국어**로 작성할 것.

[요청사항]
1. summary_3lines
   - 영상 전체 내용을 3문장으로 핵심만 요약한다.
   - 각 문장은 최대 40자 내외로 간결하게 작성한다.
   - 서로 다른 내용을 담도록 중복을 피한다.

2. chapters
   - 영상 흐름을 2~6개 구간으로 나눈다.
   - time 필드는 "초반", "중반", "후반", "도입부", "결론부" 등
     **상대적인 흐름 표현**만 사용한다. (구체적인 분 단위/초 단위 시간은 쓰지 않는다.)
   - title은 해당 구간의 내용을 한 문장으로 요약한 소제목 형태로 작성한다.

3. keywords
   - 영상의 핵심 주제를 나타내는 명사/구를 3~8개 추출한다.
   - 의미가 거의 같은 표현(예: "유튜브", "유튜브 플랫폼")은 하나로 통합한다.
   - 불필요하게 일반적인 단어(예: "영상", "설명")는 피하고,
     이 영상만의 특성을 드러낼 수 있는 단어를 우선한다.

[출력 JSON 스키마]  (필드명은 절대 바꾸지 말 것)
{{
  "summary_3lines": ["문장1", "문장2", "문장3"],
  "chapters": [
    {{"time": "초반", "title": "소제목1"}},
    {{"time": "중반", "title": "소제목2"}}
  ],
  "keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"]
}}

위 스키마를 반드시 그대로 따르고, 추가 필드나 주석을 넣지 마라.

[TRANSCRIPT]
{text}
[END_TRANSCRIPT]
        """

        try:
            response = model.generate_content(prompt)
            return self._parse_json_response(response.text)
        except Exception as e:
            return {"error": f"AI 분석 실패: {str(e)}"}

    # -------------------------------
    # [Module 2] 창작 에이전트
    # -------------------------------
    def create_content(self, video_id: str) -> Dict[str, Any]:
        """영상 자막 기반 2차 창작 (블로그 글 + 쇼츠 스크립트)"""

        if not self.api_key_exists:
            return {"error": "GEMINI_API_KEY가 설정되지 않았습니다."}

        text = get_robust_transcript(video_id)
        if not text:
            return {"error": "자막 데이터가 없어 콘텐츠를 생성할 수 없습니다."}

        model = genai.GenerativeModel(
            model_name=CREATIVE_MODEL_NAME,
            generation_config=self.creative_generation_config,
            safety_settings=self.safety_settings,
        )

        prompt = f"""
너는 100만 구독자를 보유한 **한국어 유튜브 인플루언서**이자
블로그·쇼츠 콘텐츠 제작에 능숙한 크리에이터다.

아래 [TRANSCRIPT] 내용만을 바탕으로,
블로그 글과 쇼츠 대본을 **JSON 형식**으로 생성하라.

[필수 원칙]
- 자막에 없는 내용을 과도하게 지어내지 말고, 영상의 실제 메시지를 우선 반영한다.
- 응답은 JSON만 포함하며, ```json 같은 마크다운 코드는 쓰지 않는다.
- 모든 텍스트는 자연스러운 한국어로 작성한다.

[콘텐츠 요구사항]

1. blog_post
   - title:
     - 클릭을 유도하는 매력적인 제목.
     - 과도한 낚시보다는, 영상의 핵심 가치를 분명하게 드러낼 것.
   - content:
     - 마크다운 형식 사용 (예: #, ##, **강조**, 목록 등).
     - 구조 예시:
       - 도입부: 독자의 공감을 끌어내는 문제 제기 또는 질문
       - 본문: 영상의 핵심 내용과 인사이트 정리
       - 정리: 시청/실천을 유도하는 마무리 멘트
     - 분량: 일반 블로그 포스트 기준 **3~7개 소제목** 정도 길이.
     - 문단은 2~4문장 정도로 끊어서 가독성을 높인다.

2. shorts_script (60초 분량)
   - 형식: 한 줄씩 "화면 설명 + 나레이션" 형태로 작성.
   - 예시:
     - "[화면] 노트북 화면 클로즈업 / [나레이션] 유튜브 알고리즘, 어떻게 공략해야 할까요?"
   - 전체 길이는 약 8~15줄 정도로,
     실제 60초 내에 말할 수 있는 분량을 목표로 한다.
   - 초반 3초 안에 강한 훅(hook)을 넣어서 시청자의 이탈을 막는다.
   - 영상의 핵심 메시지 또는 액션(구독/댓글/실천)을 마지막에 한 번 더 강조한다.

[출력 JSON 스키마]  (필드명은 절대 바꾸지 말 것)
{{
  "blog_post": {{
    "title": "클릭을 유도하는 제목",
    "content": "마크다운 형식의 본문 (## 소제목, **강조** 포함)"
  }},
  "shorts_script": "60초 분량 쇼츠 대본 (각 줄에 화면 설명과 나레이션 포함)"
}}

위 스키마 이외의 필드는 추가하지 말고,
문자열 내부에만 마크다운을 사용하라.

[TRANSCRIPT]
{text}
[END_TRANSCRIPT]
        """

        try:
            response = model.generate_content(prompt)
            return self._parse_json_response(response.text)
        except Exception as e:
            return {"error": f"콘텐츠 생성 실패: {str(e)}"}
