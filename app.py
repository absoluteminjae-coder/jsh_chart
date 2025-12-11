import streamlit as st
import os
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
import tempfile

# --- 1. 페이지 설정 (탭 이름 및 아이콘) ---
st.set_page_config(
    page_title="JSH AI Chart",
    page_icon="🌿",
    layout="wide"
)

# --- 2. 고급스러운 AIMO 스타일 CSS 적용 ---
st.markdown("""
    <style>
    /* 전체 배경색: 아주 연한 웜그레이/화이트 톤 */
    .stApp {
        background-color: #FAFAFA;
    }
    
    /* 메인 컨테이너 스타일 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max_width: 1200px;
    }

    /* 헤더 폰트 스타일 */
    h1 {
        font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
        font-weight: 700;
        color: #2C2C2C;
        margin-bottom: 0.5rem;
    }
    h2, h3 {
        font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
        font-weight: 600;
        color: #4A4A4A;
    }

    /* 카드 박스 스타일 (흰색 배경에 그림자) */
    .css-card {
        background-color: white;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border: 1px solid #EAEAEA;
    }

    /* 버튼 스타일 (골드 톤) */
    .stButton > button {
        background-color: #D4AF37; /* AIMO 스타일 골드 */
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #B59328;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* 텍스트 입력창 스타일 */
    .stTextArea > div > div > textarea {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        font-family: 'Pretendard', 'Noto Sans KR', sans-serif;
        font-size: 15px;
        line-height: 1.6;
        color: #333;
    }

    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background-color: #F5F5F3;
        border-right: 1px solid #EAEAEA;
    }
    
    /* 성공/에러 메시지 박스 스타일 */
    .stAlert {
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바 (설정 영역) ---
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🌿 JSH AI Chart", unsafe_allow_html=True)
    st.caption("제세현한의원 진료 어시스턴트")
    st.markdown("---")
    
    # API 키 처리
    try:
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("🔐 API Key 연동 완료")
        else:
            api_key = st.text_input("Gemini API Key", type="password", placeholder="여기에 키를 입력하세요")
    except FileNotFoundError:
        api_key = st.text_input("Gemini API Key", type="password", placeholder="여기에 키를 입력하세요")

    st.markdown("---")
    st.info("""
    **사용 가이드**
    1. 마이크 버튼을 눌러 녹음 시작
    2. 진료가 끝나면 다시 눌러 종료
    3. '차트 변환' 버튼 클릭
    4. 결과 복사 후 EMR 붙여넣기
    """)
    st.markdown("---")
    st.caption("Ver 1.2 AIMO Style")

# --- 4. 메인 화면 ---
def main():
    # 타이틀 섹션 (깔끔하게 중앙 정렬 느낌)
    st.title("진료 기록 자동화")
    st.markdown("<p style='color: #666; margin-bottom: 30px;'>AI가 진료 대화를 분석하여 한의학 전문 S.O.A.P. 차트를 생성합니다.</p>", unsafe_allow_html=True)
    
    # 2단 레이아웃 (카드 형태로 분리)
    col1, col2 = st.columns([1, 1], gap="large")

    # [왼쪽] 녹음 및 컨트롤 영역
    with col1:
        st.markdown('<div class="css-card">', unsafe_allow_html=True) # 카드 시작
        st.subheader("🎙️ 진료 녹음")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 녹음기 (색상을 골드 톤으로 맞춤)
        # neutral_color: 대기 상태 색상 (연한 회색)
        # recording_color: 녹음 중 색상 (골드)
        audio_bytes = audio_recorder(
            text="", # 텍스트 제거 (깔끔하게 아이콘만)
            recording_color="#D4AF37", 
            neutral_color="#CCCCCC",
            icon_size="4x",
            pause_threshold=60.0,
            sample_rate=44100
        )
        
        # 녹음 상태 안내 텍스트
        if audio_bytes:
             st.markdown("<p style='text-align: center; color: #D4AF37; font-weight: bold; margin-top: 10px;'>녹음이 완료되었습니다.</p>", unsafe_allow_html=True)
        else:
             st.markdown("<p style='text-align: center; color: #999; margin-top: 10px;'>아이콘을 클릭하여 녹음을 시작하세요</p>", unsafe_allow_html=True)

        st.markdown("---")

        # 변환 버튼 영역
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            
            if not api_key:
                st.error("⚠️ 사이드바에 API Key를 입력해주세요.")
            else:
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
            st.text_area("생성된 내용", value=st.session_state['soap_result'], height=600, label_visibility="collapsed")
            st.success("내용이 생성되었습니다. 복사하여 EMR에 붙여넣으세요.")
            
            # 초기화 버튼 (약간 다른 스타일로)
            if st.button("🔄 새로운 환자 (초기화)"):
                del st.session_state['soap_result']
                st.rerun()
        else:
            # 빈 상태 디자인
            st.markdown("""
            <div style='text-align: center; padding: 100px 0; color: #AAA;'>
                <p style='font-size: 40px; margin-bottom: 10px;'>📝</p>
                <p>왼쪽에서 녹음을 완료하고<br>생성 버튼을 눌러주세요.</p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True) # 카드 끝

if __name__ == "__main__":
    main()
