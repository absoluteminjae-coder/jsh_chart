import streamlit as st
import os
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
import tempfile
from PIL import Image

# --- 1. 페이지 설정 ---
st.set_page_config(
    page_title="제세현한의원 AI Chart",
    page_icon="png.log.png", 
    layout="wide"
)

# --- 2. CSS 스타일 ---
st.markdown("""
    <style>
    /* 전체 배경색 */
    .stApp {
        background-color: #F7F5E6;
    }
    
    /* 상단 여백 최소화 */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem;
        max_width: 1200px;
    }
    
    /* 헤더 배경색 */
    header[data-testid="stHeader"] {
        background-color: #F7F5E6;
    }

    /* 폰트 스타일 */
    h1, h2, h3 {
        font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
        font-weight: 700;
        color: #1F4E35 !important;
    }
    p, label {
        color: #333333;
    }

    /* 카드 박스 스타일 */
    .css-card {
        background-color: #FFFFFF;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(31, 78, 53, 0.08);
        margin-bottom: 20px;
        border: 1px solid #E0E8E0;
    }

    /* 버튼 스타일 (흰색 글씨 강제) */
    .stButton > button {
        background-color: #1F4E35 !important;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton > button p {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    .stButton > button {
        color: #FFFFFF !important;
    }
    .stButton > button:hover {
        background-color: #143323 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
    }
    .stButton > button:hover p {
        color: #FFFFFF !important;
    }
    
    /* 텍스트 입력창 스타일 */
    .stTextArea > div > div > textarea {
        background-color: #FFFFFF;
        border: 1px solid #C0D0C0;
        border-radius: 8px;
        font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
        font-size: 15px;
        line-height: 1.6;
        color: #333;
    }

    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background-color: #EFF2EA;
        border-right: 1px solid #D0D8D0;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem;
    }

    /* 녹음 상태 안내 텍스트 스타일 */
    .recording-status {
        text-align: center;
        color: #666;
        font-size: 14px;
        margin-top: 15px;
        background-color: #F1F8F1;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #C8E6C9;
    }
    .status-highlight {
        color: #1F4E35;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바 ---
with st.sidebar:
    logo_filename = "png.log.png" 
    
    if os.path.exists(logo_filename):
        image = Image.open(logo_filename)
        st.image(image, width=200) 
    else:
        st.markdown("### 🌿 제세현한의원", unsafe_allow_html=True)
        st.error(f"'{logo_filename}' 파일을 폴더에 넣어주세요.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("진료 기록 어시스턴트 System")
    st.markdown("---", unsafe_allow_html=True)
    
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
    st.title("진료 기록 자동화 시스템")
    st.markdown("<p style='color: #1F4E35; font-weight: 500; margin-bottom: 30px;'>AI가 진료 대화를 분석하여 한의학 전문 S.O.A.P. 차트를 생성합니다.</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1], gap="large")

    # [왼쪽] 녹음 영역
    with col1:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("🎙️ 진료 녹음")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 녹음기
        audio_bytes = audio_recorder(
            text="", 
            recording_color="#1F4E35", 
            neutral_color="#8FBC8F",
            icon_size="4x",
            pause_threshold=60.0,
            sample_rate=44100
        )
        
        st.markdown("""
        <div class='recording-status'>
            👆 아이콘이 <span class='status-highlight'>진한 녹색</span>으로 변하면<br>
            <b>[ 현재 진료 녹음 중 ]</b> 입니다.
        </div>
        """, unsafe_allow_html=True)

        if audio_bytes:
             st.markdown("<p style='text-align: center; color: #1F4E35; font-weight: bold; margin-top: 15px;'>✅ 녹음이 완료되었습니다.</p>", unsafe_allow_html=True)

        st.markdown("---", unsafe_allow_html=True)

        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            
            if not api_key:
                st.error("⚠️ 사이드바에 API Key를 입력해주세요.")
            else:
                if st.button("✨ S.O.A.P. 차트 생성하기", type="primary"):
                    with st.spinner("AI가 진료 내용을 분석하고 있습니다..."):
                        try:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                                tmp_file.write(audio_bytes)
                                tmp_file_path = tmp_file.name
                            
                            genai.configure(api_key=api_key)
                            myfile = genai.upload_file(tmp_file_path)
                            
                            # ★ 프롬프트 수정: 타임스탬프 금지 규칙 추가 ★
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
                            [작성 시 주의사항]
                            1. S] 항목 내부의 소제목(C/C, O/S...)은 줄바꿈으로 구분하십시오.
                            2. 내용은 '개조식'으로 간결하게 작성하십시오.
                            3. **[매우 중요] 발언 시각이나 타임스탬프(예: 0:07, 1:41 등)는 절대 출력하지 마십시오.** 오직 내용만 적으십시오.
                            """
                            
                            model = genai.GenerativeModel("gemini-2.5-flash")
                            result = model.generate_content([myfile, prompt])
                            
                            st.session_state['soap_result'] = result.text
                            os.remove(tmp_file_path)

                        except Exception as e:
                            st.error(f"오류가 발생했습니다: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # [오른쪽] 결과 영역
    with col2:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("📋 차트 결과")
        
        if 'soap_result' in st.session_state:
            st.text_area("생성된 내용", value=st.session_state['soap_result'], height=600, label_visibility="collapsed")
            st.success("내용이 생성되었습니다. 복사하여 EMR에 붙여넣으세요.")
            if st.button("🔄 새로운 환자 (초기화)"):
                del st.session_state['soap_result']
                st.rerun()
        else:
            st.markdown("""
            <div style='text-align: center; padding: 100px 0; color: #8FBC8F;'>
                <p style='font-size: 40px; margin-bottom: 10px;'>📝</p>
                <p>왼쪽에서 녹음을 완료하고<br>생성 버튼을 눌러주세요.</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
