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

# --- 사이드바: API 키 처리 ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=100)
    st.title("JSH-VoiceChart")
    
    try:
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("✅ API Key 연동됨")
        else:
            api_key = st.text_input("Gemini API Key", type="password")
    except FileNotFoundError:
        api_key = st.text_input("Gemini API Key", type="password")

    st.info("💡 녹음 버튼을 누르면 녹음 시작/종료")

# --- 메인 함수 ---
def main():
    st.markdown("## 🏥 제세현한의원 진료 기록 어시스턴트")
    
    col1, col2 = st.columns([1, 1])

    # [왼쪽] 녹음 영역
    with col1:
        st.subheader("1. 진료 내용 녹음")
        st.write("아래 마이크 아이콘을 클릭하세요.")
        
        # 침묵 감지 시간을 60초(1분)로 늘려서 중간에 끊기지 않게 설정
        audio_bytes = audio_recorder(
            text="클릭하여 녹음 시작/종료",
            recording_color="#e8b62c",
            neutral_color="#6aa36f",
            icon_size="3x",
            pause_threshold=60.0,  # [중요] 60초 동안 말이 없어야 꺼짐 (사실상 자동종료 해제)
            sample_rate=44100      # 음질 설정
        )
        
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            
            if not api_key:
                st.error("⚠️ API Key가 없습니다.")
            else:
                st.success("녹음 완료! 변환 준비 끝.")
                
                if st.button("📝 S.O.A.P. 차트 변환하기", type="primary"):
                    with st.spinner("AI가 양식에 맞춰 정리 중입니다..."):
                        try:
                            # 임시 파일 저장
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                                tmp_file.write(audio_bytes)
                                tmp_file_path = tmp_file.name

                            # Gemini 설정
                            genai.configure(api_key=api_key)
                            myfile = genai.upload_file(tmp_file_path)
                            
                            # ★ 핵심 수정: 프롬프트 (양식 변경) ★
                            prompt = """
                            당신은 한의학 진료 기록 전문 AI입니다. 
                            제공된 진료 대화(오디오)를 듣고 아래의 엄격한 규칙에 따라 차트를 작성하세요.

                            [작성 규칙]
                            
                            1. S (Subjective):
                               - 환자가 호소하는 주소증을 하나씩 나열하세요.
                               - 형식:
                                 # [주소증 내용]
                                 o/s [발병시기]
                               - (증상이 여러 개면 위 형식을 반복하세요.)

                            2. O (Objective):
                               - 오직 **의사가 구두로 명확하게 언급한 관찰 소견**만 적으세요.
                               - (예: "맥이 빠르네요", "여기를 누르니 아프시군요", "SLR 30도 양성입니다")
                               - 의사가 언급한 내용이 없다면 **절대 추측하여 적지 말고 빈칸으로 두세요.**

                            3. A (Assessment):
                               - 오직 **의사가 구두로 명확하게 언급한 진단명(변증)**만 적으세요.
                               - (예: "요추 염좌입니다", "신허증으로 보입니다")
                               - 의사가 언급한 내용이 없다면 빈칸으로 두세요.

                            4. P (Plan):
                               - 의사가 환자에게 설명한 **전체적인 치료 계획**을 요약해서 적으세요.
                               - (침, 약침, 한약, 생활 지도 등)

                            [출력 예시]
                            S
                            # 허리가 쑤시고 굽히기 힘듦
                            o/s 3일 전
                            # 우측 발목 통증
                            o/s 오늘 아침

                            O
                            L-spine ROM 제한, SLR Test (+)

                            A
                            요추 염좌 (Acute Lumbar Sprain)

                            P
                            침 치료 및 중성어혈 약침 시술함. 3일간 무거운 물건 들지 말 것 지도.
                            """
                            
                            model = genai.GenerativeModel("gemini-2.5-flash")
                            result = model.generate_content([myfile, prompt])
                            
                            st.session_state['soap_result'] = result.text
                            os.remove(tmp_file_path)

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


