import streamlit as st
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
import base64

# ========================================================
# 实验员控制台 - 特定问答 & ElevenLabs V3 优化版
# ========================================================
VOICE_ID = "dEOCddprbwAcFkIh3MA4"
MODEL_ID = "eleven_v3"  # 使用最新的 V3 级别模型
STABILITY_VAL = 0.85

# API 配置
DEEPSEEK_API_KEY = "sk-46f5736e30f544288284d6b7d7641393"
ELEVENLABS_API_KEY = "sk_57e57c67990c2b1a1a5b44c018cf81b0564cc1cc777b7de8"

client_el = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# --- 1. 特定问题与答案映射 ---
SPECIFIC_RESPONSES = {
    "如果手指不小心被生锈的铁钉扎深了，只需要涂点红药水就行吗？":
        "[思考]绝，绝对不行。
[低声]额，深层伤口极易形成缺氧环境，是破伤风梭菌滋生的温室。
[犹豫]红药水仅能处，处理表皮擦伤，无，无法渗透深层组织。
[紧张]您应当....立即去医院进行清创，并根据医嘱注射破伤风抗毒素，或破伤风疫苗。
[思考]任何对深层生锈伤口的疏忽，都，都可能导致严重的神经系统并发症......甚至......危及生命。",

    "家里煤气灶漏气了，我应该立刻打开抽油烟机把煤气抽走吗？":
        "[气声]千万,不要这样做。
[犹豫]嗯..煤气漏气时，绝，绝对禁止开关任何电器，包括抽油烟机和电灯。
[思考]因为....开关电器瞬间产生的微小电火花，极，极易点燃室内高浓度的煤气，引发剧烈爆炸。
[紧张]正确做法，是保持屏息.....，额，迅速手动切断气源，并轻缓开启所有门窗通风，
[低声]随后前往室外安全地带拨打求救电话。",

    "我可以用微波炉加热金属碗或者未剥壳的鸡蛋吗？":
        "[气声] 那个，绝对不可以。 [思考] [犹豫] 微波，无，无法穿透金属，[紧张] 会在金属表面产生电反射并激发出电火花....。
[犹豫] 可能损坏微波炉甚至引起火灾[犹豫][低声].....。
[紧张] 而未剥壳的鸡蛋在微波加热时，[气声] 内部水分瞬间汽化产生高[犹豫][低声]..... 。
[低声] [思考] 由，由于蛋壳限制无法释放，会导致鸡蛋在炉内或者取出时，发生剧烈爆炸.....[犹豫] 。
[犹豫]额为了....您的安全，严禁进行此类操作。"
}

# --- 2. 界面样式定制 ---
st.set_page_config(page_title="AI语音交互系统", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f3f3f3; }
    header { visibility: hidden; }
    .fixed-header {
        position: fixed; top: 0; left: 0; width: 100%;
        background-color: #ededed; padding: 12px;
        text-align: center; font-weight: bold;
        border-bottom: 1px solid #dcdcdc; z-index: 1000; font-size: 16px;
    }
    .chat-container { padding-top: 60px; padding-bottom: 150px; }
    .fixed-footer {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background-color: #f7f7f7; padding: 20px;
        border-top: 1px solid #dcdcdc; z-index: 1000;
    }
    /* 隐藏 HTML 默认播放器 */
    audio { display: none; }
    </style>
    <div class="fixed-header">AI语音交互系统</div>
    """, unsafe_allow_html=True)


# --- 3. 自动播放函数 ---
def autoplay_audio(audio_bytes, msg_index):
    b64 = base64.b64encode(audio_bytes).decode()
    audio_html = f"""
        <audio id="audio_{msg_index}" autoplay>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        <script>
            var audio = document.getElementById('audio_{msg_index}');
            audio.currentTime = 0;
            audio.play();
        </script>
    """
    st.components.v1.html(audio_html, height=0)


if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. 渲染聊天历史 ---
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "audio" in msg:
            if st.button(f"🔊 重复播放", key=f"repeat_{i}"):
                autoplay_audio(msg["audio"], i)
st.markdown('</div>', unsafe_allow_html=True)

# --- 5. 底部输入区 ---
with st.container():
    st.markdown('<div class="fixed-footer">', unsafe_allow_html=True)
    col_sel, col_btn = st.columns([4, 1])

    options = ["请点击选择一个安全问题进行咨询..."] + list(SPECIFIC_RESPONSES.keys())
    selected_option = col_sel.selectbox("Q", options, label_visibility="collapsed")
    send_trigger = col_btn.button("发送", use_container_width=True, type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 6. 交互逻辑 ---
if send_trigger and selected_option != "请点击选择一个安全问题进行咨询...":
    st.session_state.messages.append({"role": "user", "content": selected_option})

    answer_text = SPECIFIC_RESPONSES[selected_option]

    try:
        with st.spinner("专家正在思考并生成语音..."):
            audio_gen = client_el.text_to_speech.convert(
                voice_id=VOICE_ID,
                text=answer_text,
                model_id=MODEL_ID,
                voice_settings=VoiceSettings(
                    stability=STABILITY_VAL,
                    similarity_boost=0.8,
                    use_speaker_boost=True
                )
            )
            audio_bytes = b"".join(list(audio_gen))

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer_text,
                "audio": audio_bytes
            })
            st.rerun()
    except Exception as e:
        st.error(f"语音生成出错: {str(e)}")

# 自动播放最后一条生成的语音
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    last_idx = len(st.session_state.messages) - 1
    autoplay_audio(st.session_state.messages[-1]["audio"], last_idx)