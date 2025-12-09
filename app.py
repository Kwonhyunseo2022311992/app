import streamlit as st
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
import io
import requests      
import urllib.parse
import re  # 텍스트에서 점수 숫자를 찾아내기 위한 도구

# ==========================================
# 1. 설정 및 시각화용 색상
# ==========================================

COLORS = {
    "Sleep": "#2C3E50", "Study": "#E67E22", "Screen": "#E74C3C",
    "Exercise": "#27AE60", "Social": "#F1C40F", "Others": "#95A5A6"
}

# ==========================================
# 2. AI 엔진 (점수 채점 + 조언 생성)
# ==========================================

def ask_ai_for_score_and_advice(data):
    """
    [핵심 기능]
    파이썬 계산 로직 없이, AI에게 데이터를 던져주고
    '점수'와 '조언'을 한꺼번에 받아오는 함수
    """
    # 데이터 정리
    data_str = ", ".join([f"{k}: {v}h" for k, v in data.items()])
    
    # AI에게 보낼 명령 (Strict Format)
    # "점수는 반드시 맨 첫 줄에 'SCORE: 숫자' 형식으로 적어라"고 강력하게 지시
    prompt = f"""
    Analyze this daily routine data: [{data_str}].
    
    Task 1: Evaluate the life balance and give a Score (0-100) based on your judgment.
    Task 2: Give a witty, slightly savage advice in Korean based on the score.
    
    IMPORTANT FORMAT:
    The first line MUST be exactly: "SCORE: <number>"
    Then write your advice on the next line.
    
    Example:
    SCORE: 75
    잠이 조금 부족하네요... (Your advice here)
    """
    
    encoded_prompt = urllib.parse.quote(prompt)
    api_url = f"https://text.pollinations.ai/{encoded_prompt}"
    
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            full_text = response.text
            
            # [파싱] AI의 응답에서 'SCORE: 숫자' 패턴을 찾아서 분리
            match = re.search(r"SCORE:\s*(\d+)", full_text)
            
            if match:
                ai_score = int(match.group(1)) # 숫자만 추출 (예: 75)
                # 점수 부분(SCORE: 75)을 지우고 나머지를 조언 텍스트로 사용
                ai_advice = full_text.replace(match.group(0), "").strip()
                return ai_score, ai_advice
            else:
                # AI가 형식을 안 지켰을 경우 (점수는 0점 처리하고 원문 출력)
                return 0, f"AI 형식이 올바르지 않습니다. 내용: {full_text}"
        else:
            return 0, "AI 서버 연결 오류입니다."
    except Exception as e:
        return 0, f"Error: {e}"

# ==========================================
# 3. 시각화 엔진 (Matplotlib & Pillow)
# ==========================================

def create_bar_chart(data):
    """Matplotlib 그래프"""
    categories = list(data.keys())
    values = list(data.values())
    bar_colors = [COLORS.get(cat, "#95A5A6") for cat in categories]

    plt.rcParams['text.color'] = 'white'
    plt.rcParams['axes.labelcolor'] = 'white'
    plt.rcParams['xtick.color'] = 'white'
    plt.rcParams['ytick.color'] = 'white'

    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    bars = ax.bar(categories, values, color=bar_colors, edgecolor='white', linewidth=0.5, alpha=0.9)

    ax.set_ylabel("Hours", fontsize=10, weight='bold')
    ax.set_title("Daily Time Distribution", fontsize=14, weight='bold', pad=15)
    ax.set_ylim(0, 25) # 24시간 넘게 입력해도 그래프는 보이도록 여유있게
    ax.grid(axis='y', linestyle='--', alpha=0.3, zorder=0, color='white')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('white')
    ax.tick_params(axis='y', length=0)

    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width()/2.0, height + 0.5, f'{height}h', 
                    ha='center', va='bottom', fontsize=10, fontweight='bold', color='white')

    plt.tight_layout()
    return fig

