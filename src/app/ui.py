import streamlit as st
import tempfile, os
from agents.react_agent import ReactAgent
from tools.registry import ToolRegistry
from tools.impl.calculator import CalculatorTool
from tools.impl.rag_tool import RagTool

st.set_page_config(page_title="AI知识文档")

with st.sidebar:
    st.title("文档管理")

    uploaded_file = st.file_uploader("上传文档", type=["txt", "pdf"])

    if uploaded_file and st.button("存入知识库"):
        try:
            suffix = os.path.splitext(uploaded_file.name)[1]
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(uploaded_file.getbuffer())
                temp_path = f.name

            rag_tool = st.session_state.agent.tool_registry.get_tool("rag_tool")
            result = rag_tool.run(use_for="save", path=temp_path)
            st.success(result)
        except Exception as e:
            st.error(f"入库失败：{str(e)}")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

if "agent" not in st.session_state:
    registry = ToolRegistry()
    registry.register_tool(CalculatorTool())
    registry.register_tool(RagTool())
    st.session_state.agent = ReactAgent(tool_registry=registry)

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
    answer = st.session_state.agent.run(input_text=text,history=history)
    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.write(answer)
