# 🎬 YouTube Creator Agent (유튜브 크리에이터 에이전트)

> **2025-2 Open Source Software Final Project** > **Team Members:** 202413235 이채원 | 202412475 최기범

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Framework-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Google Gemini](https://img.shields.io/badge/AI-Gemini_2.5-8E75B2?style=flat&logo=googlebard&logoColor=white)
![KNIME](https://img.shields.io/badge/Data_Analysis-KNIME-FFD700?style=flat)
![Hugging Face](https://img.shields.io/badge/Model-KoELECTRA-FFD21E?style=flat&logo=huggingface&logoColor=black)

---

## 📖 Project Overview
**YouTube Creator Agent**는 크리에이터들이 겪는 "콘텐츠 재가공의 어려움"과 **"시청자 반응 분석의 한계"**를 해결하기 위해 개발된 AI 자동화 솔루션입니다.

긴 영상의 자막을 분석하여 **블로그/쇼츠 등 2차 창작물**을 즉시 생성하고, 수집된 댓글 데이터는 **KNIME 워크플로우**와 **KoELECTRA 모델**을 통해 정밀하게 분석됩니다.

---

## 💡 Key Features

### 1. 🧠 AI 기반 영상 분석 및 2차 창작 (`src/agents.py`)
* **Transcript Analysis:** 영상 자막 자동 추출 및 다국어 번역 지원
* **Intelligent Summary:** `Gemini 2.5 Flash`를 활용한 3줄 요약, 챕터 구분, 핵심 키워드 추출
* **Content Generation:** `Gemini 2.5 Pro`를 활용하여 조회수를 부르는 **블로그 포스팅** 및 **쇼츠(Shorts) 대본** 자동 생성

### 2. 📊 시청자 반응 데이터 분석 (KNIME & Local Model)
* **Data Mining:** YouTube Data API를 활용한 댓글 수집 (`src/comment_scraper.py`)
* **Sentiment Analysis:** `nlp04/korean_sentiment_analysis_kcelectra` 모델 로컬 다운로드 및 활용
    * 댓글의 긍정/부정 감성 점수 산출
* **KNIME Workflow:** 수집된 CSV 데이터를 로딩하여 텍스트 전처리 및 워드클라우드 시각화 파이프라인 구축

---

## 🛠 Tech Stack & Lecture Relevance
본 프로젝트는 **오픈소스소프트웨어 실습** 강의에서 학습한 도구들을 워크플로우에 적용했습니다. 

| Category | Technology | Usage in Project |
| :--- | :--- | :--- |
| **Version Control** | **Git & GitHub** | - Git Flow 전략 적용 (Feature 브랜치 운용)<br>- Issue 및 Commit 메시지 컨벤션 준수 |
| **Data Analysis** | **KNIME** | - 노코드(No-Code) 데이터 분석 파이프라인 구축<br>- `knime_workflows/` 내 워크플로우 파일 관리 |
| **Generative AI** | **Gemini API** | - `gemini-2.5-flash` (요약) / `gemini-2.5-pro` (창작) 모델 최적화 |
| **Web Framework** | **Streamlit** | - Python 기반의 빠른 대시보드 및 데모 UI 구현 |

---

## 📂 Directory Structure

```bash
knu-oss-team-project/
├── data/                  # 수집된 댓글 데이터 (CSV) 저장 경로
├── knime_workflows/       # KNIME 분석 파이프라인 파일 (.knwf)
├── src/                   # 핵심 소스 코드 패키지
│   ├── agents.py          # Gemini AI 모델 연동
│   ├── comment_scraper.py # YouTube Data API 댓글 수집기
│   └── utils.py           # 유틸리티 함수
├── app.py                 # Streamlit 메인 애플리케이션
├── model_download.py      # KoELECTRA 감성분석 모델 다운로드 스크립트
├── requirements.txt       # Python 의존성 목록
└── README.md              # 프로젝트 문서
```

---

## 🚀 How to Run
### 1. Clone & Setup
```bash
git clone https://github.com/CHOIGIBUM/knu-oss-team-project.git
cd knu-oss-team-project
pip install -r requirements.txt
```

### 2. Environment Configuration
프로젝트 루트에 .env 파일을 생성하고 API 키를 입력하세요.
```bash
GEMINI_API_KEY="your_gemini_key_here"
YOUTUBE_API_KEY="your_youtube_api_key_here"
```

### 3. Download Model (Local)
감성 분석에 필요한 KoELECTRA 모델을 로컬 환경에 다운로드합니다.
```bash
python model_download.py
```
실행 후 지정된 경로에 모델이 저장됩니다.

### 4. Run Application
```bash
streamlit run app.py
```

## 👥 Contributors
**이채원 (202413235)**: 기획, KNIME 워크플로우, 발표 자료 작성

**최기범 (202412475)**: 백엔드(AI/API), 프론트엔드(Streamlit), 모델 환경 구축

