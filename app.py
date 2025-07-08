# app.py
# 바로 실행 가능한 DSPy + mem0 + 웹검색 Streamlit 앱

import streamlit as st
import dspy
from mem0 import Memory
import os
from datetime import datetime
from typing import List, Dict, Any
import json

# 웹 검색을 위한 간단한 구현
try:
    from duckduckgo_search import DDGS
    import wikipediaapi
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False

# Streamlit 설정
st.set_page_config(
    page_title="🧠 AI 메모리 어시스턴트",
    page_icon="🤖",
    layout="wide"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        text-align: center;
        margin-bottom: 1rem;
        color: #1f77b4;
    }
    .user-msg {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        margin-left: 20px;
    }
    .assistant-msg {
        background-color: #e8f4f8;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        margin-right: 20px;
    }
    .memory-box {
        background-color: #f9f9f9;
        padding: 8px;
        border-radius: 5px;
        margin: 3px 0;
        border-left: 4px solid #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# 웹 검색 도구 클래스
class SimpleWebSearch:
    def __init__(self):
        self.available = WEB_SEARCH_AVAILABLE
        if self.available:
            self.wiki = wikipediaapi.Wikipedia(language='ko', user_agent='DSPy-Agent/1.0')
    
    def search_wikipedia(self, query: str) -> str:
        if not self.available:
            return "웹 검색 패키지가 설치되지 않았습니다. pip install duckduckgo-search wikipedia-api"
        
        try:
            page = self.wiki.page(query)
            if page.exists():
                summary = page.summary
                sentences = summary.split('.')[:3]
                result = '. '.join(sentences) + '.'
                return f"Wikipedia 검색 '{query}':\n{result}"
            else:
                return f"Wikipedia에서 '{query}' 정보를 찾을 수 없습니다."
        except Exception as e:
            return f"Wikipedia 검색 오류: {str(e)}"
    
    def search_web(self, query: str) -> str:
        if not self.available:
            return "웹 검색 패키지가 설치되지 않았습니다."
        
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))
            
            if results:
                search_result = f"웹 검색 '{query}':\n\n"
                for i, result in enumerate(results, 1):
                    search_result += f"{i}. {result['title']}\n{result['body'][:150]}...\n\n"
                return search_result
            else:
                return f"'{query}'에 대한 검색 결과가 없습니다."
        except Exception as e:
            return f"웹 검색 오류: {str(e)}"

# 메모리 도구 클래스
class SimpleMemoryTools:
    def __init__(self, memory):
        self.memory = memory
    
    def store_memory(self, content: str, user_id: str = "default") -> str:
        try:
            self.memory.add(content, user_id=user_id)
            return f"✅ 메모리 저장: {content[:50]}..."
        except Exception as e:
            return f"❌ 메모리 저장 실패: {str(e)}"
    
    def search_memories(self, query: str, user_id: str = "default") -> str:
        try:
            results = self.memory.search(query, user_id=user_id, limit=5)
            if not results or 'results' not in results:
                return "관련 메모리가 없습니다."
            
            memory_text = "관련 메모리:\n"
            for i, result in enumerate(results['results'], 1):
                memory_text += f"{i}. {result['memory']}\n"
            return memory_text
        except Exception as e:
            return f"메모리 검색 오류: {str(e)}"
    
    def get_all_memories(self, user_id: str = "default") -> List[str]:
        try:
            results = self.memory.get_all(user_id=user_id)
            if not results or 'results' not in results:
                return []
            return [result['memory'] for result in results['results']]
        except:
            return []

# 간단한 에이전트 클래스 (ReAct 없이)
class SimpleAgent:
    def __init__(self, memory, web_search):
        self.memory_tools = SimpleMemoryTools(memory)
        self.web_search = web_search
        
        # DSPy 설정
        if os.getenv("OPENAI_API_KEY"):
            lm = dspy.LM(model='openai/gpt-4o-mini')
            dspy.configure(lm=lm)
            self.qa = dspy.ChainOfThought("context, question -> reasoning, answer")
        else:
            self.qa = None
    
    def process_message(self, user_input: str, user_id: str = "default") -> str:
        # 1. 웹 검색이 필요한지 판단
        search_keywords = ["검색", "최신", "뉴스", "찾아", "알려줘", "정보"]
        needs_search = any(keyword in user_input for keyword in search_keywords)
        
        context = ""
        
        # 2. 웹 검색 수행
        if needs_search:
            search_result = self.web_search.search_wikipedia(user_input)
            context += f"검색 결과:\n{search_result}\n\n"
            # 검색 결과를 메모리에 저장
            self.memory_tools.store_memory(f"검색: {user_input} - {search_result[:100]}...", user_id)
        
        # 3. 관련 메모리 검색
        memory_result = self.memory_tools.search_memories(user_input, user_id)
        context += f"관련 기억:\n{memory_result}\n\n"
        
        # 4. AI 응답 생성
        if self.qa and os.getenv("OPENAI_API_KEY"):
            try:
                result = self.qa(context=context, question=user_input)
                response = result.answer
                # 중요한 정보를 메모리에 저장
                if len(user_input) > 10:  # 의미있는 대화만 저장
                    self.memory_tools.store_memory(f"대화: {user_input} -> {response[:100]}...", user_id)
            except Exception as e:
                response = f"AI 응답 생성 중 오류: {str(e)}"
        else:
            # API 키가 없을 때 기본 응답
            response = f"'{user_input}'에 대한 응답입니다. OpenAI API 키를 설정하면 더 정교한 답변을 받을 수 있습니다."
            if context:
                response = f"{context}\n\n{response}"
        
        return response

