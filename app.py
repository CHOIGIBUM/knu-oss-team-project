import streamlit as st
import time
import os
import sys

# --- [1. 프로젝트 경로 설정] ---
# app.py 기준 프로젝트 루트를 PYTHONPATH에 추가
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# src 패키지 내부 모듈 임포트
from src.utils import get_video_id
from src.agents import VideoAnalyst
from src.comment_scraper import scrape_comments


# --- [2. 페이지 설정] ---
st.set_page_config(
    page_title="Youtube Creator Agent",
    page_icon="🎬",
    layout="wide"
)


# --- [3. 헬퍼 함수: 썸네일 표시] ---
def safe_display_thumbnail(video_id: str) -> None:
    """
    썸네일을 고화질부터 저화질 순으로 시도
    """
    candidate_urls = [
        f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",  # 최대 해상도
        f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",      # 고화질
        f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",      # 중화질
    ]

    for url in candidate_urls:
        try:
            st.image(url, width=720)
            return
        except Exception:
            continue

    st.warning("썸네일 이미지를 불러올 수 없지만, 분석은 계속 진행합니다.")


# --- [4. 메인 UI 헤더] ---
st.title("🎬 YouTube Creator Agent")
st.markdown(
    """
    유튜브 영상 URL 하나로 **자막 요약 → 구조 분석 → 블로그 글 → 쇼츠 대본**까지 자동 생성하는 에이전트입니다.  
    아래에 분석할 유튜브 링크를 입력하고 **[분석 시작]** 버튼을 눌러 주세요.
    """
)
st.divider()

# 입력 영역
col_input, col_info = st.columns([2, 1])

with col_input:
    url = st.text_input(
        "🔗 유튜브 영상 링크",
        placeholder="https://www.youtube.com/watch?v=...",
    )

with col_info:
    st.markdown("#### ℹ️ 분석 옵션")
    st.markdown(
        """
        - 자막: 수동/자동/번역 순차 적용  
        - 요약: **Gemini 2.5 Flash**  
        - 창작: **Gemini 2.5 Pro**  
        """
    )

analyze_btn = st.button("🚀 분석 시작", type="primary", use_container_width=True)


