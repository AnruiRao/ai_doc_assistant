import streamlit as st
import httpx

st.set_page_config(page_title="AI知识文档")

with st.sidebar:
    st.title("文档管理")

    uploaded_file = st.file_uploader("上传文档", type=["txt", "pdf"])

    if uploaded_file and st.button("存入知识库"):
        try:
            r = httpx.post(
                "http://localhost:8000/upload",
                files={"file":(uploaded_file.name, uploaded_file.getvalue(), "application/octet-stream")},
                timeout=60,
            )
            r.raise_for_status()
            st.success(r.json()["message"])
        except Exception as e:
            st.error(f"入库失败：{str(e)}")

    try:
        resp = httpx.get("http://localhost:8000/documents", timeout=10)
        if resp.status_code == 200:
            docs = resp.json()
            if not docs:
                st.caption("暂无文档")
            for doc in docs:
                cols = st.columns([4,1])
                with cols[0]:
                    st.write(f"{doc['filename']}")
                    st.caption(f"{doc['chunk_count']} 片段")
                with cols[1]:
                    if st.button("删除", key=doc["id"]):
                        st.session_state.confirm_del = doc["id"]

                if st.session_state.get("confirm_del") == doc["id"]:
                    st.caption(f"确认删除 {doc['filename']}？")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("确认", key=f"ok_{doc['id']}"):
                            httpx.delete(f"http://localhost:8000/documents/{doc['id']}", timeout=10)
                            st.session_state.confirm_del = None
                            st.rerun()
                    with c2:
                        if st.button("取消", key=f"no_{doc['id']}"):
                            st.session_state.confirm_del = None
                            st.rerun()
    except httpx.ConnectError:
        st.caption("API 未连接")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if text := st.chat_input("请输入你的内容："):
    st.session_state.messages.append({"role": "user", "content": text})
    with st.chat_message("user"):
        st.write(text)
        
    history = st.session_state.messages[:-1]

    try:
        r = httpx.post(
            "http://localhost:8000/chat",
            json={"input_text": text, "history": history},
            timeout=120,
        )
        r.raise_for_status()
        answer = r.json()["reply"]
    except Exception as e:
        answer = f"请求失败： {str(e)}"

    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.write(answer)

    st.rerun()
