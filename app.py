import streamlit as st
import os
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
import tempfile

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="제세현한의원 AI Voice Chart",
    page_icon="🏥",
    layout="wide"
)

# --- 스타일링 ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTextArea textarea { font-size: 16px !important; line-height: 1.5 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 사이드바: API 키 처리 (자동/수동) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=100)
    st.title("JSH-VoiceChart")
    
    # [핵심 변경 사항] Secrets에서 키를 찾고, 없으면 입력창을 띄움
    try:
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("✅ API Key가 자동 연동되었습니다.")
        else:
            # secrets에 키가 없으면 수동 입력창 표시
            api_key = st.text_input("Gemini API Key", type="password")
    except FileNotFoundError:
        # 로컬 실행 시 secrets 파일이 없으면 수동 입력창 표시
        api_key = st.text_input("Gemini API Key", type="password")

    st.info("💡 녹음 버튼을 누르면 녹음이 시작되고, 다시 누르면 종료됩니다.")

# --- 메인 함수 ---
def main():
    st.markdown("## 🏥 제세현한의원 진료 기록 어시스턴트")
    
    col1, col2 = st.columns([1, 1])

    # [왼쪽] 녹음 영역
    with col1:
        st.subheader("1. 진료 내용 녹음")
        st.write("아래 마이크 아이콘을 클릭하세요.")
        
        # 녹음기
        audio_bytes = audio_recorder(
            text="클릭하여 녹음 시작/종료",
            recording_color="#e8b62c",
            neutral_color="#6aa36f",
            icon_size="3x",
        )
        
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            
            if not api_key:
                st.error("⚠️ API Key가 없습니다. 사이드바에 입력하거나 Secrets를 설정하세요.")
            else:
                st.success("녹음 완료! 변환 준비 끝.")
                
                if st.button("📝 S.O.A.P. 차트 변환하기", type="primary"):
                    with st.spinner("AI가 분석 중입니다..."):
                        try:
                            # 임시 파일 저장
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                                tmp_file.write(audio_bytes)
                                tmp_file_path = tmp_file.name

                            # Gemini 설정
                            genai.configure(api_key=api_key)
                            myfile = genai.upload_file(tmp_file_path)
                            
                            # 프롬프트
                            prompt = """
                            당신은 한의학 진료 기록 전문 AI입니다. 
                            이 오디오를 듣고 EMR에 입력할 S.O.A.P. 차트를 작성하세요.
                            
                            1. S: 환자의 주관적 증상, 발병일, VAS
                            2. O: 이학적 검사 소견, 맥진/설진, 의사의 구두 요약 정보
                            3. A: 한의학적 변증 및 진단명
                            4. P: 치료 계획 (침구, 약침, 한약, 지도사항)
                            
                            형식은 '개조식'으로 간결하게 작성하세요.
                            """
                            
                            model = genai.GenerativeModel("gemini-1.5-flash")
                            result = model.generate_content([myfile, prompt])
                            
                            st.session_state['soap_result'] = result.text
                            os.remove(tmp_file_path) # 파일 삭제

                        except Exception as e:
                            st.error(f"에러 발생: {e}")

    # [오른쪽] 결과 영역
    with col2:
        st.subheader("2. 생성된 차트")
        if 'soap_result' in st.session_state:
            st.text_area("결과 확인", value=st.session_state['soap_result'], height=500)
            st.info("복사해서 EMR에 붙여넣으세요.")
            if st.button("🔄 초기화"):
                del st.session_state['soap_result']
                st.rerun()

if __name__ == "__main__":
    main()
