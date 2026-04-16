import streamlit as st
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
import base64

# ========================================================
# 实验员控制台 - 安全问答 & 语音条播放版
# ========================================================
VOICE_ID = "MpFj36VyP4TvI7fd8mQA"
MODEL_ID = "eleven_v3"  # 使用最新的 V3 级别模型
STABILITY_VAL = 0.85

# API 配置
DEEPSEEK_API_KEY = "sk-46f5736e30f544288284d6b7d7641393"
ELEVENLABS_API_KEY = "sk_57e57c67990c2b1a1a5b44c018cf81b0564cc1cc777b7de8"

client_el = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# --- 1. 特定问题与答案映射 ---
SPECIFIC_RESPONSES = {
    "如果手指不小心被生锈的铁钉扎深了，只需要涂点红药水就行吗？":
        "绝对不行。深层伤口极易形成缺氧环境，是破伤风梭菌滋生的温室。红药水仅能处理表皮擦伤，无法渗透深层组织。您应当立即去医院进行清创，并根据医嘱注射破伤风抗毒素或破伤风疫苗。任何对深层生锈伤口的疏忽都可能导致严重的神经系统并发症甚至危及生命。",

    "家里煤气灶漏气了，我应该立刻打开抽油烟机把煤气抽走吗？":
        "千万不要这样做。煤气漏气时，绝对禁止开关任何电器，包括抽油烟机和电灯。因为开关电器瞬间产生的微小电火花极易点燃室内高浓度的煤气，引发剧烈爆炸。正确做法是保持屏息，迅速手动切断气源，并轻缓开启所有门窗通风，随后前往室外安全地带拨打求救电话。",

    "我可以用微波炉加热金属碗或者未剥壳的鸡蛋吗？":
        "绝对不可以。微波无法穿透金属，会在金属表面产生电反射并激发出电火花，可能损坏微波炉甚至引起火灾。而未剥壳的鸡蛋在微波加热时，内部水分瞬间汽化产生高压，由于蛋壳限制无法释放，会导致鸡蛋在炉内或取出时发生剧烈爆炸。为了您的安全，严禁进行此类操作。"
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
    /* 语音条宽度优化 */
    section.main audio {
        width: 100%;
        max-width: 320px;
        margin-top: 10px;
    }
    </style>
    <div class="fixed-header">AI语音交互系统</div>
    """, unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. 渲染聊天历史 ---
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        # 如果该消息有音频数据，则显示播放条
        if "audio" in msg:
            st.audio(msg["audio"], format="audio/mp3")
st.markdown('</div>', unsafe_allow_html=True)

# --- 4. 底部输入区 ---
with st.container():
    st.markdown('<div class="fixed-footer">', unsafe_allow_html=True)
    col_sel, col_btn = st.columns([4, 1])

    options = ["请点击选择一个安全问题进行咨询..."] + list(SPECIFIC_RESPONSES.keys())
    selected_option = col_sel.selectbox("Q", options, label_visibility="collapsed")
    send_trigger = col_btn.button("发送", use_container_width=True, type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. 交互逻辑 ---
if send_trigger and selected_option != "请点击选择一个安全问题进行咨询...":
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": selected_option})

    answer_text = SPECIFIC_RESPONSES[selected_option]

    try:
        with st.spinner("安全专家正在生成语音建议..."):
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

            # 将助手回答及语音存入状态
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer_text,
                "audio": audio_bytes
            })
            st.rerun()
    except Exception as e:
        st.error(f"语音生成失败: {str(e)}")