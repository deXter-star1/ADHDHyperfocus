import streamlit as st
import json
import time
from google import genai
from google.genai import types
from google.genai import errors

st.set_page_config(page_title="HyperFocus", page_icon="🎯", layout="centered")

st.markdown(
    """
    <style>
    [data-testid="stToolbar"], header[data-testid="stHeader"] {display: none;}
    .block-container {padding-top: 2.5rem; padding-bottom: 4rem; max-width: 720px;}
    .stButton button {font-weight: 700; letter-spacing: 0.01em; padding: 0.55rem 1.6rem;}

    /* The "do this first" hero card — coral, dark text, like the mockup */
    .start-card {background:#f25c54; border-radius:24px; padding:1.5rem 1.6rem;
                 margin:1rem 0 1.6rem 0;}
    .start-card .label {font-size:0.75rem; font-weight:800; letter-spacing:0.07em;
                        text-transform:uppercase; color:#3a0f0d;}
    .start-card .action {font-size:1.4rem; font-weight:800; color:#161616;
                         margin-top:0.4rem; line-height:1.2;}

    /* Checklist items as soft rounded rows */
    [data-testid="stCheckbox"] {background:#262626; border-radius:14px;
                                padding:0.7rem 1rem; margin-bottom:0.5rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div style="margin-bottom:1.6rem;">
      <h1 style="font-size:3rem; font-weight:900; letter-spacing:-0.02em; margin:0;">🎯 HyperFocus</h1>
      <p style="font-size:1.05rem; color:#9a9a9a; font-weight:500; margin-top:0.5rem;">
        Stuck on starting? Drop in any task and get one tiny first step to lock onto.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

api_key = st.sidebar.text_input("Gemini API key", type="password")

if "steps" not in st.session_state:
    st.session_state.steps = []

task = st.text_area(
    "What are you trying to start?",
    placeholder="e.g. Study fiber optics chapter 4 for tomorrow's exam",
    height=90,
)

if st.button("Break it down 🧩", type="primary"):
    if not api_key:
        st.error("Paste your Gemini API key in the sidebar first.")
    elif not task.strip():
        st.error("Type in a task first.")
    else:
        new_steps = None
        busy = False
        try:
            with st.spinner("Breaking it into doable pieces..."):
                client = genai.Client(api_key=api_key)
                prompt = (
                    "You are a focus coach for someone with ADHD who struggles to START "
                    "tasks but hyperfocuses once they begin. Break the task into a short list "
                    "of small, concrete, physical steps. Rules: the FIRST step must be tiny — "
                    "doable in under 2 minutes with zero prep, to beat the starting wall "
                    "(e.g. 'Open the textbook to page 40', not 'Start studying'). Each step is "
                    "one concrete physical action, not a vague goal. Keep it to 5-7 steps, "
                    "ordered so momentum builds. Plain, encouraging, non-patronizing language. "
                    'Return ONLY JSON: {"steps": ["step 1", "step 2", ...]}\n\n'
                    f"TASK: {task}"
                )
                answer = None
                for attempt in range(3):
                    try:
                        response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=prompt,
                            config=types.GenerateContentConfig(response_mime_type="application/json"),
                        )
                        answer = response.text
                        break
                    except errors.ServerError:
                        time.sleep(2)
            if answer:
                new_steps = json.loads(answer).get("steps", [])
            else:
                busy = True
        except Exception:
            st.error("Something went off. Try rewording the task.")

        if busy:
            st.warning("Gemini's busy — wait a few seconds and try again.")
        if new_steps is not None:
            for k in list(st.session_state.keys()):
                if k.startswith("step_"):
                    st.session_state.pop(k, None)
            st.session_state.steps = new_steps

steps = st.session_state.steps
if steps:
    st.markdown(
        f"""
        <div class="start-card">
          <div class="label">🎯 Just do this first</div>
          <div class="action">{steps[0]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    rest = steps[1:]
    if rest:
        st.markdown("**Then keep the momentum going:**")
        done = 0
        for i, step in enumerate(rest):
            if st.checkbox(step, key=f"step_{i}"):
                done += 1
        st.progress(done / len(rest))
        if done == len(rest):
            st.success("All done — you rode the focus all the way through. 🎉")
            st.balloons()
        else:
            st.caption(f"{done} of {len(rest)} done")

    if st.button("New task"):
        for k in list(st.session_state.keys()):
            if k.startswith("step_"):
                st.session_state.pop(k, None)
        st.session_state.steps = []
        st.rerun()