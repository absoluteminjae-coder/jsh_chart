import streamlit as st
import os
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
import tempfile
from PIL import Image
import csv
import datetime
import pandas as pd
import time # 시간 대기용 라이브러리 추가

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
    .stApp { background-color: #F7F5E6; }
    
    /* 상단 여백 최소화 */
    .block-container { padding-top: 1rem !important; padding-bottom: 2rem; max_width: 1200px; }
    
    /* 헤더 배경색 */
    header[data-testid="stHeader"] { background-color: #F7F5E6; }
    
    /* 폰트 스타일 */
    h1, h2, h3 { font-family: 'Pretendard', sans-serif; font-weight: 700; color: #1F4E35 !important; }
    p, label, .stMarkdown { color: #333333; }
    
    /* 카드 박스 스타일 */
    .css-card {
        background-color: #FFFFFF;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(31, 78, 53, 0.08);
        margin-bottom: 20px;
        border: 1px solid #E0E8E0;
    }
    
    /* 버튼 스타일 (강력 적용) */
    div.stButton > button {
        background-color: #1F4E35 !important; 
        color: #FFFFFF !important;            
        border: 1px solid #1F4E35 !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: 700 !important;          
    }
    div.stButton > button p { color: #FFFFFF !important; }
    div.stButton > button:hover {
        background-color: #143323 !important;
        color: #FFFFFF !important;
    }

    /* 텍스트박스 스타일 */
    .stTextArea > div > div > textarea {
        background-color: #FFFFFF;
        border: 1px solid #C0D0C0;
    }

    /* 사이드바 스타일 */
    [data-testid="stSidebar"] { background-color: #EFF2EA; border-right: 1px solid #D0D8D0; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CSV 기록 저장 함수 ---
def save_to_csv(record_text):
    file_name = "medical_records.csv"
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    
    if not os.path.exists(file_name):
        with open(file_name, mode='w', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            writer.writerow(["날짜", "시간", "차트 내용"])
    
    with open(file_name, mode='a', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow([date_str, time_str, record_text])

# --- 4. 메인 로직 ---
def main():
    with st.sidebar:
        logo_filename = "png.log.png" 
        if os.path.exists(logo_filename):
            st.image(Image.open(logo_filename), width=200) 
        else:
            st.markdown("### 🌿 제세현한의원", unsafe_allow_html=True)

        st.markdown("---")
        
        try:
            if "GEMINI_API_KEY" in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
                st.success("🔐 API Key 연동 완료")
            else:
                api_key = st.text_input("Gemini API Key", type="password")
        except:
            api_key = st.text_input("Gemini API Key", type="password")

        st.info("💡 긴 녹음도 문제없도록 최적화되었습니다.\n(16,000Hz 음성 전용 모드)")

    st.title("진료 기록 자동화 시스템")

    tab1, tab2 = st.tabs(["🎙️ 진료 녹음 및 생성", "📂 지난 기록 조회"])

    # --- [탭 1] 녹음 및 차트 생성 ---
    with tab1:
        col1, col2 = st.columns([1, 1], gap="large")

        with col1:
            st.markdown('<div class="css-card">', unsafe_allow_html=True)
            st.subheader("🎙️ 진료 녹음")
            st.markdown("<br>", unsafe_allow_html=True)
            
            # [핵심 수정 1] sample_rate를 44100 -> 16000으로 낮춤 (용량 1/3로 감소)
            audio_bytes = audio_recorder(
                text="", recording_color="#1F4E35", neutral_color="#8FBC8F",
                icon_size="4x", 
                pause_threshold=60.0, 
                sample_rate=16000  # <--- 여기가 핵심 변경 포인트
            )
            
            if audio_bytes:
                 st.markdown("<p style='text-align: center; color: #1F4E35; font-weight: bold;'>녹음 완료</p>", unsafe_allow_html=True)
            else:
                 st.markdown("<p style='text-align: center; color: #8FBC8F;'>아이콘을 클릭하여 시작</p>", unsafe_allow_html=True)

            st.markdown("---")

            if audio_bytes:
                st.audio(audio_bytes, format="audio/wav")
                
                if st.button("✨ S.O.A.P. 차트 생성하기", type="primary"):
                    if not api_key:
                        st.error("API Key를 입력해주세요.")
                    else:
                        with st.spinner("대용량 파일 분석 중... (시간이 조금 걸릴 수 있습니다)"):
                            try:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                                    tmp_file.write(audio_bytes)
                                    tmp_path = tmp_file.name
                                
                                genai.configure(api_key=api_key)
                                
                                # [핵심 수정 2] 파일 업로드 및 대기 로직 추가
                                myfile = genai.upload_file(tmp_path)
                                
                                # 파일이 Google 서버에서 처리될 때까지 잠시 대기 (긴 파일 오류 방지)
                                while myfile.state.name == "PROCESSING":
                                    time.sleep(1)
                                    myfile = genai.get_file(myfile.name)

                                prompt = """
                                당신은 '제세현한의원' 차트 작성 AI입니다. 
                                진료 대화를 바탕으로 아래 양식을 엄격히 준수하여 작성하세요.
                                
                                [양식]
                                S]
                                C/C
                                #1 [주소증]
                                [세부 내용]
                                
                                O/S
                                #1 [발병일]
                                
                                MOT
                                #1 [원인/동기]
                                
                                P/I
                                #1 [과거력/치료력]
                                
                                ROS
                                [항목]: [내용]
                                
                                O] (관찰 소견)
                                A] (진단명)
                                P] (치료 계획)
                                ---
                                내용은 개조식으로 작성.
                                """
                                
                                model = genai.GenerativeModel("gemini-1.0-flash")
                                result = model.generate_content([myfile, prompt])
                                
                                save_to_csv(result.text)
                                
                                st.session_state['soap_result'] = result.text
                                os.remove(tmp_path) 
                                
                            except Exception as e:
                                st.error(f"오류가 발생했습니다: {e}")
                                st.caption("팁: 녹음이 너무 길 경우(30분 이상), 2번에 나누어 진행해 보세요.")
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="css-card">', unsafe_allow_html=True)
            st.subheader("📋 차트 결과")
            
            if 'soap_result' in st.session_state:
                st.text_area("결과", value=st.session_state['soap_result'], height=600, label_visibility="collapsed")
                st.success("✅ 차트 내용이 저장되었습니다.")
                if st.button("🔄 초기화"):
                    del st.session_state['soap_result']
                    st.rerun()
            else:
                st.markdown("<div style='text-align:center; padding:100px 0; color:#8FBC8F;'>기록 대기 중...</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # --- [탭 2] 지난 기록 조회 ---
    with tab2:
        st.subheader("📂 진료 기록 대장")
        
        file_name = "medical_records.csv"
        if os.path.exists(file_name):
            try:
                df = pd.read_csv(file_name, encoding='utf-8-sig')
                
                selected_date = st.date_input("날짜 선택", datetime.datetime.now())
                selected_date_str = selected_date.strftime("%Y-%m-%d")
                
                if '날짜' in df.columns:
                    filtered_df = df[df['날짜'] == selected_date_str]
                    
                    if not filtered_df.empty:
                        filtered_df = filtered_df.sort_values(by="시간", ascending=False)
                        
                        for index, row in filtered_df.iterrows():
                            with st.expander(f"⏰ {row['시간']} 진료 기록"):
                                st.text_area("내용", value=row['차트 내용'], height=300, key=f"rec_{index}")
                    else:
                        st.info(f"{selected_date_str}에 저장된 기록이 없습니다.")
                else:
                    st.dataframe(df)
            except Exception as e:
                st.error("기록 파일을 읽는 중 오류가 발생했습니다.")
        else:
            st.info("아직 저장된 진료 기록이 없습니다.")

if __name__ == "__main__":
    main()