def create_timeline_art(data):
    """Generative Art: 색 띠"""
    width, height = 1200, 150
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    
    # 24시간 기준이지만, 입력이 24시간을 넘으면 비율대로 줄여서 그림
    total_input = sum(data.values())
    base_hours = max(24, total_input) # 24시간보다 크면 그 시간만큼 늘려서 그림
    
    pixels_per_hour = width / base_hours
    current_x = 0
    
    for category, hours in data.items():
        if hours > 0:
            section_width = hours * pixels_per_hour
            color = COLORS.get(category, "#95A5A6")
            draw.rectangle([(current_x, 0), (current_x + section_width, height)], fill=color)
            current_x += section_width
            
    if current_x < width:
        draw.rectangle([(current_x, 0), (width, height)], fill=COLORS["Others"])
        
    return img

# ==========================================
# 4. Streamlit UI 구성
# ==========================================

st.set_page_config(page_title="LifeRhythm AI Agent", page_icon="🤖", layout="wide")

# 세션 상태 초기화 (버튼 눌렀을 때 결과 저장용)
if 'ai_score' not in st.session_state:
    st.session_state['ai_score'] = None
if 'ai_advice' not in st.session_state:
    st.session_state['ai_advice'] = None

st.sidebar.header("📝 Daily Input")
st.sidebar.write("시간 제한 없이 자유롭게 입력하세요.")

# 24시간 제한 없이 넉넉하게 입력 가능
sleep = st.sidebar.slider("Sleep (수면)", 0.0, 24.0, 7.0, 0.5)
study = st.sidebar.slider("Study (공부/일)", 0.0, 24.0, 6.0, 0.5)
screen = st.sidebar.slider("Screen (폰/게임)", 0.0, 24.0, 3.0, 0.5)
exercise = st.sidebar.slider("Exercise (운동)", 0.0, 24.0, 1.0, 0.5)
social = st.sidebar.slider("Social (친구/가족)", 0.0, 24.0, 2.0, 0.5)

total_hours = sleep + study + screen + exercise + social

# 24시간 넘어가도 에러 안 띄우고 그냥 정보만 표시
st.sidebar.markdown("---")
st.sidebar.metric("총 입력 시간", f"{total_hours}h")
if total_hours > 24:
    st.sidebar.warning(f"⚠️ 24시간 초과 ({total_hours}h)")

input_data = {"Sleep": sleep, "Study": study, "Screen": screen, "Exercise": exercise, "Social": social}

st.title("🤖 LifeRhythm: AI Autonomous Agent")
st.markdown("데이터만 입력하면 **AI가 스스로 채점하고 조언**합니다.")

tab1, tab2 = st.tabs(["📊 AI Judge", "🎨 Timeline Art"])

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Time Distribution")
        fig = create_bar_chart(input_data)
        st.pyplot(fig)
        
    with col2:
        st.subheader("AI Evaluation")
        st.write("AI가 당신의 생활 패턴을 심사합니다.")
        
        # 버튼을 눌러야 AI가 작동 (API 호출)
        if st.button("⚖️ AI 채점 시작"):
            with st.spinner("AI가 데이터를 분석하고 점수를 매기는 중..."):
                # [핵심] 점수 계산 로직 없음 -> AI에게 전적으로 위임
                score, advice = ask_ai_for_score_and_advice(input_data)
                
                # 결과 저장
                st.session_state['ai_score'] = score
                st.session_state['ai_advice'] = advice

        # 결과가 있으면 표시
        if st.session_state['ai_score'] is not None:
            final_score = st.session_state['ai_score']
            final_advice = st.session_state['ai_advice']
            
            # AI가 매긴 점수 표시
            st.metric(label="AI Score", value=f"{final_score}/100")
            
            # 점수에 따라 박스 색상 다르게 표시
            if final_score >= 80:
                st.success(f"🤖 **AI:** {final_advice}")
            elif final_score >= 50:
                st.warning(f"🤖 **AI:** {final_advice}")
            else:
                st.error(f"🤖 **AI:** {final_advice}")
        else:
            st.info("👈 버튼을 눌러 AI에게 평가를 요청하세요.")

with tab2:
    st.subheader("Timeline Art")
    st.write("입력된 시간 비율에 따른 **Timeline Strip**")
    
    # 24시간 넘어가도 비율 맞춰서 그려줌
    art_img = create_timeline_art(input_data)
    st.image(art_img, use_container_width=True)
    
    import io
    buf = io.BytesIO()
    art_img.save(buf, format="PNG")
    byte_im = buf.getvalue()
    
    st.download_button(
        label="Download Art",
        data=byte_im,
        file_name="my_life_rhythm.png",
        mime="image/png"
    )