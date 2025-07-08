# app.py
# ChatGPT/Claude 스타일의 완전한 대화 관리 시스템을 갖춘 DSPy + mem0 + 웹검색 Streamlit 앱

import streamlit as st
import dspy
from mem0 import Memory
import os
import uuid
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any

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

# 기존 CSS 스타일 (그대로 유지)
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
    
    /* 메시지 컨테이너 */
    .message-container {
        margin: 12px 0;
        position: relative;
    }
    
    .user-message-container {
        display: flex;
        justify-content: flex-end;
        align-items: flex-start;
        margin-left: 60px;
    }
    
    .assistant-message-container {
        display: flex;
        justify-content: flex-start;
        align-items: flex-start;
        margin-right: 60px;
    }
    
    /* 메시지 스타일 개선 */
    .user-msg {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 18px 18px 5px 18px;
        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
        position: relative;
        word-wrap: break-word;
        max-width: 80%;
    }
    
    .user-msg::before {
        content: "👤";
        position: absolute;
        right: -45px;
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
        box-shadow: 0 2px 10px rgba(240, 147, 251, 0.3);
        position: relative;
        word-wrap: break-word;
        max-width: 80%;
    }
    
    .assistant-msg::before {
        content: "🤖";
        position: absolute;
        left: -45px;
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
    
    /* 타임스탬프 */
    .message-timestamp {
        font-size: 0.75rem;
        opacity: 0.7;
        margin-top: 5px;
        text-align: right;
    }
    
    .user-message-container .message-timestamp {
        text-align: right;
    }
    
    .assistant-message-container .message-timestamp {
        text-align: left;
    }
    
    /* 3열 레이아웃 스타일 */
    .three-column-container {
        display: flex;
        gap: 20px;
        height: 80vh;
        max-width: 100%;
    }
    
    .left-sidebar {
        flex: 0 0 280px;
        background: linear-gradient(145deg, #f8f9fa, #e9ecef);
        border-radius: 15px;
        padding: 20px;
        overflow-y: auto;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .main-chat-area {
        flex: 1;
        display: flex;
        flex-direction: column;
        background: #ffffff;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        overflow: hidden;
    }
    
    .right-panel {
        flex: 0 0 320px;
        background: linear-gradient(145deg, #f1f3f4, #e8eaed);
        border-radius: 15px;
        padding: 20px;
        overflow-y: auto;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* 채팅 영역 내부 구조 */
    .chat-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        text-align: center;
        font-weight: 600;
        font-size: 1.2rem;
    }
    
    .chat-messages {
        flex: 1;
        padding: 20px;
        overflow-y: auto;
        background: #fafbfc;
    }
    
    .chat-input-area {
        border-top: 1px solid #e9ecef;
        padding: 20px;
        background: white;
    }
    
    /* 사이드바 섹션 스타일 */
    .sidebar-section {
        margin-bottom: 25px;
        padding-bottom: 15px;
        border-bottom: 1px solid #dee2e6;
    }
    
    .sidebar-section:last-child {
        border-bottom: none;
    }
    
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #495057;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* 우측 패널 스타일 */
    .panel-section {
        background: white;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .panel-header {
        font-size: 1rem;
        font-weight: 600;
        color: #495057;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
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
    @media (max-width: 1200px) {
        .three-column-container {
            flex-direction: column;
            height: auto;
        }
        
        .left-sidebar, .right-panel {
            flex: none;
            width: 100%;
            max-height: 300px;
        }
        
        .main-chat-area {
            min-height: 60vh;
        }
    }
</style>
""", unsafe_allow_html=True)

# 대화 템플릿 정의
CONVERSATION_TEMPLATES = {
    "coding": {
        "title": "💻 코딩 도움",
        "description": "프로그래밍 질문과 코드 리뷰를 위한 대화",
        "initial_message": "안녕하세요! 코딩 관련 질문이나 도움이 필요한 부분이 있나요? 프로그래밍 언어, 알고리즘, 디버깅, 코드 리뷰 등 무엇이든 도와드리겠습니다.",
        "suggested_prompts": [
            "Python 함수 작성 도움",
            "코드 오류 디버깅", 
            "알고리즘 최적화",
            "코드 리뷰 요청"
        ]
    },
    "writing": {
        "title": "✍️ 글쓰기 도움",
        "description": "창작, 에세이, 보고서 작성을 위한 대화",
        "initial_message": "창작 활동이나 글쓰기에 도움이 필요하신가요? 소설, 에세이, 보고서, 블로그 포스트 등 어떤 종류의 글이든 함께 작업해보겠습니다.",
        "suggested_prompts": [
            "블로그 포스트 아이디어",
            "소설 플롯 구성",
            "보고서 구조 잡기", 
            "문체 개선 요청"
        ]
    },
    "learning": {
        "title": "📚 학습 도우미",
        "description": "새로운 주제 학습과 설명을 위한 대화",
        "initial_message": "새로운 것을 배우고 싶으신가요? 복잡한 개념도 쉽게 설명해드리고, 단계별로 학습할 수 있도록 도와드리겠습니다.",
        "suggested_prompts": [
            "개념 쉽게 설명해주세요",
            "예시와 함께 알려주세요",
            "연습 문제 만들어주세요",
            "심화 내용 추천"
        ]
    },
    "brainstorm": {
        "title": "💡 아이디어 브레인스토밍", 
        "description": "창의적 아이디어 발상과 기획을 위한 대화",
        "initial_message": "새로운 아이디어가 필요하신가요? 함께 브레인스토밍하며 창의적인 솔루션을 찾아보겠습니다!",
        "suggested_prompts": [
            "비즈니스 아이디어",
            "프로젝트 기획",
            "문제 해결 방안",
            "창의적 접근법"
        ]
    }
}

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
        
        # DSPy 설정 (선택된 모델 사용)
        if os.getenv("OPENAI_API_KEY"):
            selected_model = getattr(st.session_state, 'selected_model', 'gpt-4o-mini')
            lm = dspy.LM(model=f'openai/{selected_model}')
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
            # Wikipedia 검색
            wiki_result = self.web_search.search_wikipedia(user_input)
            context += f"Wikipedia 검색:\n{wiki_result}\n\n"
            
            # 일반 웹 검색
            web_result = self.web_search.search_web(user_input)
            context += f"웹 검색:\n{web_result}\n\n"
            
            # 검색 결과를 메모리에 저장
            self.memory_tools.store_memory(f"검색: {user_input} - Wikipedia: {wiki_result[:50]}... Web: {web_result[:50]}...", user_id)
        
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
            selected_model = getattr(st.session_state, 'selected_model', 'gpt-4o-mini')
            response = f"'{user_input}'에 대한 응답입니다. (모델: {selected_model})\nOpenAI API 키를 설정하면 더 정교한 답변을 받을 수 있습니다."
            if context:
                response = f"{context}\n\n{response}"
        
        return response

# 대화 세션 관리 클래스
class ConversationManager:
    """ChatGPT 스타일의 대화 세션 관리"""
    
    def __init__(self):
        self.init_conversation_state()
    
    def init_conversation_state(self):
        """대화 상태 초기화"""
        if 'conversations' not in st.session_state:
            st.session_state.conversations = {}
        
        if 'current_conversation_id' not in st.session_state:
            st.session_state.current_conversation_id = None
        
        if 'conversation_list' not in st.session_state:
            st.session_state.conversation_list = []
    
    def create_new_conversation(self, title=None):
        """새 대화 세션 생성 (ChatGPT 스타일)"""
        # 현재 대화가 있고 메시지가 있다면 자동 저장
        if (st.session_state.current_conversation_id and 
            st.session_state.current_conversation_id in st.session_state.conversations and
            st.session_state.conversations[st.session_state.current_conversation_id]['messages']):
            
            self.save_current_conversation(auto_generate_title=True)
        
        # 새 대화 세션 ID 생성
        new_conversation_id = str(uuid.uuid4())
        
        # 새 대화 세션 생성
        new_conversation = {
            'id': new_conversation_id,
            'title': title or "새 대화",
            'messages': [],
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'user_id': st.session_state.user_id,
            'model': st.session_state.selected_model,
            'starred': False
        }
        
        # 세션 상태 업데이트
        st.session_state.conversations[new_conversation_id] = new_conversation
        st.session_state.current_conversation_id = new_conversation_id
        st.session_state.messages = []  # 현재 메시지 초기화
        
        # 대화 목록에 추가 (최신순)
        st.session_state.conversation_list.insert(0, new_conversation_id)
        
        st.toast("✨ 새 대화가 시작되었습니다!")
        return new_conversation_id
    
    def save_current_conversation(self, auto_generate_title=True):
        """현재 대화 저장"""
        if not st.session_state.current_conversation_id:
            return False
        
        conversation_id = st.session_state.current_conversation_id
        
        if conversation_id in st.session_state.conversations:
            # 현재 메시지를 대화에 저장
            st.session_state.conversations[conversation_id]['messages'] = st.session_state.messages.copy()
            st.session_state.conversations[conversation_id]['updated_at'] = datetime.now()
            
            # 대화 제목 자동 생성 (AI 기반 또는 규칙 기반)
            if (auto_generate_title and 
                st.session_state.conversations[conversation_id]['title'] == "새 대화" and
                len(st.session_state.messages) >= 2):
                
                agent = getattr(st.session_state, 'agent', None)
                new_title = self.generate_conversation_title(st.session_state.messages, agent)
                st.session_state.conversations[conversation_id]['title'] = new_title
            
            return True
        return False
    
    def generate_conversation_title(self, messages, agent=None):
        """대화 제목 자동 생성"""
        if not messages or len(messages) < 2:
            return "새 대화"
        
        # 첫 번째 사용자 메시지에서 키워드 추출
        user_messages = [msg for msg in messages if msg['role'] == 'user']
        if user_messages:
            first_message = user_messages[0]['content']
            
            # 간단한 키워드 기반 제목 생성
            keywords = self.extract_keywords(first_message)
            if keywords:
                title = " ".join(keywords[:3])  # 첫 3개 키워드
                return title[:25] + "..." if len(title) > 25 else title
            else:
                # 첫 메시지의 처음 부분 사용
                title = first_message[:25]
                return title + "..." if len(first_message) > 25 else title
        
        return "새 대화"
    
    def extract_keywords(self, text):
        """간단한 키워드 추출 (한국어 지원)"""
        # 한국어 단어 추출 (2글자 이상)
        korean_words = re.findall(r'[가-힣]{2,}', text)
        
        # 영어 단어 추출
        english_words = re.findall(r'[a-zA-Z]{3,}', text)
        
        # 불용어 제거
        stopwords = {'이것', '그것', '저것', '여기', '거기', '저기', '이거', '그거', '저거',
                    '무엇', '누구', '언제', '어디', '어떻게', '왜', '어떤', '그런', '이런',
                    '있는', '없는', '하는', '되는', '같은', '다른', '많은', '적은', '좋은', '나쁜'}
        
        all_words = korean_words + english_words
        keywords = [word for word in all_words if word not in stopwords and len(word) >= 2]
        
        # 중복 제거하면서 순서 유지
        seen = set()
        unique_keywords = []
        for word in keywords:
            if word not in seen:
                seen.add(word)
                unique_keywords.append(word)
        
        return unique_keywords[:5]  # 최대 5개 키워드
    
    def load_conversation(self, conversation_id):
        """특정 대화 로드"""
        if conversation_id in st.session_state.conversations:
            # 현재 대화 먼저 저장
            if st.session_state.current_conversation_id:
                self.save_current_conversation()
            
            # 선택한 대화 로드
            conversation = st.session_state.conversations[conversation_id]
            st.session_state.current_conversation_id = conversation_id
            st.session_state.messages = conversation['messages'].copy()
            st.session_state.user_id = conversation.get('user_id', st.session_state.user_id)
            
            # 대화 목록에서 맨 위로 이동 (최근 접근한 대화)
            if conversation_id in st.session_state.conversation_list:
                st.session_state.conversation_list.remove(conversation_id)
            st.session_state.conversation_list.insert(0, conversation_id)
            
            st.toast(f"📂 '{conversation['title']}'를 불러왔습니다!")
            return True
        return False
    
    def delete_conversation(self, conversation_id):
        """대화 삭제"""
        if conversation_id in st.session_state.conversations:
            title = st.session_state.conversations[conversation_id]['title']
            del st.session_state.conversations[conversation_id]
            
            if conversation_id in st.session_state.conversation_list:
                st.session_state.conversation_list.remove(conversation_id)
            
            # 삭제된 대화가 현재 대화라면 새 대화 시작
            if st.session_state.current_conversation_id == conversation_id:
                if st.session_state.conversation_list:
                    # 다른 대화가 있으면 가장 최근 대화 로드
                    self.load_conversation(st.session_state.conversation_list[0])
                else:
                    # 모든 대화가 삭제되면 새 대화 시작
                    self.create_new_conversation()
            
            st.toast(f"🗑️ '{title}'가 삭제되었습니다!")
            return True
        return False
    
    def get_conversation_list(self):
        """대화 목록 반환 (최신순)"""
        conversations = []
        for conv_id in st.session_state.conversation_list:
            if conv_id in st.session_state.conversations:
                conv = st.session_state.conversations[conv_id]
                conversations.append({
                    'id': conv_id,
                    'title': conv['title'],
                    'created_at': conv['created_at'],
                    'updated_at': conv['updated_at'],
                    'message_count': len(conv['messages']),
                    'is_current': conv_id == st.session_state.current_conversation_id,
                    'starred': conv.get('starred', False)
                })
        return conversations
    
    def ensure_current_conversation(self):
        """현재 대화가 없으면 새로 생성"""
        if not st.session_state.current_conversation_id:
            self.create_new_conversation()

# 전역 대화 관리자 인스턴스
@st.cache_resource
def get_conversation_manager():
    return ConversationManager()

# 템플릿 기반 대화 생성
def create_template_based_conversation(template_key):
    """템플릿 기반 새 대화 생성"""
    conv_manager = get_conversation_manager()
    
    if template_key in CONVERSATION_TEMPLATES:
        template = CONVERSATION_TEMPLATES[template_key]
        
        # 템플릿 제목으로 새 대화 생성
        conversation_id = conv_manager.create_new_conversation(template['title'])
        
        # 초기 메시지 추가
        add_message_with_timestamp("assistant", template['initial_message'])
        
        # 제안 프롬프트를 세션 상태에 저장 (UI에서 표시용)
        st.session_state['suggested_prompts'] = template['suggested_prompts']
        
        st.toast(f"✨ {template['title']} 대화가 시작되었습니다!")
        return True
    
    return False

# ChatGPT 스타일 좌측 사이드바
def create_chatgpt_style_sidebar():
    """ChatGPT 스타일 사이드바"""
    conv_manager = get_conversation_manager()
    conv_manager.init_conversation_state()
    
    st.markdown('''
    <div class="left-sidebar">
        <div class="sidebar-section">
            <div class="section-title">💬 대화</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # 새 대화 버튼 (ChatGPT 스타일)
    if st.button("➕ 새 대화", 
                 help="새로운 대화를 시작합니다 (현재 대화는 자동 저장)", 
                 use_container_width=True, 
                 type="primary",
                 key="new_chat_main"):
        conv_manager.create_new_conversation()
        st.rerun()
    
    # 검색 및 필터 섹션
    with st.expander("🔍 검색 및 필터", expanded=False):
        # 검색바
        search_query = st.text_input(
            "🔍 대화 검색",
            placeholder="제목이나 내용으로 검색...",
            key="conversation_search"
        )
        
        # 필터 옵션
        col1, col2 = st.columns(2)
        with col1:
            filter_option = st.selectbox(
                "📂 필터",
                ["all", "starred", "today", "this_week"],
                format_func=lambda x: {
                    "all": "전체",
                    "starred": "⭐ 즐겨찾기", 
                    "today": "📅 오늘",
                    "this_week": "📆 이번 주"
                }[x],
                key="conversation_filter"
            )
        
        with col2:
            sort_option = st.selectbox(
                "🔄 정렬",
                ["recent", "oldest", "title"],
                format_func=lambda x: {
                    "recent": "최신순",
                    "oldest": "오래된순", 
                    "title": "제목순"
                }[x],
                key="conversation_sort"
            )
    
    # 대화 목록 가져오기 및 필터링
    conversations = conv_manager.get_conversation_list()
    
    # 검색 적용
    if search_query:
        conversations = search_conversations(search_query, conversations)
        if conversations:
            st.success(f"🔍 {len(conversations)}개 대화를 찾았습니다")
        else:
            st.warning("🔍 검색 결과가 없습니다")
    
    # 필터 적용
    conversations = filter_conversations(conversations, filter_option)
    
    # 정렬 적용
    if sort_option == "recent":
        conversations.sort(key=lambda x: x['updated_at'], reverse=True)
    elif sort_option == "oldest":
        conversations.sort(key=lambda x: x['updated_at'])
    elif sort_option == "title":
        conversations.sort(key=lambda x: x['title'].lower())
    
    st.markdown("---")
    
    # 대화 목록 렌더링
    if conversations:
        render_conversation_list(conversations, conv_manager)
    else:
        if search_query or filter_option != "all":
            st.info("조건에 맞는 대화가 없습니다.")
        else:
            st.info("아직 저장된 대화가 없습니다.\n새 대화를 시작해보세요!")
    
    # 설정 섹션
    st.markdown("---")
    st.markdown('<div class="section-title">⚙️ 설정</div>', unsafe_allow_html=True)
    
    # API 키 입력
    api_key = st.text_input(
        "🔑 OpenAI API Key", 
        type="password", 
        value=os.getenv("OPENAI_API_KEY", ""),
        key="api_key_sidebar"
    )
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    
    # 모델 선택
    model_options = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
    selected_model = st.selectbox(
        "🤖 AI 모델",
        model_options,
        index=0,
        key="model_selector"
    )
    st.session_state.selected_model = selected_model

def search_conversations(query, conversations):
    """대화 검색 기능"""
    if not query.strip():
        return conversations
    
    query = query.lower().strip()
    search_results = []
    
    for conv in conversations:
        # 제목에서 검색
        title_match = query in conv['title'].lower()
        
        # 메시지 내용에서 검색
        content_match = False
        if conv['id'] in st.session_state.conversations:
            full_conv = st.session_state.conversations[conv['id']]
            for message in full_conv['messages']:
                if query in message['content'].lower():
                    content_match = True
                    break
        
        if title_match or content_match:
            search_results.append(conv)
    
    return search_results

def filter_conversations(conversations, filter_type="all"):
    """대화 필터링"""
    if filter_type == "all":
        return conversations
    elif filter_type == "starred":
        return [conv for conv in conversations if conv.get('starred', False)]
    elif filter_type == "today":
        today = datetime.now().date()
        return [conv for conv in conversations if conv['updated_at'].date() == today]
    elif filter_type == "this_week":
        week_ago = (datetime.now() - timedelta(days=7)).date()
        return [conv for conv in conversations if conv['updated_at'].date() >= week_ago]
    else:
        return conversations

def render_conversation_list(conversations, conv_manager):
    """대화 목록 렌더링 (시간별 그룹화)"""
    # 오늘, 어제, 이번 주, 이전으로 그룹화
    today_convs = []
    yesterday_convs = []
    this_week_convs = []
    older_convs = []
    
    today = datetime.now().date()
    yesterday = (datetime.now() - timedelta(days=1)).date()
    week_ago = (datetime.now() - timedelta(days=7)).date()
    
    for conv in conversations:
        conv_date = conv['updated_at'].date()
        if conv_date == today:
            today_convs.append(conv)
        elif conv_date == yesterday:
            yesterday_convs.append(conv)
        elif conv_date >= week_ago:
            this_week_convs.append(conv)
        else:
            older_convs.append(conv)
    
    # 그룹별 렌더링
    if today_convs:
        st.markdown("**📅 오늘**")
        for conv in today_convs:
            render_conversation_item(conv, conv_manager)
    
    if yesterday_convs:
        st.markdown("**📅 어제**")
        for conv in yesterday_convs:
            render_conversation_item(conv, conv_manager)
    
    if this_week_convs:
        st.markdown("**📆 이번 주**")
        for conv in this_week_convs:
            render_conversation_item(conv, conv_manager)
    
    if older_convs:
        with st.expander("📚 이전 대화", expanded=False):
            for conv in older_convs:
                render_conversation_item(conv, conv_manager)

def render_conversation_item(conv, conv_manager):
    """개별 대화 아이템 렌더링"""
    # 현재 대화 및 즐겨찾기 표시
    if conv['is_current']:
        button_style = "🟢 "
    elif conv.get('starred', False):
        button_style = "⭐ "
    else:
        button_style = "💬 "
    
    col1, col2, col3 = st.columns([3, 1, 0.5])
    
    with col1:
        if st.button(
            f"{button_style}{conv['title'][:30]}...",
            key=f"load_conv_{conv['id']}",
            help=f"메시지: {conv['message_count']}개 | 업데이트: {conv['updated_at'].strftime('%H:%M')}",
            use_container_width=True,
            disabled=conv['is_current']
        ):
            conv_manager.load_conversation(conv['id'])
            st.rerun()
    
    with col2:
        # 즐겨찾기 토글
        is_starred = conv.get('starred', False)
        if st.button(
            "⭐" if is_starred else "☆",
            key=f"star_{conv['id']}",
            help="즐겨찾기",
            use_container_width=True
        ):
            st.session_state.conversations[conv['id']]['starred'] = not is_starred
            st.rerun()
    
    with col3:
        # 삭제 버튼
        if st.button(
            "🗑️",
            key=f"delete_conv_{conv['id']}",
            help="삭제",
            use_container_width=True
        ):
            confirm_key = f"confirm_delete_{conv['id']}"
            if st.session_state.get(confirm_key, False):
                conv_manager.delete_conversation(conv['id'])
                if confirm_key in st.session_state:
                    del st.session_state[confirm_key]
                st.rerun()
            else:
                st.session_state[confirm_key] = True
                st.toast("⚠️ 한 번 더 클릭하면 삭제됩니다!")

# 중앙 채팅 영역 생성
def create_main_chat_area():
    st.markdown('''
    <div class="main-chat-area">
        <div class="chat-header">
            🧠 AI 메모리 어시스턴트
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # 채팅 메시지 영역
    chat_container = st.container()
    with chat_container:
        # 대화 내역 표시
        render_messages()
    
    # 채팅 입력 영역
    st.markdown('<div class="chat-input-area">', unsafe_allow_html=True)
    
    # 에이전트 설정 확인
    if setup_agent():
        user_input, uploaded_file = create_enhanced_chat_input()
        
        if user_input:
            # 사용자 메시지 추가
            if uploaded_file:
                add_message_with_timestamp("user", f"{user_input}\n📎 첨부파일: {uploaded_file.name}")
            else:
                add_message_with_timestamp("user", user_input)
            
            # AI 응답 생성
            with st.spinner("🤖 응답 생성 중..."):
                try:
                    response = st.session_state.agent.process_message(user_input, st.session_state.user_id)
                    add_message_with_timestamp("assistant", response)
                except Exception as e:
                    add_message_with_timestamp("assistant", f"❌ 오류: {str(e)}")
            
            st.rerun()
    else:
        st.error("❌ 에이전트 설정 실패")
    
    st.markdown('</div>', unsafe_allow_html=True)

# 향상된 채팅 입력
def create_enhanced_chat_input():
    """제안 프롬프트가 포함된 채팅 입력"""
    
    # 제안 프롬프트 표시
    if 'suggested_prompts' in st.session_state and st.session_state.suggested_prompts:
        st.markdown("**💡 제안 프롬프트:**")
        
        # 2x2 그리드로 제안 프롬프트 표시
        cols = st.columns(2)
        for i, prompt in enumerate(st.session_state.suggested_prompts[:4]):
            with cols[i % 2]:
                if st.button(
                    f"💬 {prompt}",
                    key=f"suggested_{i}",
                    help=f"'{prompt}' 메시지 전송",
                    use_container_width=True
                ):
                    # 제안 프롬프트 클릭 시 메시지로 전송
                    add_message_with_timestamp("user", prompt)
                    
                    # AI 응답 생성
                    with st.spinner("🤖 응답 생성 중..."):
                        try:
                            response = st.session_state.agent.process_message(prompt, st.session_state.user_id)
                            add_message_with_timestamp("assistant", response)
                            
                            # 제안 프롬프트 사용 후 제거
                            if 'suggested_prompts' in st.session_state:
                                del st.session_state.suggested_prompts
                                
                        except Exception as e:
                            add_message_with_timestamp("assistant", f"❌ 오류: {str(e)}")
                    
                    st.rerun()
        
        # 제안 프롬프트 닫기 버튼
        if st.button("❌ 제안 닫기", key="close_suggestions"):
            if 'suggested_prompts' in st.session_state:
                del st.session_state.suggested_prompts
            st.rerun()
        
        st.markdown("---")
    
    # 템플릿 빠른 시작
    if len(st.session_state.messages) == 0:
        with st.expander("🚀 템플릿으로 빠른 시작", expanded=True):
            st.markdown("**어떤 종류의 대화를 시작하시겠어요?**")
            
            # 템플릿 버튼들 (2x2 그리드)
            template_keys = list(CONVERSATION_TEMPLATES.keys())
            
            for i in range(0, len(template_keys), 2):
                cols = st.columns(2)
                for j, template_key in enumerate(template_keys[i:i+2]):
                    template = CONVERSATION_TEMPLATES[template_key]
                    with cols[j]:
                        if st.button(
                            template['title'],
                            key=f"template_{template_key}",
                            help=template['description'],
                            use_container_width=True
                        ):
                            create_template_based_conversation(template_key)
                            st.rerun()
    
    # 기본 채팅 입력
    tab1, tab2 = st.tabs(["💬 텍스트", "📎 파일"])
    
    with tab1:
        user_input = st.chat_input("메시지를 입력하세요... (도움말: /help)")
        
        # 특수 명령어 처리
        if user_input:
            command = user_input.strip().lower()
            
            if command == '/new':
                conv_manager = get_conversation_manager()
                conv_manager.create_new_conversation()
                return None, None
            elif command.startswith('/template'):
                parts = command.split()
                if len(parts) == 2 and parts[1] in CONVERSATION_TEMPLATES:
                    create_template_based_conversation(parts[1])
                    return None, None
                else:
                    template_list = "\n".join([f"- {key}: {template['title']}" 
                                             for key, template in CONVERSATION_TEMPLATES.items()])
                    help_message = f"""
🎯 **사용 가능한 템플릿:**

{template_list}

**사용법:** `/template [템플릿명]`
**예시:** `/template coding` 또는 `/template writing`
                    """
                    add_message_with_timestamp("assistant", help_message)
                    st.rerun()
                    return None, None
            elif command == '/help':
                help_message = """
🆘 **도움말**

**💬 새 대화 시작 방법:**
1. 좌측 사이드바의 `➕ 새 대화` 버튼
2. 특수 명령어 `/new` 입력

**⚡ 특수 명령어:**
- `/new` - 새 대화 시작 (현재 대화 자동 저장)
- `/template [이름]` - 템플릿 기반 대화 시작
- `/help` - 이 도움말

**🎯 템플릿:**
- `coding` - 프로그래밍 도움
- `writing` - 글쓰기 도움  
- `learning` - 학습 도우미
- `brainstorm` - 아이디어 브레인스토밍
                """
                add_message_with_timestamp("assistant", help_message)
                st.rerun()
                return None, None
        
        return user_input, None
    
    with tab2:
        uploaded_file = st.file_uploader(
            "파일을 업로드하세요",
            type=['txt', 'md', 'pdf', 'docx', 'jpg', 'jpeg', 'png'],
            help="텍스트 파일, 이미지, 문서를 업로드할 수 있습니다."
        )
        
        if uploaded_file:
            file_content = ""
            file_type = uploaded_file.type
            
            if file_type.startswith('text/'):
                file_content = str(uploaded_file.read(), "utf-8")
            elif file_type.startswith('image/'):
                st.image(uploaded_file, caption="업로드된 이미지", use_container_width=True)
                file_content = f"[이미지 파일: {uploaded_file.name}]"
            else:
                file_content = f"[파일: {uploaded_file.name} ({file_type})]"
            
            process_file = st.button("📄 파일 처리", use_container_width=True)
            if process_file:
                return f"파일 내용 분석 요청: {uploaded_file.name}\n\n{file_content}", uploaded_file
        
        return None, None

# 우측 패널 생성
def create_right_panel():
    """향상된 우측 패널"""
    
    # 현재 대화 정보
    with st.container():
        st.markdown('<div class="panel-section">', unsafe_allow_html=True)
        st.markdown('<div class="panel-header">ℹ️ 현재 대화</div>', unsafe_allow_html=True)
        
        if st.session_state.current_conversation_id:
            current_conv = st.session_state.conversations[st.session_state.current_conversation_id]
            
            st.markdown(f"**제목:** {current_conv['title']}")
            st.markdown(f"**메시지:** {len(current_conv['messages'])}개")
            st.markdown(f"**모델:** {current_conv.get('model', 'unknown')}")
            st.markdown(f"**생성:** {current_conv['created_at'].strftime('%Y-%m-%d %H:%M')}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 메모리 상태
    with st.container():
        st.markdown('<div class="panel-section">', unsafe_allow_html=True)
        st.markdown('<div class="panel-header">🧠 메모리 상태</div>', unsafe_allow_html=True)
        
        if st.session_state.agent:
            memories = st.session_state.agent.memory_tools.get_all_memories(st.session_state.user_id)
            
            if memories:
                st.metric("저장된 기억", f"{len(memories)}개")
                
                # 최근 메모리 표시
                st.markdown("**최근 기억:**")
                for i, memory in enumerate(memories[-3:], 1):
                    st.markdown(f'''
                    <div class="memory-box">
                        💭 {memory[:100]}...
                    </div>
                    ''', unsafe_allow_html=True)
            else:
                st.info("💭 저장된 기억이 없습니다.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 세션 통계
    with st.container():
        st.markdown('<div class="panel-section">', unsafe_allow_html=True)
        st.markdown('<div class="panel-header">📊 세션 통계</div>', unsafe_allow_html=True)
        
        total_msgs = len(st.session_state.messages)
        user_msgs = len([m for m in st.session_state.messages if m['role'] == 'user'])
        ai_msgs = total_msgs - user_msgs
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("사용자", user_msgs)
            st.metric("전체 대화", len(st.session_state.get('conversation_list', [])))
        with col2:
            st.metric("AI", ai_msgs)
            starred_count = len([conv_id for conv_id in st.session_state.get('conversation_list', [])
                               if st.session_state.conversations.get(conv_id, {}).get('starred', False)])
            st.metric("⭐ 즐겨찾기", starred_count)
        
        st.markdown('</div>', unsafe_allow_html=True)

# 메시지 렌더링 함수 (기존과 동일)
def render_messages():
    for i, msg in enumerate(st.session_state.messages):
        timestamp = msg.get('timestamp', datetime.now().strftime('%H:%M'))
        
        if msg['role'] == 'user':
            st.markdown(f'''
            <div class="message-container">
                <div class="user-message-container">
                    <div>
                        <div class="user-msg">{msg["content"]}</div>
                        <div class="message-timestamp">{timestamp}</div>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
            <div class="message-container">
                <div class="assistant-message-container">
                    <div>
                        <div class="assistant-msg">{msg["content"]}</div>
                        <div class="message-timestamp">{timestamp}</div>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

# 세션 상태 초기화
def init_session_state():
    """세션 상태 초기화 (대화 관리 시스템 포함)"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = "user_001"
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = "gpt-4o-mini"
    if 'current_model' not in st.session_state:
        st.session_state.current_model = None
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    
    # 대화 관리자 초기화
    conv_manager = get_conversation_manager()
    conv_manager.init_conversation_state()
    
    # 현재 대화가 없으면 새로 생성
    conv_manager.ensure_current_conversation()
    
    # messages는 현재 대화의 메시지와 동기화
    if st.session_state.current_conversation_id:
        current_conv = st.session_state.conversations.get(st.session_state.current_conversation_id)
        if current_conv and 'messages' not in st.session_state:
            st.session_state.messages = current_conv['messages'].copy()
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []

# 에이전트 설정
def setup_agent():
    # 모델이 변경되었거나 에이전트가 없는 경우 재생성
    if (st.session_state.agent is None or 
        getattr(st.session_state, 'current_model', None) != st.session_state.selected_model):
        
        try:
            # mem0 설정
            config = {
                "llm": {
                    "provider": "openai",
                    "config": {
                        "model": st.session_state.selected_model,
                        "temperature": 0.1,
                        "api_key": os.getenv("OPENAI_API_KEY")
                    }
                } if os.getenv("OPENAI_API_KEY") else None
            }
            
            memory = Memory.from_config(config) if config["llm"] else Memory()
            web_search = SimpleWebSearch()
            agent = SimpleAgent(memory, web_search)
            
            st.session_state.agent = agent
            st.session_state.current_model = st.session_state.selected_model
            return True
        except Exception as e:
            st.error(f"에이전트 설정 실패: {str(e)}")
            return False
    return True

# 메시지 추가 함수 (자동 저장 포함)
def add_message_with_timestamp(role: str, content: str):
    """메시지 추가 및 자동 저장"""
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().strftime('%H:%M')
    }
    st.session_state.messages.append(message)
    
    # 현재 대화에 자동 저장
    conv_manager = get_conversation_manager()
    conv_manager.save_current_conversation()

# 메인 앱
def main():
    init_session_state()
    
    # 페이지 설정
    st.markdown('<div class="main-header">🧠 AI 메모리 어시스턴트</div>', unsafe_allow_html=True)
    
    # 사용법 가이드
    with st.expander("📖 사용법 가이드", expanded=False):
        st.markdown("""
        ### 🚀 ChatGPT 스타일 대화 관리
        - **➕ 새 대화**: 현재 대화를 자동 저장하고 새 대화 시작
        - **💬 대화 목록**: 모든 과거 대화에 언제든 접근 가능
        - **🟢 현재 대화**: 초록색 점으로 현재 활성 대화 표시
        - **⭐ 즐겨찾기**: 중요한 대화를 즐겨찾기로 표시
        - **🔍 검색**: 제목이나 내용으로 대화 검색
        - **🎯 템플릿**: 목적에 맞는 대화 템플릿으로 빠른 시작
        
        ### ⌨️ 단축키
        - `/new` - 새 대화 시작
        - `/template [이름]` - 템플릿 기반 대화 시작
        - `/help` - 도움말 표시
        """)
    
    # 3열 레이아웃
    col1, col2, col3 = st.columns([1, 2, 1], gap="medium")
    
    # ChatGPT 스타일 좌측 사이드바
    with col1:
        create_chatgpt_style_sidebar()
    
    # 중앙 메인 채팅 영역
    with col2:
        create_main_chat_area()
    
    # 우측 패널
    with col3:
        create_right_panel()

if __name__ == "__main__":
    main()