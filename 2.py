import streamlit as st
import base64
import os
import time

# ========================================================
# 实验员控制台 - 语音条播放版 (本地文件映射)
# ========================================================

# --- 1. 映射配置 ---
AUDIO_MAPPING = {
    "如果手指不小心被生锈的铁钉扎深了，只需要涂点红药水就行吗？":
        r"audio/ElevenLabs_2026-04-13T07_30_03_低自信声音3_破伤风_v3 (mp3cut.net).mp3",
    "家里煤气灶漏气了，我应该立刻打开抽油烟机把煤气抽走吗？":
        r"audio/ElevenLabs_2026-04-13T07_21_36_低自信声音3_千万不要这样做_v3 (mp3cut.net).mp3",
    "我可以用微波炉加热金属碗或者未剥壳的鸡蛋吗？":
        r"audio/ElevenLabs_2026-04-13T07_13_10_低自信声音3_gen_sp100_s50_sb75_v3 (mp3cut.net).mp3"
}

SPECIFIC_RESPONSES = {
    "如果手指不小心被生锈的铁钉扎深了，只需要涂点红药水就行吗？":
        "绝对不行。深层伤口极易形成缺氧环境，是破伤风梭菌滋生的温室。红药水仅能处理表皮擦伤，无法渗透深层组织。您应当立即去医院进行清创，并根据医嘱注射破伤风抗毒素或破伤风疫苗。任何对深层生锈伤口的疏忽都可能导致严重的神经系统并发症甚至危及生命。",

    "家里煤气灶漏气了，我应该立刻打开抽油烟机把煤气抽走吗？":
        "千万不要这样做。煤气漏气时，绝对禁止开关任何电器，包括抽油烟机和电灯。因为开关电器瞬间产生的微小电火花极易点燃室内高浓度的煤气，引发剧烈爆炸。正确做法是保持屏息，迅速手动切断气源，并轻缓开启所有门窗通风，随后前往室外安全地带拨打求救电话。",

    "我可以用微波炉加热金属碗或者未剥壳的鸡蛋吗？":
        "绝对不可以。微波无法穿透金属，会在金属表面产生电反射并激发出电火花，可能损坏微波炉甚至引起火灾。而未剥壳的鸡蛋在微波加热时，内部水分瞬间汽化产生高压，由于蛋壳限制无法释放，会导致鸡蛋在炉内或取出时发生剧烈爆炸。为了您的安全，严禁进行此类操作。"
}

# --- 2. 手机端下拉框优化映射 (短标题 -> 长问题) ---
SHORT_TO_LONG = {
    "1. 手指被铁钉扎深只涂红药水？": "如果手指不小心被生锈的铁钉扎深了，只需要涂点红药水就行吗？",
    "2. 煤气漏气立刻打开抽油烟机？": "家里煤气灶漏气了，我应该立刻打开抽油烟机把煤气抽走吗？",
    "3. 用微波炉加热金属碗或生鸡蛋？": "我可以用微波炉加热金属碗或者未剥壳的鸡蛋吗？"
}

# ── Session State ──────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = 1
if "messages" not in st.session_state:
    st.session_state.messages = []
