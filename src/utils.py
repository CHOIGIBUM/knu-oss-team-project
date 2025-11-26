import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

ytt_api = YouTubeTranscriptApi()


def get_video_id(url):
    """유튜브 URL에서 Video ID 추출"""
    if not url:
        return None

    # 이미 11자리 ID만 들어온 경우
    if len(url) == 11 and "http" not in url:
        return url

    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
        r'(?:shorts\/)([0-9A-Za-z_-]{11})',
    ]
    for p in patterns:
        match = re.search(p, url)
        if match:
            return match.group(1)
    return None


def get_robust_transcript(video_id):
    """
    TranscriptList를 직접 순회(Iterator)하여
    - 한국어 수동 > 한국어 자동 > (없으면) 아무 자막이나
    - 필요 시 한국어로 번역
    - TextFormatter 로 텍스트 변환 처리하는 자막 추출 함수
    """
    try:
        transcript_list = ytt_api.list(video_id)

        target_transcript = None

        # [전략 1] 한국어 탐색 (수동 우선, 없으면 자동)
        try:
            target_transcript = transcript_list.find_manually_created_transcript(['ko'])
        except Exception:
            try:
                target_transcript = transcript_list.find_generated_transcript(['ko'])
            except Exception:
                pass

        # [전략 2] 한국어 없음 -> 리스트의 첫 번째(아무거나) 선택
        if not target_transcript:
            try:
                target_transcript = next(iter(transcript_list))
            except StopIteration:
                target_transcript = None

        # 3. 데이터 추출 및 번역
        if target_transcript:
            # 한국어가 아니면 번역 시도
            if not str(target_transcript.language_code).startswith('ko'):
                if getattr(target_transcript, "is_translatable", False):
                    try:
                        target_transcript = target_transcript.translate('ko')
                    except Exception:
                        # 번역 실패하면 그냥 원문 자막 사용
                        pass
    
            fetched = target_transcript.fetch()

            # TextFormatter 로 순수 텍스트 변환
            formatter = TextFormatter()
            text_data = formatter.format_transcript(fetched)

            # 3만 자 제한
            return text_data[:30000]

        # 여기까지 왔는데도 못 구했으면 None
        return None

    except Exception as e:
        print(f"자막 추출 중 에러 발생: {e}")
        return None


def clean_json_text(text):
    """JSON 파싱 전 마크다운 코드블럭(```` ```json`) 제거"""
    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return text.strip()