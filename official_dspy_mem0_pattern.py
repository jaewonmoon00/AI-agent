# official_dspy_mem0_pattern.py
# DSPy 공식 사이트의 mem0 통합 패턴

import dspy
from mem0 import Memory
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class MemoryTools:
    """mem0 메모리 시스템과 상호작용하는 도구들"""
    
    def __init__(self, memory: Memory):
        self.memory = memory
    
    def store_memory(self, content: str, user_id: str = "default_user") -> str:
        """정보를 메모리에 저장"""
        try:
            self.memory.add(content, user_id=user_id)
            return f"메모리 저장됨: {content}"
        except Exception as e:
            return f"메모리 저장 오류: {str(e)}"
    
    def search_memories(self, query: str, user_id: str = "default_user", limit: int = 5) -> str:
        """관련 메모리 검색"""
        try:
            results = self.memory.search(query, user_id=user_id, limit=limit)
            if not results:
                return "관련 메모리를 찾을 수 없습니다."
            
            memory_text = "관련 메모리:\n"
            for i, result in enumerate(results["results"]):
                memory_text += f"{i+1}. {result['memory']}\n"
            return memory_text
        except Exception as e:
            return f"메모리 검색 오류: {str(e)}"
    
    def get_all_memories(self, user_id: str = "default_user") -> str:
        """사용자의 모든 메모리 가져오기"""
        try:
            results = self.memory.get_all(user_id=user_id)
            if not results:
                return "저장된 메모리가 없습니다."
            
            memory_text = "저장된 모든 메모리:\n"
            for i, result in enumerate(results["results"]):
                memory_text += f"{i+1}. {result['memory']}\n"
            return memory_text
        except Exception as e:
            return f"메모리 조회 오류: {str(e)}"

def get_current_time() -> str:
    """현재 시간 반환"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class MemoryQA(dspy.Signature):
    """
    메모리 기능을 가진 도움이 되는 어시스턴트입니다.
    사용자의 입력에 답변할 때마다 중요한 정보를 메모리에 저장하여
    나중에 활용할 수 있도록 합니다.
    """
    user_input: str = dspy.InputField()
    response: str = dspy.OutputField()

class MemoryReActAgent(dspy.Module):
    """mem0 메모리 기능이 강화된 ReAct 에이전트"""
    
    def __init__(self, memory: Memory):
        super().__init__()
        self.memory_tools = MemoryTools(memory)
        
        # ReAct에서 사용할 도구들 정의
        self.tools = [
            self.memory_tools.store_memory,
            self.memory_tools.search_memories,
            self.memory_tools.get_all_memories,
            get_current_time,
            self.set_reminder,
            self.get_preferences,
            self.update_preferences,
        ]
        
        # 도구가 포함된 ReAct 초기화
        self.react = dspy.ReAct(
            signature=MemoryQA,
            tools=self.tools,
            max_iters=6
        )
    
    def forward(self, user_input: str):
        """메모리 인식 추론으로 사용자 입력 처리"""
        return self.react(user_input=user_input)
    
    def set_reminder(self, reminder_text: str, date_time: str = None, user_id: str = "default_user") -> str:
        """사용자를 위한 알림 설정"""
        reminder = f"알림 설정 ({date_time}): {reminder_text}"
        return self.memory_tools.store_memory(
            f"REMINDER: {reminder}",
            user_id=user_id
        )
    
    def get_preferences(self, category: str = "general", user_id: str = "default_user") -> str:
        """특정 카테고리의 사용자 선호도 가져오기"""
        query = f"사용자 선호도 {category}"
        return self.memory_tools.search_memories(
            query=query,
            user_id=user_id
        )
    
    def update_preferences(self, category: str, preference: str, user_id: str = "default_user") -> str:
        """사용자 선호도 업데이트"""
        preference_text = f"{category}에 대한 사용자 선호도: {preference}"
        return self.memory_tools.store_memory(
            preference_text,
            user_id=user_id
        )

def setup_official_integration():
    """공식 패턴을 따른 설정"""
    
    # DSPy 설정
    lm = dspy.LM(model='openai/gpt-4o-mini')
    dspy.configure(lm=lm)
    
    # mem0 설정
    config = {
        "llm": {
            "provider": "openai",
            "config": {
                "model": "gpt-4o-mini",
                "temperature": 0.1
            }
        },
        "embedder": {
            "provider": "openai",
            "config": {
                "model": "text-embedding-3-small"
            }
        }
    }
    
    # 메모리 시스템 초기화
    memory = Memory.from_config(config)
    
    # 메모리 강화 에이전트 생성
    agent = MemoryReActAgent(memory)
    
    return agent

def demo_conversation():
    """공식 예제와 유사한 대화 데모"""
    
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY 환경변수를 설정해주세요.")
        return
    
    try:
        agent = setup_official_integration()
        
        print("🧠 메모리 강화 ReAct 에이전트 데모")
        print("=" * 50)
        
        conversations = [
            "안녕하세요, 저는 김철수이고 한식, 특히 비빔밥을 좋아합니다.",
            "저는 김철수입니다. 아침 7시에 운동하는 것을 선호합니다.",
            "김철수입니다. 제 음식 선호도에 대해 무엇을 기억하고 있나요?",
            "김철수입니다. 내일 장보기 알림을 설정해주세요.",
            "김철수입니다. 제 운동 선호도는 무엇인가요?",
            "김철수입니다. 주말에는 등산도 좋아합니다.",
            "김철수입니다. 지금까지 저에 대해 무엇을 알고 있나요?"
        ]
        
        for i, user_input in enumerate(conversations, 1):
            print(f"\n📝 사용자: {user_input}")
            try:
                response = agent(user_input=user_input)
                print(f"🤖 에이전트: {response.response}")
            except Exception as e:
                print(f"❌ 오류: {e}")
    
    except Exception as e:
        print(f"설정 오류: {e}")

if __name__ == "__main__":
    demo_conversation()