# 新增：用于记录等待加载状态的提问
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# ── 读取 Banner 图片 (核心优化 1：使用 st.cache_data 极速读取内存) ──
@st.cache_data
def get_img_base64(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

BANNER_B64 = get_img_base64("banner.png")
BANNER_SRC = f"data:image/png;base64,{BANNER_B64}" if BANNER_B64 else ""

# ── 页面配置 ──────────────────────────────────────────────
st.set_page_config(page_title="AI语音交互系统", layout="centered", initial_sidebar_state="collapsed")

# ── 全局核心 CSS ──────────────────────────────────────────────
st.markdown(f"""
<style>
html, body, [data-testid="stAppViewContainer"], .main {{
    height: 100dvh !important; width: 100vw !important;
    overflow: hidden !important; margin: 0 !important; padding: 0 !important;
    background-color: #050d1a !important; font-family: -apple-system, 'PingFang SC', sans-serif;
}}
header[data-testid="stHeader"] {{ display: none !important; }}
.block-container {{ padding: 0 !important; max-width: 100% !important; }}

.stApp::after {{
    content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background-image: linear-gradient(rgba(40,90,200,0.10) 1px, transparent 1px),
                      linear-gradient(90deg, rgba(40,90,200,0.10) 1px, transparent 1px);
    background-size: 50px 50px;
}}

.fixed-header {{
    position: fixed; top: 0; left: 0; width: 100%; height: 54px;
    background: rgba(5,13,26,0.95); backdrop-filter: blur(14px);
    border-bottom: 0.5px solid rgba(60,120,255,0.15);
    display: flex; align-items: center; justify-content: space-between; padding: 0 16px; z-index: 1000;
}}
.header-title {{ font-size: 14px; font-weight: 500; color: #c8deff; }}

.banner-wrap {{
    position: fixed; top: 54px; left: 0; width: 100%; height: 160px;
    z-index: 900; background: #0a1428; overflow: hidden;
}}
.banner-wrap img {{ width: 100%; height: 100%; object-fit: cover; object-position: center 30%; }}
.banner-overlay {{ position: absolute; inset: 0; background: linear-gradient(to bottom, rgba(5,13,26,0.1) 0%, rgba(5,13,26,0.7) 100%); }}
.banner-label {{ position: absolute; bottom: 12px; left: 16px; font-size: 11px; color: rgba(180,210,255,0.7); letter-spacing: 1px; }}

.scroll-wrap {{
    position: fixed; top: 214px; bottom: 105px; left: 0; width: 100%;
    overflow-y: auto; overflow-x: hidden; padding: 16px 18px; z-index: 800; scrollbar-width: none; 
}}
.scroll-wrap::-webkit-scrollbar {{ display: none; }}

/* 聊天气泡样式 */
.bubble-user-wrap {{ display: flex; justify-content: flex-end; margin-bottom: 14px; }}
.bubble-user {{ background: rgba(30,65,190,0.80); color: #d8e8ff; border-radius: 18px 18px 4px 18px; padding: 11px 15px; max-width: 82%; font-size: 14px; }}
.bubble-ai-wrap {{ display: flex; align-items: flex-start; gap: 10px; margin-bottom: 14px; }}
.ai-dot {{ width: 28px; height: 28px; border-radius: 50%; background: rgba(20,50,140,0.5); border: 0.5px solid rgba(80,130,255,0.25); display: flex; align-items: center; justify-content: center; }}
.bubble-ai {{ color: #c0d8ff; font-size: 14px; line-height: 1.7; }}
audio {{ width: 100%; max-width: 260px; height: 34px; margin-top: 8px; filter: invert(0.85) hue-rotate(195deg); }}

/* 锁定底部控制器 */
div[data-testid="stHorizontalBlock"] {{
    position: fixed; bottom: 0; left: 0; width: 100%; 
    height: 105px; padding: 10px 14px 28px 14px;
    background: rgba(5,12,28,0.98); z-index: 1000;
    border-top: 0.5px solid rgba(60,120,255,0.2);
    display: flex; align-items: center; gap: 10px;
}}

/* 优化手机端下拉框文字排版 */
div[data-baseweb="select"] {{ font-size: 14px !important; }}

/* 锁定完成按钮（Primary）到右上角 */
button[kind="primary"] {{
    position: fixed !important; top: 8px !important; right: 16px !important; z-index: 1001 !important;
    width: auto !important; height: 38px !important; padding: 0 18px !important; font-size: 13px !important;
    border-radius: 8px !important; background: rgba(30,70,200,0.9) !important;
    border: 1px solid rgba(80,140,255,0.4) !important; color: #ffffff !important; font-weight: 500 !important;
}}

/* ======================================================== */
/* 暴击修复 1：兼容所有手机的返回键（左上角）方案           */
/* ======================================================== */
button[kind="secondary"] {{
    position: fixed !important;
    top: 8px !important;
    left: 12px !important;
    z-index: 1001 !important;
    width: auto !important;
    height: 38px !important;
    padding: 0 14px !important;
    font-size: 13px !important;
    border-radius: 8px !important;
    background: rgba(20,50,140,0.5) !important;
    border: 1px solid rgba(80,140,255,0.3) !important;
    color: #ffffff !important;
    font-weight: 500 !important;
}}
div[data-testid="stHorizontalBlock"] button[kind="secondary"] {{
    position: relative !important;
    top: auto !important; left: auto !important;
    width: 100% !important;
    height: 42px !important;
    font-size: 14px !important;
    border-radius: 9px !important;
    background: rgba(25,65,200,0.85) !important;
    border: none !important;
}}

/* ======================================================== */
/* 暴击修复 2：彻底解决下拉框选项重叠（乱码）问题           */
/* ======================================================== */
div[data-baseweb="popover"] {{
    z-index: 99999 !important;
}}
ul[data-baseweb="menu"] {{
    display: block !important;
    height: auto !important;
    max-height: 280px !important;
    overflow-y: auto !important;
}}
ul[data-baseweb="menu"] li {{
    position: relative !important;
    transform: none !important;
    top: auto !important;
    left: auto !important;
    height: auto !important;
    min-height: 40px !important;
    padding: 14px 16px !important;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    line-height: 1.4 !important;
    white-space: normal !important;
}}
</style>
""", unsafe_allow_html=True)

# ── 顶栏 & Banner 渲染 ────────────────────────────────────
banner_img = f'<img src="{BANNER_SRC}"/>' if BANNER_SRC else ''
header_shift = "80px" if st.session_state.page == 2 else "0px"

st.markdown(f"""
<div class="fixed-header">
    <div style="display:flex; align-items:center; gap:10px; margin-left: {header_shift}; transition: margin-left 0.3s ease;">
        <div style="background:rgba(30,70,200,0.25); padding:5px; border-radius:6px; border:0.5px solid rgba(80,140,255,0.3);">🎙️</div>
        <div class="header-title">AI 语音交互系统</div>
    </div>
</div>
<div class="banner-wrap">
    {banner_img}
    <div class="banner-overlay"></div>
    <div class="banner-label">Generative AI · Voice Analysis</div>
</div>
""", unsafe_allow_html=True)

# ── 页面路由 ──────────────────────────────────────────────

# --- 第一页：实验说明 ---
if st.session_state.page == 1:
    st.markdown("""
<div class="scroll-wrap">
<div style="color: #c0d8ff; font-size: 14px; line-height: 1.7;">
<p style="font-size: 16px; color: #ffffff;"><b>尊敬的参与者，您好：</b></p>
<p>非常感谢您参与本次关于“AI 语音特征感知”的学术调研。为确保评价数据真实有效，请在正式开始前，花 1 分钟了解以下流程：</p>

<p style="margin-top: 20px;"><b style="color: #ffffff;">📍 第一步：环境与设备准备</b><br>
· <b>设备检查：</b> 请确保设备已退出静音模式，并将音量调至适中。<br>
· <b>环境建议：</b> 建议在安静环境下体验，或佩戴耳机以精准捕捉声音细节。<br>
· <b>网络保障：</b> 请使用稳定的 Wi-Fi 或 5G 网络，避免音频加载卡顿。</p>

<p style="margin-top: 20px;"><b style="color: #ffffff;">⚠️ 第二步：核心实验要求（非常重要）</b><br>
进入交互页面后，请严格遵循以下原则：<br>
· <b>手动播放：</b> AI 生成回答后，请手动点击下方语音条的“播放”按钮。<br>
· <b>完整听取：</b> 请务必 <span style="color: #4dabff; font-weight: bold;">听完整个进度条</span>。实验着重考察声音的微小变化（如停顿、节奏、语音自信度等），漏听或跳听会导致您的直觉判断偏离实际。<br>
· <b>反复确认：</b> 如果第一遍未听清，您可以重复播放或拖动进度条重听。<br>
· <b>耐心等待：</b> 语音为大模型实时生成，加载需几秒钟时间，请稍作等待。</p>

<p style="margin-top: 20px;"><b style="color: #ffffff;">📝 第三步：完成问卷</b><br>
请完成<b style="color: #3b82f6;">全部三个问题的交互后</b>，请跟随您的<b>第一直觉</b>，点击页面右上角的“进入问答环节”按钮，跳转至问卷页面进行最终评分。</p>

<p style="margin-top: 28px; color: #4dabff; text-align: center;">
<b>感谢您的配合！您的认真反馈对本研究结论至关重要。</b>
</p>
</div>
</div>
""", unsafe_allow_html=True)

    _, col_btn, _ = st.columns([0.1, 0.8, 0.1])
    with col_btn:
        if st.button("我已阅读说明，进入实验 (下一页)", use_container_width=True):
            st.session_state.page = 2
            st.rerun()

# --- 第二页：实验交互 ---
elif st.session_state.page == 2:

    if st.button("⬅ 返回", key="back_btn"):
        st.session_state.page = 1
        st.rerun()

    if st.button("进入问答环节", type="primary", key="finish_btn"):
        st.session_state.page = 3
        st.rerun()

    # ========================================================
    # 聊天内容渲染（滚动区）
    # ========================================================
    chat_html = '<div class="scroll-wrap" id="chatWrap">'
    
    if not st.session_state.messages and not st.session_state.pending_question:
        chat_html += '<div style="display:flex;align-items:center;justify-content:center;height:100%;opacity:0.4;font-size:13px;color:#c0d8ff;">请在底部选择问题发送</div>'
    else:
        # 1. 渲染已完成的历史记录
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                chat_html += f'<div class="bubble-user-wrap"><div class="bubble-user">{msg["content"]}</div></div>'
            else:
                audio_b64 = msg.get("audio_b64", "")
                audio_html = f'<audio controls src="data:audio/mp3;base64,{audio_b64}"></audio>' if audio_b64 else '<div style="color:#ff6b6b; font-size:12px; margin-top:8px;">⚠️ 无法加载音频，请检查文件路径是否正确。</div>'
                chat_html += f'''
                <div class="bubble-ai-wrap">
                    <div class="ai-dot">🎙️</div>
                    <div style="flex:1;">
                        <div class="bubble-ai">{msg["content"]}</div>
                        {audio_html}
                    </div>
                </div>'''

        # 2. 如果存在 pending_question，说明用户刚发了问题，立刻渲染“正在加载中”气泡
        if st.session_state.pending_question:
            chat_html += '''
            <div class="bubble-ai-wrap">
                <div class="ai-dot">🎙️</div>
                <div style="flex:1;">
                    <div class="bubble-ai" style="color: #4dabff; font-weight: bold; font-style: italic;">正在加载中.....</div>
                </div>
            </div>'''
            
    chat_html += '</div>'
    
    # 1.2倍速脚本注入
    chat_html += """
    <script>
        var audios = window.parent.document.getElementsByTagName('audio');
        for (var i = 0; i < audios.length; i++) {
            audios[i].playbackRate = 1.2;
        }
    </script>
    """
    
    st.markdown(chat_html, unsafe_allow_html=True)

    # 底部对话控制器
    options = ["请点击选择一个问题进行咨询..."] + list(SHORT_TO_LONG.keys())
    col_sel, col_btn = st.columns([3.5, 1], gap="small")

    with col_sel:
        selected_short = st.selectbox("Q", options, label_visibility="collapsed")
    with col_btn:
        send_trigger = st.button("发送", use_container_width=True)

    # ========================================================
    # 步骤一：触发发送，保存提问，并标记为 pending 状态，立即刷新页面
    # ========================================================
    if send_trigger and selected_short != "请点击选择一个问题进行咨询...":
        long_question = SHORT_TO_LONG[selected_short]
        # 存入用户问题
        st.session_state.messages.append({"role": "user", "content": long_question})
        # 标记当前正在等待生成
        st.session_state.pending_question = long_question
        # 立刻重载，让上方渲染出“正在加载中.....”
        st.rerun()

    # ========================================================
    # 步骤二：页面重新载入后，展示了“正在加载中”，现在执行2秒等待并加载答案
    # ========================================================
    if st.session_state.pending_question:
        long_question = st.session_state.pending_question
        answer = SPECIFIC_RESPONSES[long_question]
        audio_path = AUDIO_MAPPING[long_question]
        
        # 让页面在前端显示“正在加载中.....”保持 2 秒钟
        time.sleep(2)

        audio_b64 = ""
        if os.path.exists(audio_path):
            with open(audio_path, "rb") as f:
                audio_b64 = base64.b64encode(f.read()).decode()
        
        # 移除 pending 状态，追加正式回答
        st.session_state.pending_question = None
        st.session_state.messages.append({
            "role": "assistant", 
            "content": answer, 
            "audio_b64": audio_b64
        })
        # 再次重载，用真实的文字和语音替换掉“正在加载中.....”
        st.rerun()


# --- 第三页：问卷跳转 ---
elif st.session_state.page == 3:
    st.markdown("""
<div class="scroll-wrap">
<div style="text-align:center; padding-top:40px;">
<p style="font-size:18px; color:white; font-weight:bold;">实验交互已完成</p>
<p style="margin:20px 0; color:#c0d8ff;">请点击下方按钮进入问卷调查平台：</p>

<a href="https://v.wjx.cn/vm/t3s55FM.aspx" target="_self" rel="noopener noreferrer"
style="display:inline-block; background:#1941c8; color:white; padding:12px 30px; 
text-decoration:none; border-radius:8px; font-weight:bold; cursor:pointer;">
进入问卷星填写评分
</a>

</div>
</div>
""", unsafe_allow_html=True)

    _, col_back, _ = st.columns([0.2, 0.6, 0.2])
    with col_back:
        if st.button("返回查看对话", use_container_width=True):
            st.session_state.page = 2
            st.rerun()
