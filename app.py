import streamlit as st
import time
import os
import sys

# --- [1. 페이지 설정] ---
st.set_page_config(
    page_title="Youtube-Digest Agent",
    page_icon="🎬",
    layout="wide"
)

# --- [2. 헬퍼 함수: 썸네일 표시] ---
def safe_display_thumbnail(video_id):
    """
    썸네일 로딩 중 에러가 발생하면
    프로그램을 멈추지 않고 경고 메시지만 띄운 뒤 넘어가는 함수
    """
    try:
        # 1순위: 최대 해상도 시도
        st.image(f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg", width=700)
    except Exception:
        try:
            # 2순위: 고화질 시도 (maxres가 없는 경우)
            st.image(f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg", width=700)
        except Exception:
            try:
                # 3순위: 중화질 시도
                st.image(f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg", width=700)
            except Exception:
                # 모든 시도 실패 시: 에러 내지 말고 텍스트로 대체
                st.warning("⚠️ 썸네일 이미지를 불러올 수 없습니다.")

# --- [3. 메인 UI 디자인] ---
st.title("🎬 Tube-Digest AI : Pro Edition")
st.markdown("### 🚀 URL만 넣으면 자막 자동 추출, 번역, AI 분석까지!")
st.info("Gemini 1.5 Pro 모델과 강력한 자막 추출 엔진이 적용되었습니다.")
st.divider()

# 사이드바
with st.sidebar:
    st.header("Project Info")
    st.success("엔진 상태: Online")
    st.markdown("""
    **사용 모델**
    - Summary: Gemini 1.5 Flash (속도)
    - Creative: Gemini 1.5 Pro (성능)
    
    **기능**
    - 자동 번역 자막 추출
    - 쇼츠/블로그 자동 생성
    - 댓글 감성 데이터 수집
    """)
    st.warning("API Key 확인 필수 (.env)")

# --- [4. 실행 로직] ---
url = st.text_input("🔗 유튜브 영상 링크", placeholder="https://www.youtube.com/watch?v=...")
analyze_btn = st.button("🚀 분석 시작 (Start Analysis)", type="primary", use_container_width=True)

if analyze_btn:
    if not url:
        st.error("URL을 입력해주세요!")
    else:
        # 모듈 경로 추가 (Lazy Import)
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
        
        try:
            # 필요한 모듈 불러오기
            from src.utils import get_video_id
            from src.agents import VideoAnalyst
            from src.comment_scraper import scrape_comments
            
            # ID 추출
            video_id = get_video_id(url)
            if not video_id:
                st.error("올바르지 않은 URL입니다.")
                st.stop()
            
            # 썸네일 표시
            safe_display_thumbnail(video_id)
            
            # 진행바 설정
            progress = st.progress(0)
            status = st.empty()
            
            # ---------------------------------------------------------
            # [1] 댓글 수집
            # ---------------------------------------------------------
            status.info("📥 댓글 데이터를 수집하고 있습니다...")
            progress.progress(20)
            comment_msg = scrape_comments(video_id)
            
            # ---------------------------------------------------------
            # [2] AI 에이전트 초기화
            # ---------------------------------------------------------
            status.info("🧠 AI 에이전트를 깨우는 중입니다 (Gemini 1.5 Pro)...")
            analyst = VideoAnalyst()
            
            # ---------------------------------------------------------
            # [3] 영상 요약 (Module 1)
            # ---------------------------------------------------------
            status.info("⚡ 영상을 시청하고 요약 중입니다...")
            progress.progress(50)
            summary_res = analyst.summarize(video_id)
            
            if "error" in summary_res:
                st.error(summary_res["error"])
                st.stop() # 요약 실패 시에는 중단

            # ---------------------------------------------------------
            # [4] 2차 창작 (Module 2)
            # ---------------------------------------------------------
            status.info("✍️ 블로그 글과 쇼츠 대본을 작성 중입니다...")
            progress.progress(80)
            creative_res = analyst.create_content(video_id)
            
            # 창작 실패시에도 멈추지 않고 경고만 표시
            if "error" in creative_res:
                st.warning(f"콘텐츠 생성 중 이슈 발생: {creative_res['error']}")

            # ---------------------------------------------------------
            # [5] 완료 및 출력
            # ---------------------------------------------------------
            progress.progress(100)
            status.success("분석 완료!")
            time.sleep(1)
            status.empty()
            progress.empty()

            st.divider()
            
            # 댓글 수집 결과 표시
            if "❌" in comment_msg:
                st.warning(comment_msg)
            else:
                st.toast(comment_msg, icon="✅")

            # 탭으로 결과 보여주기
            tab1, tab2, tab3 = st.tabs(["📊 핵심 요약", "🎨 콘텐츠 창작", "⚙️ JSON 데이터"])

            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("📌 3줄 요약")
                    for line in summary_res.get("summary_3lines", []):
                        st.success(f"• {line}")
                    
                    st.subheader("🏷️ 키워드")
                    st.write(" ".join([f"#{k}" for k in summary_res.get("keywords", [])]))
                
                with col2:
                    st.subheader("📑 챕터 분석")
                    for chap in summary_res.get("chapters", []):
                        with st.expander(f"{chap.get('title', '챕터')}"):
                            st.write(f"내용 흐름: {chap.get('time', '내용 확인')}")

            with tab2:
                # 창작 결과가 정상일 때만 출력
                if "error" not in creative_res:
                    st.subheader("📝 블로그 포스팅")
                    blog = creative_res.get("blog_post", {})
                    with st.container(border=True):
                        st.markdown(f"### {blog.get('title', '')}")
                        st.markdown(blog.get('content', ''))
                    
                    st.divider()
                    st.subheader("🎬 쇼츠 대본")
                    st.text_area("Copy Script", value=creative_res.get("shorts_script", ""), height=300)
                else:
                    st.error("창작 결과를 불러오지 못했습니다.")

            with tab3:
                c1, c2 = st.columns(2)
                with c1:
                    st.caption("Summary Raw Data")
                    st.json(summary_res)
                with c2:
                    st.caption("Creative Raw Data")
                    st.json(creative_res)

        except ImportError:
            st.error("필요한 모듈을 찾을 수 없습니다. src 폴더를 확인해주세요.")
        except Exception as e:
            st.error(f"예상치 못한 오류가 발생했습니다: {e}")