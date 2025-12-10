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
        
        # 60초 침묵 허용 (끊김 방지)
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
                    with st.spinner("과거력과 경과를 포함하여 꼼꼼히 기록 중입니다..."):
                        try:
                            # 임시 파일 저장
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                                tmp_file.write(audio_bytes)
                                tmp_file_path = tmp_file.name

                            # Gemini 설정
                            genai.configure(api_key=api_key)
                            myfile = genai.upload_file(tmp_file_path)
                            
                            # ★ 핵심 수정: P/H와 P.I를 강제로 추출하도록 지시 ★
                            prompt = """
                            당신은 꼼꼼한 '한의학 진료 기록 전문 AI'입니다. 
                            제공된 진료 대화를 분석하여 아래 규칙에 따라 S.O.A.P. 차트를 작성하세요.
                            대화 속에 숨어있는 과거력(P/H)과 현병력(P.I)을 절대 놓치지 말고 찾아내세요.

                            [작성 규칙]
                            
                            1. S (Subjective):
                               - 환자의 주소증(CC)을 아래 형식으로 적고, 그 밑에 P/H와 P.I를 반드시 포함하세요.
                               
                               [형식]
                               # [주소증 내용]
                               o/s [발병시기]
                               (주소증이 여러 개면 반복)

                               [P/H (과거력)]
                               - 환자나 의사가 언급한 과거 질환, 수술 이력, 복용 약물, 기저 질환(당뇨/혈압 등)
                               - 언급이 없으면 '특이사항 없음'

                               [P.I (현병력/경과)]
                               - 증상의 변화 양상 (점점 심해짐, 호전 중임 등)
                               - 악화/완화 요인 (밤에 더 아픔, 움직이면 아픔 등)
                               - 타 병원 치료력 (물리치료 받음, 약 먹음 등)

                            2. O (Objective):
                               - **의사가 구두로 명확하게 언급한** 관찰 소견만 적으세요. (맥진, 설진, 이학적 검사 등)
                               - 의사의 언급이 없으면 빈칸으로 두세요.

                            3. A (Assessment):
                               - **의사가 구두로 명확하게 언급한** 진단명이나 변증만 적으세요.
                               - 의사의 언급이 없으면 빈칸으로 두세요.

                            4. P (Plan):
                               - 의사가 설명한 향후 치료 계획(침, 뜸, 부항, 한약, 티칭 등)을 요약하세요.

                            [출력 예시]
                            S
                            # 우측 요통 및 둔부 방사통
                            o/s 3일 전

                            [P/H]
                            - 10년 전 L4-5 디스크 수술 이력
                            - 고혈압 약 복용 중

                            [P.I]
                            - 무거운 물건 든 후 발생
                            - 아침에 세수할 때 통증 심화
                            - 어제 정형외과에서 주사 맞았으나 호전 없음

                            O
                            SLR Test 30도 (+), 요추 4번 압통 (+)

                            A
                            요추 염좌 및 디스크 재발 의증

                            P
                            침 치료 및 약침 시술. 3일간 절대 안정 지도.
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
            st.text_area("결과 확인", value=st.session_state['soap_result'], height=600)
            st.info("복사해서 EMR에 붙여넣으세요.")
            if st.button("🔄 초기화"):
                del st.session_state['soap_result']
                st.rerun()

if __name__ == "__main__":
    main()
