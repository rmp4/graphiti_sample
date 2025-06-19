import requests
import uuid

def create_initial_state(user_query: str):
    return {
        "user_query": user_query,
        "messages": [
            {
                "content": user_query,
                "type": "human"
            }
        ],
        "search_results": {
            "results": [],
            "total_count": 0,
            "search_time_ms": 0,
            "result_quality": 0.0,
            "metadata": {}
        },
        "current_status": "initialized",
        "should_continue": True,
        "user_intent": "",
        "intent_confidence": 0.0,
        "intent_parameters": {},
        "current_step": "start",
        "next_step": "analyze_intent",
        "error_message": None,
        "formatted_response": "",
        "response_type": "text",
        "refinement_history": [],
        "needs_refinement": False,
        "refinement_suggestions": []
    }

def run_langgraph_query(base_url: str, thread_id: str, user_query: str):
    url = f"{base_url}/threads/{thread_id}/runs/stream"
    assistant_id = "tender_search"  # 根據你的 langgraph.json 設定調整

    payload = {
        "assistant_id": assistant_id,
        "input": create_initial_state(user_query),
        "config": {
            "configurable": {}
        },
        "stream_mode": ["values"]
    }

    response = requests.post(url, json=payload, stream=True)
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return

    print("Streaming response:")
    for line in response.iter_lines():
        if line:
            print(line.decode("utf-8"))

if __name__ == "__main__":
    BASE_URL = "http://127.0.0.1:8123"
    THREAD_ID = "a976584f-07bb-4016-b594-42bfef32e035"  # 使用你提供的有效 thread_id
    USER_QUERY = "有哪些大數據的專案"

    run_langgraph_query(BASE_URL, THREAD_ID, USER_QUERY)