# 세션 상태 초기화
def init_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = "user_001"

# 에이전트 설정
def setup_agent():
    if st.session_state.agent is None:
        try:
            # mem0 설정
            config = {
                "llm": {
                    "provider": "openai",
                    "config": {
                        "model": "gpt-4o-mini",
                        "temperature": 0.1,
                        "api_key": os.getenv("OPENAI_API_KEY")
                    }
                } if os.getenv("OPENAI_API_KEY") else None
            }
            
            memory = Memory.from_config(config) if config["llm"] else Memory()
            web_search = SimpleWebSearch()
            agent = SimpleAgent(memory, web_search)
            
            st.session_state.agent = agent
            return True
        except Exception as e:
            st.error(f"에이전트 설정 실패: {str(e)}")
            return False
    return True

# 메인 앱
def main():
    init_session_state()
    
    st.markdown('<div class="main-header">🧠 AI 메모리 어시스턴트</div>', unsafe_allow_html=True)
    
    # 사이드바
    with st.sidebar:
        st.header("⚙️ 설정")
        
        # API 키 입력
        api_key = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            st.success("✅ API 키 설정됨")
        else:
            st.warning("⚠️ API 키 필요")
        
        # 사용자 ID
        user_id = st.text_input("사용자 ID", value=st.session_state.user_id)
        st.session_state.user_id = user_id
        
        st.markdown("---")
        
        # 기능 상태
        st.header("📊 기능 상태")
        st.write(f"웹 검색: {'✅' if WEB_SEARCH_AVAILABLE else '❌'}")
        st.write(f"API 키: {'✅' if api_key else '❌'}")
        
        if not WEB_SEARCH_AVAILABLE:
            st.info("웹 검색을 위해 설치하세요:\npip install duckduckgo-search wikipedia-api")
        
        st.markdown("---")
        
        # 대화 관리
        if st.button("🗑️ 대화 삭제"):
            st.session_state.messages = []
            st.rerun()
    
    # 메인 영역
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 대화")
        
        # 에이전트 설정
        if setup_agent():
            # 대화 내역 표시
            for msg in st.session_state.messages:
                if msg['role'] == 'user':
                    st.markdown(f'<div class="user-msg">👤 <strong>사용자:</strong><br>{msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="assistant-msg">🤖 <strong>AI:</strong><br>{msg["content"]}</div>', unsafe_allow_html=True)
            
            # 사용자 입력
            user_input = st.chat_input("메시지를 입력하세요...")
            
            if user_input:
                # 사용자 메시지 추가
                st.session_state.messages.append({"role": "user", "content": user_input})
                
                # AI 응답 생성
                with st.spinner("🤖 AI가 생각하는 중..."):
                    response = st.session_state.agent.process_message(user_input, st.session_state.user_id)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                
                st.rerun()
        else:
            st.error("에이전트를 설정할 수 없습니다.")
    
    with col2:
        st.header("🧠 메모리")
        
        if st.session_state.agent:
            memories = st.session_state.agent.memory_tools.get_all_memories(st.session_state.user_id)
            
            if memories:
                st.write(f"저장된 기억: {len(memories)}개")
                for i, memory in enumerate(memories[-5:], 1):  # 최근 5개만 표시
                    st.markdown(f'<div class="memory-box">{i}. {memory}</div>', unsafe_allow_html=True)
            else:
                st.info("💭 아직 저장된 기억이 없습니다.")
        
        st.markdown("---")
        
        # 통계
        st.header("📊 통계")
        total_msgs = len(st.session_state.messages)
        user_msgs = len([m for m in st.session_state.messages if m['role'] == 'user'])
        
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.metric("총 메시지", total_msgs)
        with col_stat2:
            st.metric("사용자 메시지", user_msgs)

if __name__ == "__main__":
    main()