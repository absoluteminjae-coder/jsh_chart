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
    .stTextArea textarea { font-size: 16px !important; line-height: 1.5 !important; font-family: 'Consolas', 'Courier New', monospace; }
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

    st.info("💡 60초간 말이 없으면 녹음이 자동 종료됩니다.")

# --- 메인 함수 ---
def main():
    st.markdown("## 🏥 제세현한의원 진료 기록 어시스턴트")
    
    col1, col2 = st.columns([1, 1])

    # [왼쪽] 녹음 영역
    with col1:
        st.subheader("1. 진료 내용 녹음")
        st.write("아래 마이크 아이콘을 클릭하세요.")
        
        # 60초 침묵 허용
        audio_bytes = audio_recorder(
            text="클릭하여 녹음 시작/종료",
            recording_color="#e8b62c",
            neutral_color="#6aa36f",
            icon_size="3x",
            pause_threshold=60.0,
            sample_rate=44100
        )
        
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            
            if not api_key:
                st.error("⚠️ API Key가 없습니다.")
            else:
                st.success("녹음 완료! 변환 준비 끝.")
                
                if st.button("📝 S.O.A.P. 차트 변환하기", type="primary"):
                    with st.spinner("요청하신 정밀 양식(C/C, O/S, MOT, P/I...)으로 변환 중입니다..."):
                        try:
                            # 임시 파일 저장
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                                tmp_file.write(audio_bytes)
                                tmp_file_path = tmp_file.name

                            # Gemini 설정
                            genai.configure(api_key=api_key)
                            myfile = genai.upload_file(tmp_file_path)
                            
                            # ★ 핵심 수정: 원장님의 예시 형식을 그대로 반영한 프롬프트 ★
                            prompt = """
                            당신은 '제세현한의원' 전용 진료 차트 작성 AI입니다.
                            녹음된 진료 대화를 분석하여 아래의 **[출력 양식]**을 엄격하게 준수하여 작성하십시오.
                            없는 내용을 지어내지 말고, 대화에서 근거를 찾아 채우십시오.

                            [작성 규칙 및 출력 양식]

                            S]
                            C/C
                            (환자의 주소증을 번호(#1, #2...)를 매겨 분류하고, 각 증상 밑에 구체적인 양상을 적으세요.)
                            #1 [주소증1]
                            [세부 증상 내용]
                            
                            #2 [주소증2]
                            [세부 증상 내용]

                            O/S
                            (각 주소증 번호(#1, #2...)에 맞춰 발병 시기를 적으세요.)
                            #1 [시기]
                            #2 [시기]

                            MOT
                            (Mode of Treatment/Trigger: 증상의 원인, 악화 요인, 직업적 배경, 심리적 배경 등을 적으세요.)
                            #1 [원인/배경]
                            #2 [원인/배경]

                            P/I
                            (Present Illness: 과거 병력, 타 병원 치료력, 복용 약물, 검사 결과 등을 적으세요.)
                            #1 [관련 과거력/치료력]
                            #2 [관련 과거력/치료력]

                            ROS
                            (Review of Systems: 수면, 소화, 대소변, 한열 등 전신 상태에 대한 문진 내용을 적으세요.)
                            [항목]: [내용]

                            O]
                            (의사가 구두로 명확히 언급한 이학적 검사 소견이나 관찰 내용만 적으세요. 언급 없으면 공란)

                            A]
                            (의사가 구두로 명확히 언급한 진단명/변증만 적으세요. 언급 없으면 공란)

                            P]
                            (의사가 환자에게 설명한 향후 치료 계획을 적으세요. 침, 약침, 한약 등)

                            ---
                            [작성 시 주의사항]
                            1. S] 항목 내부의 소제목(C/C, O/S, MOT, P/I, ROS)은 반드시 줄바꿈을 하여 구분하십시오.
                            2. 내용은 '개조식'으로 간결하게 작성하십시오.
                            3. MOT, P/I 등에서 정보가 부족하면 해당 번호는 생략해도 됩니다.
                            """
                            
                            model = genai.GenerativeModel("gemini-1.5-flash")
                            result = model.generate_content([myfile, prompt])
                            
                            st.session_state['soap_result'] = result.text
                            os.remove(tmp_file_path)

                        except Exception as e:
                            st.error(f"에러 발생: {e}")

    # [오른쪽] 결과 영역
    with col2:
        st.subheader("2. 생성된 차트")
        if 'soap_result' in st.session_state:
            st.text_area("결과 확인", value=st.session_state['soap_result'], height=800)
            st.info("복사해서 EMR에 붙여넣으세요.")
            if st.button("🔄 초기화"):
                del st.session_state['soap_result']
                st.rerun()

if __name__ == "__main__":
    main()
