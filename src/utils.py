import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

def get_video_id(url):
    """
    유튜브 URL에서 Video ID를 추출하는 정규식 함수
    """
    if not url:
        return None
    if len(url) == 11 and "http" not in url:
        return url
        
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
        r'(?:shorts\/)([0-9A-Za-z_-]{11})'
    ]
    for p in patterns:
        match = re.search(p, url)
        if match: return match.group(1)
    return None

def get_robust_transcript(video_id):
    """
    자막을 가져오는 함수
    1. 한국어 수동 자막 시도
    2. 한국어 자동 자막 시도
    3. 영어 자막이 있으면 가져와서 한국어로 번역
    4. 그 외 언어도 한국어로 번역 시도
    """
    try:
        # 자막 목록 불러오기
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # 우선순위: 한국어(수동) -> 한국어(자동) -> 영어(번역)
        try:
            # 한국어 자막이 있나? (수동/자동 포함)
            transcript = transcript_list.find_transcript(['ko'])
        except:
            # 없으면 영어 자막을 찾아서 한국어로 번역
            try:
                transcript = transcript_list.find_transcript(['en'])
                transcript = transcript.translate('ko')
            except:
                # 영어도 없으면, '번역 가능한' 아무 자막이나 가져와서 한국어로 번역
                transcript = transcript_list.find_generated_transcript(['en', 'ja', 'es']) # 대표 언어 시도
                transcript = transcript.translate('ko')

        # 텍스트로 변환
        formatter = TextFormatter()
        text_data = formatter.format_transcript(transcript.fetch())
        
        # 너무 길면 자르기 (Gemini 토큰 절약) - 2시간 분량 정도는 거뜬하지만 안전하게
        return text_data[:30000] 

    except Exception as e:
        print(f"자막 추출 실패: {e}")
        return None

def clean_json_text(text):
    """Gemini가 가끔 ```json ... ``` 태그를 붙여서 주는걸 제거"""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text