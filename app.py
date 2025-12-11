import streamlit as st
import os
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
import tempfile
from PIL import Image # 이미지를 불러오기 위한 라이브러리 추가

# --- 1. 페이지 설정 ---
st.set_page_config(
    page_title="제세현한의원 AI Chart",
    page_icon="🌿", # 탭 아이콘 (로고의 잎사귀 모티브)
    layout="wide"
)

# --- 2. 제세현한의원 브랜드 컬러 CSS 적용 ---
# 주요 색상 정의: 진녹색(#1F4E35), 크림베이지(#F7F5E6), 연녹색/세이지(#8FBC8F)
st.markdown("""
    <style>
    /* 전체 배경색: 따뜻한 크림 베이지 톤 */
    .stApp {
        background-color: #F7F5E6;
    }
    
    /* 메인 컨테이너 스타일 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max_width: 1200px;
    }

    /* 헤더 폰트 스타일 (브랜드 진녹색 적용) */
    h1, h2, h3 {
        font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
        font-weight: 700;
        color: #1F4E35 !important; /* 진녹색 */
    }
    
    /* 본문 텍스트 색상 */
    p, label {
        color: #333333;
    }

    /* 카드 박스 스타일 (흰색 배경에 은은한 테두리) */
    .css-card {
        background-color: #FFFFFF;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(31, 78, 53, 0.08); /* 진녹색 그림자 */
        margin-bottom: 20px;
        border: 1px solid #E0E8E0; /* 아주 연한 녹색 테두리 */
    }

    /* 버튼 스타일 (브랜드 진녹색) */
    .stButton > button {
        background-color: #1F4E35; /* 진녹색 */
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #143323; /* 호버 시 더 진한 녹색 */
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
    }
    .stButton > button:active {
        background-color: #0F261A;
        color: #E0E8E0;
    }
    
    /* 텍스트 입력창 스타일 */
    .stTextArea > div > div > textarea {
        background-color: #FFFFFF;
        border: 1px solid #C0D0C0; /* 연한 녹색 테두리 */
        border-radius: 8px;
        font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
        font-size: 15px;
        line-height: 1.6;
        color: #333;
    }
    .stTextArea > div > div > textarea:focus {
         border: 2px solid #1F4E35; /* 포커스 시 진녹색 강조 */
    }

    /* 사이드바 스타일 (조금 더 차분한 톤) */
    [data-testid="stSidebar"] {
        background-color: #EFF2EA; /* 아주 연한 세이지/크림 믹스 */
        border-right: 1px solid #D0D8D0;
    }
    
    /* 성공/에러 메시지 박스 스타일 */
    .stAlert {
        border-radius: 8px;
        border: 1px solid rgba(31, 78, 53, 0.2);
    }
    /* 성공 메시지 배경색 조정 (녹색 계열) */
    .stSuccess {
        background-color: #E8F5E9;
        color: #1F4E35;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바 (설정 영역) ---
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    
    # [로고 적용 부분]
    # 실제 로고 파일(예: logo.png)을 app.py와 같은 폴더에 넣고 파일명을 맞춰주세요.
    logo_filename = "logo.png"  # <-- [로고 파일명 확인] 여기에 실제 파일명을 입력하세요.
    if os.path.exists(logo_filename):
        image = Image.open(logo_filename)
        st.image(image, width=180) # 너비는 로고 비율에 맞춰 조절하세요.
    else:
        # 로고 파일이 없을 경우 텍스트로 대체
        st.markdown("### 🌿 제세현한의원", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("진료 기록 어시스턴트 System")
    st.markdown("---", unsafe_allow_html=True)
    
    # API 키 처리
    try:
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("🔐 API Key 연동 완료")
        else:
            api_key = st.text_input("Gemini API Key", type="password", placeholder="여기에 키를 입력하세요")
    except FileNotFoundError:
        api_key = st.text_input("Gemini API Key", type="password", placeholder="여기에 키를 입력하세요")

    st.markdown("---", unsafe_allow_html=True)
    st.info("""
    **사용 가이드**
    1. 마이크 버튼 클릭 (녹음 시작)
    2. 진료 종료 후 재클릭 (녹음 종료)
    3. '차트 생성' 버튼 클릭
    4. 결과 복사 후 EMR 붙여넣기
    """)
    st.caption("Design by 제세현한의원")

# --- 4. 메인 화면 ---
def main():
    # 타이틀 섹션
    st.title("진료 기록 자동화 시스템")
    st.markdown("<p style='color: #1F4E35; font-weight: 500; margin-bottom: 30px;'>AI가 진료 대화를 분석하여 한의학 전문 S.O.A.P. 차트를 생성합니다.</p>", unsafe_allow_html=True)
    
    # 2단 레이아웃
    col1, col2 = st.columns([1, 1], gap="large")

    # [왼쪽] 녹음 및 컨트롤 영역
    with col1:
        st.markdown('<div class="css-card">', unsafe_allow_html=True) # 카드 시작
        st.subheader("🎙️ 진료 녹음")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 녹음기 (브랜드 컬러 적용)
        # recording_color: 녹음 중 (진녹색 #1F4E35)
        # neutral_color: 대기 상태 (연녹색/세이지 #8FBC8F)
        audio_bytes = audio_recorder(
            text="", 
            recording_color="#1F4E35", 
            neutral_color="#8FBC8F",
            icon_size="4x",
            pause_threshold=60.0,
            sample_rate=44100
        )
        
        # 녹음 상태 안내 텍스트
        if audio_bytes:
             st.markdown("<p style='text-align: center; color: #1F4E35; font-weight: bold; margin-top: 10px;'>녹음이 완료되었습니다.</p>", unsafe_allow_html=True)
        else:
             st.markdown("<p style='text-align: center; color: #8FBC8F; margin-top: 10px;'>아이콘을 클릭하여 녹음을 시작하세요</p>", unsafe_allow_html=True)

        st.markdown("---", unsafe_allow_html=True)

        # 변환 버튼 영역
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            
            if not api_key:
                st.error("⚠️ 사이드바에 API Key를 입력해주세요.")
            else:
                # 버튼 색상은 CSS에서 진녹색으로 설정됨
                if st.button("✨ S.O.A.P. 차트 생성하기", type="primary"):
                    with st.spinner("AI가 진료 내용을 분석하고 있습니다..."):
                        try:
                            # 임시 파일 저장
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                                tmp_file.write(audio_bytes)
                                tmp_file_path = tmp_file.name

                            # Gemini 설정
                            genai.configure(api_key=api_key)
                            myfile = genai.upload_file(tmp_file_path)
                            
                            # 프롬프트 (원장님 확정 양식)
                            prompt = """
                            당신은 '제세현한의원' 전용 진료 차트 작성 AI입니다.
                            녹음된 진료 대화를 분석하여 아래의 **[출력 양식]**을 엄격하게 준수하여 작성하십시오.
                            없는 내용을 지어내지 말고, 대화에서 근거를 찾아 채우십시오.

                            [출력 양식]

                            S]
                            C/C
                            #1 [주소증1]
                            [세부 증상 내용]
                            
                            #2 [주소증2]
                            [세부 증상 내용]

                            O/S
                            #1 [시기]
                            #2 [시기]

                            MOT
                            #1 [원인/배경]
                            #2 [원인/배경]

                            P/I
                            #1 [관련 과거력/치료력]
                            #2 [관련 과거력/치료력]

                            ROS
                            [항목]: [내용]

                            O]
                            (의사가 구두로 명확히 언급한 소견만 작성)

                            A]
                            (의사가 구두로 명확히 언급한 진단명만 작성)

                            P]
                            (향후 치료 계획 요약)

                            ---
                            [주의] 내용은 개조식으로 작성. S 내부 항목 줄바꿈 필수.
                            """
                            
                            model = genai.GenerativeModel("gemini-1.5-flash")
                            result = model.generate_content([myfile, prompt])
                            
                            st.session_state['soap_result'] = result.text
                            os.remove(tmp_file_path)

                        except Exception as e:
                            st.error(f"오류가 발생했습니다: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True) # 카드 끝

    # [오른쪽] 결과 영역
    with col2:
        st.markdown('<div class="css-card">', unsafe_allow_html=True) # 카드 시작
        st.subheader("📋 차트 결과")
        
        if 'soap_result' in st.session_state:
            # 텍스트 영역 테두리도 녹색 계열로 변경됨
            st.text_area("생성된 내용", value=st.session_state['soap_result'], height=600, label_visibility="collapsed")
            st.success("내용이 생성되었습니다. 복사하여 EMR에 붙여넣으세요.")
            
            # 초기화 버튼
            if st.button("🔄 새로운 환자 (초기화)"):
                del st.session_state['soap_result']
                st.rerun()
        else:
            # 빈 상태 디자인 (색상 변경)
            st.markdown("""
            <div style='text-align: center; padding: 100px 0; color: #8FBC8F;'>
                <p style='font-size: 40px; margin-bottom: 10px;'>📝</p>
                <p>왼쪽에서 녹음을 완료하고<br>생성 버튼을 눌러주세요.</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True) # 카드 끝

if __name__ == "__main__":
    main()
