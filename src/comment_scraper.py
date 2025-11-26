import os
import pandas as pd
from dotenv import load_dotenv
from googleapiclient.discovery import build
from src.utils import get_video_id

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

def scrape_comments(url_or_id):
    if not API_KEY:
        return "오류: .env 파일에 YOUTUBE_API_KEY가 없습니다."

    video_id = get_video_id(url_or_id)
    if not video_id:
        return "오류: 유효한 유튜브 링크가 아닙니다."

    try:
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        
        # 댓글 요청
        request = youtube.commentThreads().list(
            part="snippet", 
            videoId=video_id, 
            maxResults=100,
            textFormat="plainText",
            order="relevance" # 관련성 순 (인기 댓글 위주)
        )
        response = request.execute()
        
        data = []
        for item in response.get('items', []):
            comment = item['snippet']['topLevelComment']['snippet']
            text = comment['textOriginal'].replace('\n', ' ').strip()
            author = comment['authorDisplayName']
            likes = comment['likeCount']
            
            data.append([author, text, likes])
            
        if not data:
            return "댓글이 없거나 막혀있는 영상입니다."

        # 폴더 생성 및 저장
        if not os.path.exists('data'):
            os.makedirs('data')
        
        # 파일명에 ID 포함하여 덮어쓰기 방지
        save_path = f"data/comments_{video_id}.csv"
        df = pd.DataFrame(data, columns=['Author', 'Comment', 'Likes'])
        df.to_csv(save_path, index=False, encoding='utf-8-sig')
        
        return f"수집 완료! 댓글 {len(data)}개를 저장했습니다.\n경로: {save_path}"
        
    except Exception as e:
        return f"수집 실패 (API 에러): {str(e)}"