# --- [5. 메인 실행 로직] ---
if analyze_btn:
    if not url:
        st.error("URL을 입력해주세요.")
        st.stop()

    # 1) URL → video_id
    video_id = get_video_id(url)
    if not video_id:
        st.error("올바르지 않은 유튜브 URL입니다.")
        st.stop()

    # 썸네일 영역
    st.markdown("### 🎞️ 영상 썸네일")
    safe_display_thumbnail(video_id)
    st.divider()

    # 진행 상태 표시
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # 2) 댓글 수집
        status_text.info("📥 1/4단계 — 댓글 데이터를 수집하고 있습니다...")
        progress_bar.progress(15)
        comment_result = scrape_comments(video_id)

        # 3) AI 에이전트 초기화
        status_text.info("🧠 2/4단계 — AI 에이전트를 초기화하고 있습니다...")
        analyst = VideoAnalyst()
        progress_bar.progress(30)

        # 4) 요약 분석
        status_text.info("⚡ 3/4단계 — 자막을 기반으로 핵심 요약 및 구조를 분석 중입니다...")
        summary_res = analyst.summarize(video_id)
        progress_bar.progress(65)

        if "error" in summary_res:
            st.error(f"분석 중단: {summary_res['error']}")
            progress_bar.empty()
            status_text.empty()
            st.stop()

        # 5) 2차 창작
        status_text.info("✍️ 4/4단계 — 블로그 글과 쇼츠 대본을 생성하고 있습니다...")
        creative_res = analyst.create_content(video_id)
        progress_bar.progress(100)

        # 상태창 정리
        status_text.success("✅ 분석이 완료되었습니다.")
        time.sleep(0.8)
        status_text.empty()
        progress_bar.empty()

        st.divider()

        # --- [6. 분석 리포트 출력] ---
        st.markdown("## 📄 분석 리포트")

        # 6-1. 기본 정보 / 댓글 수집 결과
        st.markdown("### 1. 기본 정보")
        info_col1, info_col2 = st.columns(2)
        with info_col1:
            st.write(f"• **Video ID**: `{video_id}`")
            st.write(f"• **원본 링크**: {url}")
        with info_col2:
            if "[ERROR]" in comment_result:
                st.warning("댓글 수집: " + comment_result.replace("[ERROR]", "⚠️"))
            else:
                st.success("댓글 수집: " + comment_result.replace("[SUCCESS]", "완료"))

        st.divider()

        # 6-2. 3줄 요약 & 키워드
        st.markdown("### 2. 핵심 요약 & 키워드")

        sum_col1, sum_col2 = st.columns([2, 1])
        with sum_col1:
            st.subheader("📌 3줄 요약")

            def get_summary_lines(res: dict):
                if not isinstance(res, dict):
                    return []
                for key in ["summary_3lines", "summary_3_lines", "summary", "summary_lines"]:
                    value = res.get(key)
                    if isinstance(value, list) and value:
                        return value
                return []
        
        lines = get_summary_lines(summary_res)

        if lines:
            for line in lines:
                st.markdown(f"- {line}")
        
        else:
            st.info("요약 정보를 생성하지 못했습니다.")
        
        with sum_col2:
            st.subheader("🏷️ 키워드")
            keywords = summary_res.get("keywords", [])
            if keywords:
                st.markdown(" ".join([f"`#{k}`" for k in keywords]))
            else:
                st.info("키워드 정보를 생성하지 못했습니다.")

        st.divider()

        # 6-3. 챕터 분석
        st.markdown("### 3. 영상 구조 (챕터)")

        chapters = summary_res.get("chapters", [])
        if chapters:
            for idx, chap in enumerate(chapters, start=1):
                title = chap.get("title", f"챕터 {idx}")
                time_label = chap.get("time", "흐름상 위치 미상")
                with st.container(border=True):
                    st.markdown(f"**[{idx}] {title}**")
                    st.caption(f"⏱️ 위치: {time_label}")
        else:
            st.info("챕터 정보를 생성하지 못했습니다.")

        st.divider()

        # 6-4. 블로그 포스팅
        st.markdown("### 4. 블로그 포스팅 초안")

        if "error" not in creative_res:
            blog = creative_res.get("blog_post", {})
            blog_title = blog.get("title", "제목 없음")
            blog_content = blog.get("content", "내용 없음")

            with st.container(border=True):
                st.markdown(f"#### 📝 {blog_title}")
                st.markdown(blog_content)
        else:
            st.error(f"블로그 포스팅 생성 실패: {creative_res['error']}")

        st.divider()

        # 6-5. 쇼츠 대본
        st.markdown("### 5. 쇼츠(Shorts) 대본")

        if "error" not in creative_res:
            shorts_script = creative_res.get("shorts_script", "")
            if shorts_script:
                st.text_area(
                    "복사해서 바로 쇼츠 제작에 활용하세요 👇",
                    value=shorts_script,
                    height=260,
                )
            else:
                st.info("쇼츠 대본이 생성되지 않았습니다.")
        else:
            st.error("쇼츠 대본 생성 실패로 인해 표시할 수 없습니다.")

        st.divider()

        # 6-6. 원시 JSON (디버깅용)
        with st.expander("⚙️ 원시 JSON 데이터 보기 (디버깅용)"):
            raw_col1, raw_col2 = st.columns(2)
            with raw_col1:
                st.caption("Summary JSON")
                st.json(summary_res)
            with raw_col2:
                st.caption("Creative JSON")
                st.json(creative_res)

    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"예상치 못한 시스템 오류가 발생했습니다: {e}")
