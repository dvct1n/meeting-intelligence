"""Streamlit front-end.  Run:  streamlit run ui/streamlit_app.py"""
import os

import pandas as pd
import requests
import streamlit as st

API = os.getenv("API_URL", "http://localhost:8000")
HEADERS = {"X-API-Key": os.environ["API_KEY"]} if os.getenv("API_KEY") else {}

st.set_page_config(page_title="AI Meeting Intelligence", page_icon="🎙️", layout="wide")
st.title("🎙️ AI Meeting Intelligence")


def fmt(sec: float) -> str:
    sec = int(sec)
    return f"{sec // 3600}:{sec % 3600 // 60:02d}:{sec % 60:02d}" if sec >= 3600 else f"{sec // 60:02d}:{sec % 60:02d}"


def call(method: str, path: str, **kw):
    r = requests.request(method, f"{API}{path}", headers=HEADERS, timeout=60, **kw)
    r.raise_for_status()
    return r


def api(method: str, path: str, **kw):
    r = call(method, path, **kw)
    return r.json() if r.content else None


try:
    meetings = api("GET", "/meetings")
except Exception as e:
    st.error(f"Cannot reach the API at {API}: {e}")
    st.stop()


def label(m: dict) -> str:
    return f"{(m.get('analysis') or {}).get('title') or m['filename']} · {m['created_at'][:16]} · {m['status']}"


tab_up, tab_view, tab_search = st.tabs(["⬆️ Upload", "📋 Meeting", "🔎 Search"])

with tab_up:
    f = st.file_uploader("Meeting recording", type=["wav", "mp3", "m4a", "mp4", "flac", "ogg", "webm", "mkv"])
    if f and st.button("Process recording", type="primary"):
        try:
            m = api("POST", "/meetings", files={"file": (f.name, f.getvalue())})
            st.success(f"Uploaded. Meeting id: {m['id']}. Processing runs in the background; open the Meeting tab.")
        except requests.HTTPError as e:
            st.error(e.response.json().get("detail", str(e)))


BUSY = ("uploaded", "processing")


def meeting_view(meeting_id: str, was_busy: bool) -> None:
    m = api("GET", f"/meetings/{meeting_id}")
    if m["status"] in BUSY:
        st.info("⏳ Processing… this page refreshes automatically.")
        return
    if was_busy:
        st.rerun()  # job just finished: rerun the whole app so polling stops and the list updates
    if m["status"] == "failed":
        st.error(m.get("error") or "Processing failed")
        return

    a = m["analysis"] or {}
    st.header(a.get("title", "Meeting"))
    st.caption(f"Duration {fmt(m['duration'])} · {len({u['speaker'] for u in m['utterances']})} speakers")
    st.download_button(
        "⬇️ Download report (Markdown)", call("GET", f"/meetings/{meeting_id}/export").content,
        file_name=f"meeting-{meeting_id}.md", mime="text/markdown",
    )
    st.write(a.get("summary", ""))
    if a.get("topics"):
        st.markdown("**Topics:** " + " · ".join(a["topics"]))
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("✅ Decisions")
        for d in a.get("decisions", []) or [{"decision": "None found"}]:
            st.markdown(f"- {d['decision']}" + (f"  \n  _{d['rationale']}_" if d.get("rationale") else ""))
    with c2:
        st.subheader("📌 Action items")
        if a.get("action_items"):
            st.dataframe(
                pd.DataFrame(a["action_items"]).rename(columns={"task": "Task", "owner": "Owner", "deadline": "Deadline"}),
                hide_index=True,
            )
        else:
            st.write("None found")
    if a.get("speaker_summaries"):
        st.subheader("🗣️ Speakers")
        for spk, txt in a["speaker_summaries"].items():
            with st.expander(spk):
                st.write(txt)
    with st.expander("Topic chunks"):
        for c in m["chunks"]:
            st.markdown(f"**{fmt(c['start'])}–{fmt(c['end'])}** · {', '.join(c['speakers'])}")
            st.write(c.get("summary") or "")
    with st.expander("Full transcript"):
        for u in m["utterances"]:
            st.markdown(f"`{fmt(u['start'])}` **{u['speaker']}**: {u['text']}")


with tab_view:
    if not meetings:
        st.info("No meetings yet.")
    else:
        choice = st.selectbox("Select a meeting", meetings, format_func=label)
        if st.button("🗑️ Delete this meeting"):
            try:
                api("DELETE", f"/meetings/{choice['id']}")
                st.rerun()
            except requests.HTTPError as e:
                st.error(e.response.json().get("detail", str(e)))
        busy = choice["status"] in BUSY
        # poll every 5 s only while the selected meeting is still being processed
        st.fragment(meeting_view, run_every=5 if busy else None)(choice["id"], busy)

with tab_search:
    q = st.text_input("Ask something across your meetings", placeholder="What did we decide about the release date?")
    scope = st.selectbox("Scope", [None, *meetings], format_func=lambda m: "All meetings" if m is None else label(m))
    if q:
        hits = api("POST", "/search", json={"query": q, "meeting_id": scope["id"] if scope else None, "limit": 5})
        if not hits:
            st.info("No results.")
        for h in hits:
            with st.container(border=True):
                st.markdown(
                    f"**score {h['score']:.2f}** · meeting `{h['meeting_id']}` · "
                    f"{fmt(h['start'])}–{fmt(h['end'])} · {', '.join(h['speakers'])}"
                )
                if h.get("summary"):
                    st.write(h["summary"])
                with st.expander("Transcript excerpt"):
                    st.text(h["text"])
