import time

SESSION_IDLE_SECONDS = 120  # demo: reset after 2 min idle


def init_session_state(st):
    if "last_activity" not in st.session_state:
        st.session_state.last_activity = time.time()

    if "step" not in st.session_state:
        st.session_state.step = "select"  # select -> lesson -> quiz1 -> reexplain_q1 -> quiz2 -> done

    if "topic_id" not in st.session_state:
        st.session_state.topic_id = None

    if "answers_q1" not in st.session_state:
        st.session_state.answers_q1 = {}

    if "answers_q2" not in st.session_state:
        st.session_state.answers_q2 = {}

    if "q1_result" not in st.session_state:
        st.session_state.q1_result = None

    if "q2_result" not in st.session_state:
        st.session_state.q2_result = None

    if "reexplain_text" not in st.session_state:
        st.session_state.reexplain_text = ""

    if "reexplain_latency" not in st.session_state:
        st.session_state.reexplain_latency = None

    if "reexplain_mode" not in st.session_state:
        st.session_state.reexplain_mode = None


def touch(st):
    st.session_state.last_activity = time.time()


def maybe_reset(st):
    now = time.time()
    if now - st.session_state.last_activity > SESSION_IDLE_SECONDS:
        st.session_state.step = "select"
        st.session_state.topic_id = None
        st.session_state.answers_q1 = {}
        st.session_state.answers_q2 = {}
        st.session_state.q1_result = None
        st.session_state.q2_result = None
        st.session_state.reexplain_text = ""
        st.session_state.reexplain_latency = None
        st.session_state.reexplain_mode = None
        st.session_state.last_activity = now
        st.toast("Session reset (idle).")