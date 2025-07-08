# app.py
# 바로 실행 가능한 DSPy + mem0 + 웹검색 Streamlit 앱 (개선된 스타일링)

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
    layout="wide",
    initial_sidebar_state="expanded"
)

# 개선된 CSS 스타일
st.markdown("""
<style>
    /* 전체 앱 스타일링 */
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1.5rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* 메시지 스타일 개선 */
    .user-msg {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 18px 18px 5px 18px;
        margin: 8px 0 8px 60px;
        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
        position: relative;
        word-wrap: break-word;
    }
    
    .user-msg::before {
        content: "👤";
        position: absolute;
        left: -45px;
        top: 50%;
        transform: translateY(-50%);
        background: #667eea;
        width: 35px;
        height: 35px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
    }
    
    .assistant-msg {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 18px 18px 18px 5px;
        margin: 8px 60px 8px 0;
        box-shadow: 0 2px 10px rgba(240, 147, 251, 0.3);
        position: relative;
        word-wrap: break-word;
    }
    
    .assistant-msg::before {
        content: "🤖";
        position: absolute;
        right: -45px;
        top: 50%;
        transform: translateY(-50%);
        background: #f093fb;
        width: 35px;
        height: 35px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
    }
    
    /* 메모리 박스 개선 */
    .memory-box {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 12px 16px;
        border-radius: 12px;
        margin: 8px 0;
        border-left: 4px solid #4CAF50;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
        font-size: 0.9rem;
    }
    
    .memory-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* 사이드바 스타일링 */
    .sidebar-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px;
        border-radius: 10px;
        text-align: center;
        font-weight: 600;
        margin-bottom: 20px;
    }
    
    /* 상태 표시 스타일 */
    .status-item {
        display: flex;
        align-items: center;
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 8px;
        background: #f8f9fa;
        border: 1px solid #e9ecef;
    }
    
    .status-success {
        background: #d4edda;
        border-color: #c3e6cb;
        color: #155724;
    }
    
    .status-warning {
        background: #fff3cd;
        border-color: #ffeaa7;
        color: #856404;
    }
    
    /* 통계 카드 */
    .metric-card {
        background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        margin: 8px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .metric-number {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2d3436;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #636e72;
        margin-top: 5px;
    }
    
    /* 채팅 입력창 영역 */
    .chat-input-container {
        background: #ffffff;
        border-radius: 15px;
        padding: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-top: 20px;
    }
    
    /* 로딩 상태 */
    .loading-indicator {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
        color: #667eea;
        font-style: italic;
    }
    
    /* 버튼 개선 */
    .stButton > button {
        border-radius: 20px;
        border: none;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* 스크롤바 커스터마이징 */
    .main .block-container {
        max-height: 80vh;
        overflow-y: auto;
    }
    
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    /* 반응형 디자인 */
    @media (max-width: 768px) {
        .user-msg, .assistant-msg {
            margin-left: 10px;
            margin-right: 10px;
        }
        
        .user-msg::before, .assistant-msg::before {
            display: none;
        }
        
        .main-header {
            font-size: 1.8rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# 웹 검색 도구 클래스 (기존과 동일)
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

# 메모리 도구 클래스 (기존과 동일)
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

# 간단한 에이전트 클래스 (기존과 동일)
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

# 세션 상태 초기화 (기존과 동일)
def init_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = "user_001"

# 에이전트 설정 (기존과 동일)
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

# 개선된 사이드바 생성 함수
def create_sidebar():
    with st.sidebar:
        st.markdown('<div class="sidebar-header">⚙️ 설정 & 상태</div>', unsafe_allow_html=True)
        
        # API 키 입력
        api_key = st.text_input("🔑 OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        
        # 사용자 ID
        user_id = st.text_input("👤 사용자 ID", value=st.session_state.user_id)
        st.session_state.user_id = user_id
        
        st.markdown("---")
        
        # 기능 상태
        st.markdown("### 📊 시스템 상태")
        
        # API 키 상태
        if api_key:
            st.markdown('<div class="status-item status-success">✅ API 키 연결됨</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-item status-warning">⚠️ API 키 필요</div>', unsafe_allow_html=True)
        
        # 웹 검색 상태
        if WEB_SEARCH_AVAILABLE:
            st.markdown('<div class="status-item status-success">✅ 웹 검색 가능</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-item status-warning">⚠️ 웹 검색 비활성화</div>', unsafe_allow_html=True)
            st.info("웹 검색을 위해 설치하세요:\n`pip install duckduckgo-search wikipedia-api`")
        
        st.markdown("---")
        
        # 대화 관리
        if st.button("🗑️ 대화 내역 삭제", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

# 개선된 메시지 렌더링 함수
def render_messages():
    for msg in st.session_state.messages:
        if msg['role'] == 'user':
            st.markdown(f'<div class="user-msg">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="assistant-msg">{msg["content"]}</div>', unsafe_allow_html=True)

# 개선된 메모리 패널 함수
def create_memory_panel():
    st.markdown("### 🧠 메모리 상태")
    
    if st.session_state.agent:
        memories = st.session_state.agent.memory_tools.get_all_memories(st.session_state.user_id)
        
        if memories:
            st.markdown(f"**저장된 기억: {len(memories)}개**")
            # 최근 5개만 표시
            for i, memory in enumerate(memories[-5:], 1):
                st.markdown(f'<div class="memory-box">💭 {memory}</div>', unsafe_allow_html=True)
        else:
            st.info("💭 아직 저장된 기억이 없습니다.")
    
    st.markdown("---")
    
    # 통계 정보
    st.markdown("### 📊 사용 통계")
    total_msgs = len(st.session_state.messages)
    user_msgs = len([m for m in st.session_state.messages if m['role'] == 'user'])
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-number">{total_msgs}</div>
            <div class="metric-label">총 메시지</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-number">{user_msgs}</div>
            <div class="metric-label">사용자 메시지</div>
        </div>
        ''', unsafe_allow_html=True)

# 메인 앱
def main():
    init_session_state()
    
    # 헤더
    st.markdown('<div class="main-header">🧠 AI 메모리 어시스턴트</div>', unsafe_allow_html=True)
    
    # 사이드바
    create_sidebar()
    
    # 메인 영역 (2열 구조 유지)
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 💬 대화")
        
        # 에이전트 설정
        if setup_agent():
            # 대화 내역 표시
            render_messages()
            
            # 사용자 입력
            st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
            user_input = st.chat_input("메시지를 입력하세요...")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if user_input:
                # 사용자 메시지 추가
                st.session_state.messages.append({"role": "user", "content": user_input})
                
                # AI 응답 생성
                with st.spinner("🤖 AI가 생각하는 중..."):
                    response = st.session_state.agent.process_message(user_input, st.session_state.user_id)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                
                st.rerun()
        else:
            st.error("❌ 에이전트를 설정할 수 없습니다.")
    
    with col2:
        create_memory_panel()

if __name__ == "__main__":
    main()