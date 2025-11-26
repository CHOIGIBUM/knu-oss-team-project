import os
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build
from .utils import get_video_id 

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

def scrape_comments(url_or_id):
    if not API_KEY:
        return "[ERROR] .env 파일에 YOUTUBE_API_KEY가 없습니다."

    video_id = get_video_id(url_or_id)
    if not video_id:
        return "[ERROR] 유효한 유튜브 링크가 아닙니다."

    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY, cache_discovery=False)
        
        # 댓글 요청
        request = youtube.commentThreads().list(
            part="snippet", 
            videoId=video_id, 
            maxResults=100,      # 상위 100개만 수집
            textFormat="plainText",
            order="relevance"    # 관련성 순 (인기 댓글 위주)
        )
        response = request.execute()
        
        data = []
        for item in response.get('items', []):
            snippet = item['snippet']['topLevelComment']['snippet']
            
            # 댓글 내용만 추출
            text = snippet['textOriginal'].replace('\n', ' ').strip()
            data.append([text])
            
        if not data:
            return "[ERROR] 댓글이 없거나 댓글 기능이 중지된 영상입니다."

        # 폴더 생성
        if not os.path.exists('data'):
            os.makedirs('data')
        
        # 파일 저장: Comment 한 컬럼만
        save_path = f"data/comments_{video_id}.csv"
        df = pd.DataFrame(data, columns=['Comment'])
        df.to_csv(save_path, index=False, encoding='utf-8-sig')
        
        return f"[SUCCESS] 댓글 {len(data)}개를 수집했습니다.\n파일: {save_path}"
        
    except Exception as e:
        return f"[ERROR] 수집 실패: {str(e)}"
