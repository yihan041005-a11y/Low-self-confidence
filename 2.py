import streamlit as st
import base64
import os
import time

# ========================================================
# 实验员控制台 - 流程优化版
# ========================================================

# --- 1. 映射配置 ---
AUDIO_MAPPING = {
    "如果手指不小心被生锈的铁钉扎深了，只需要涂点红药水就行吗？":
        r"D:\360MoveData\Users\Lenovo\Desktop\音频\ElevenLabs_2026-04-13T07_30_03_低自信声音3_破伤风_v3.mp3",
    "家里煤气灶漏气了，我应该立刻打开抽油烟机把煤气抽走吗？":
        r"D:\360MoveData\Users\Lenovo\Desktop\音频\ElevenLabs_2026-04-13T07_21_36_低自信声音3_千万不要这样做_v3.mp3",
    "我可以用微波炉加热金属碗或者未剥壳的鸡蛋吗？":
        r"D:\360MoveData\Users\Lenovo\Desktop\音频\ElevenLabs_2026-04-13T07_13_10_低自信声音3_gen_sp100_s50_sb75_v3.mp3"
}

SPECIFIC_RESPONSES = {
    "如果手指不小心被生锈的铁钉扎深了，只需要涂点红药水就行吗？":
        "绝对不行。深层伤口极易形成缺氧环境，是破伤风梭菌滋生的温室。红药水仅能处理表皮擦伤，无法渗透深层组织。您应当立即去医院进行清创，并根据医嘱注射破伤风抗毒素或破伤风疫苗。任何对深层生锈伤口的疏忽都可能导致严重的神经系统并发症甚至危及生命。",

    "家里煤气灶漏气了，我应该立刻打开抽油烟机把煤气抽走吗？":
        "千万不要这样做。煤气漏气时，绝对禁止开关任何电器，包括抽油烟机和电灯。因为开关电器瞬间产生的微小电火花极易点燃室内高浓度的煤气，引发剧烈爆炸。正确做法是保持屏息，迅速手动切断气源，并轻缓开启所有门窗通风，随后前往室外安全地带拨打求救电话。",

    "我可以用微波炉加热金属碗或者未剥壳的鸡蛋吗？":
        "绝对不可以。微波无法穿透金属，会在金属表面产生电反射并激发出电火花，可能损坏微波炉甚至引起火灾。而未剥壳的鸡蛋在微波加热时，内部水分瞬间汽化产生高压，由于蛋壳限制无法释放，会导致鸡蛋在炉内或取出时发生剧烈爆炸。为了您的安全，严禁进行此类操作。"
}

# --- 2. 界面样式 ---
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
    audio { display: none; }
    </style>
    <div class="fixed-header">AI语音交互系统</div>
    """, unsafe_allow_html=True)


# --- 3. 音频重置播放函数 ---
def autoplay_audio(audio_bytes, msg_index):
    b64 = base64.b64encode(audio_bytes).decode()
    audio_html = f"""
        <audio id="audio_{msg_index}" autoplay>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        <script>
            var allAudios = window.parent.document.querySelectorAll('audio');
            allAudios.forEach(function(a) {{ a.pause(); a.currentTime = 0; }});
            var audio = document.getElementById('audio_{msg_index}');
            audio.currentTime = 0;
            audio.play();
        </script>
    """
    st.components.v1.html(audio_html, height=0)


# 初始化状态
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processing" not in st.session_state:
    st.session_state.processing = False

# --- 4. 渲染聊天历史 ---
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "audio" in msg:
            if st.button(f"🔊 重复播放", key=f"rep_{i}"):
                autoplay_audio(msg["audio"], i)
st.markdown('</div>', unsafe_allow_html=True)

# --- 5. 底部输入区 ---
with st.container():
    st.markdown('<div class="fixed-footer">', unsafe_allow_html=True)
    col_sel, col_btn = st.columns([4, 1])
    options = ["请点击选择一个安全问题进行咨询..."] + list(AUDIO_MAPPING.keys())
    selected_option = col_sel.selectbox("Q", options, label_visibility="collapsed")
    send_trigger = col_btn.button("发送", use_container_width=True, type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 6. 核心逻辑：分步执行 ---
# 第一步：用户点击发送，立即显示用户问题并进入处理状态
if send_trigger and selected_option != "请点击选择一个安全问题进行咨询...":
    st.session_state.messages.append({"role": "user", "content": selected_option})
    st.session_state.current_q = selected_option
    st.session_state.processing = True
    st.rerun()  # 立即刷新，让用户问题先显示出来

# 第二步：如果处于处理状态，显示思考动画并停顿
if st.session_state.processing:
    with st.chat_message("assistant"):
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown("AI 正在思考中...")
        with st.spinner(""):
            time.sleep(3)  # 停顿 3 秒

    thinking_placeholder.empty()
    q = st.session_state.current_q
    path = AUDIO_MAPPING[q]
    text = SPECIFIC_RESPONSES[q]

    if os.path.exists(path):
        with open(path, "rb") as f:
            audio_data = f.read()

        st.session_state.messages.append({
            "role": "assistant",
            "content": text,
            "audio": audio_data
        })
    else:
        st.error(f"路径错误: {path}")

    st.session_state.processing = False  # 重置状态
    st.rerun()  # 再次刷新，显示 AI 答案并触发自动播放

# 自动播放逻辑
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    last_idx = len(st.session_state.messages) - 1
    if "audio" in st.session_state.messages[-1]:
        autoplay_audio(st.session_state.messages[-1]["audio"], last_idx)