import requests
import streamlit as st
import re
import os
from dotenv import load_dotenv
from Bio.Seq import Seq
from Bio.Data.CodonTable import TranslationError
import os
import sqlite3

# DB 파일 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "genelog.db")

load_dotenv()


def AI_teacher(gene_data):
    N_api_key = os.getenv("AI_request_N_API")
    invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
    stream = False

    headers = {
        "Authorization": f"Bearer {N_api_key}",
        "Accept": "text/event-stream" if stream else "application/json",
    }

    payload = {
    "model": "nvidia/nemotron-3.5-bolt-e4b",
    "max_tokens": 1024,
    "stream": stream,
    "temperature": 0.3,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "seed": 0,
    "messages": [
    {"role": "system",
     "content": "너는 고등학생에게 유전공학을 가르치는 선생님이야. 한국어로 쉽게 설명해. 확실하지 않은 내용은 추측이라고 밝혀."},
    {"role": "user",
     "content": f"다음 단백질이 무엇이고 어떤 역할을 하는지 설명해줘:\n{gene_data}"}
    ]
    }
    try:
        response = requests.post(invoke_url, headers=headers, json=payload, stream=stream, timeout=60)
        if response.status_code != 200:            # 키 문제, 호출 제한 등
            st.error(f"AI 요청 실패 (상태 코드: {response.status_code})")
            return None
        answer = response.json()["choices"][0]["message"]["content"]
        return answer
    except requests.exceptions.Timeout:
        st.error("AI 서버가 바빠요. 잠시 후 다시 시도해 주세요.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"AI 요청 중 오류 발생: {e}")
        return None

# 입력 오류 교정 함수
def correction(x):
    result = x.replace('\n', "")
    result = "".join(result.split())
    result = re.sub(r"[0-9]", "", result)
    if not result.isalpha():
        return ""
    result = result.upper()
    return result

# 유전자 교차 검증
def check(genes):
    comparison = set(['A', 'T', 'G', 'C', 'U'])
    checker = set(list(genes))
    cheking = correction(x=genes)
    if checker | comparison == comparison and not(cheking == ""):
        return cheking
    return "get out!"

def get_gene_data(gene_c):
    try:
        url = "https://rest.uniprot.org/uniparc/sequence"
        params = params = {
                "sequence": str(gene_c),   
                 "format": "json",
        }       
        response = requests.get(url,params=params, timeout=10)

        if response.status_code != 200:
            print(f"요청 실패 (상태 코드: {response.status_code})")
            return
        data = response.json()
        return data

    except requests.exceptions.Timeout as e:
        print(f"서버 응답시간 초과: {e}")
    except requests.exceptions.RequestException as e:
        print(f"요청 중 오류 발생: {e}")
    except Exception as e:
        print(f"오류 발생: {e}")
def save_db(save_data_s):
    return 0
def check_db(save_data_s):
    return 0

st.title("Gene Teacher")

st.header("질문창")

quest = st.text_input("어떤 염기서열을 알고싶으신가요")

if st.button("확인"):
    v = check(genes=quest)
    if not v == "get out!":
        try:
            res = Seq(v).translate(cds = True)
            save = get_gene_data(res)
            save_data = save["uniParcCrossReferences"][0]
            with st.spinner("AI 선생님이 설명을 준비하고 있어요..."):
                answer = AI_teacher(save_data)    # 이 줄이 끝날 때까지 동글뱅이
            st.write(answer)                      # 동글뱅이가 사라진 뒤에 답 출력
        except  TranslationError:
            st.write("OOPs! 잘못된 염기서열을 넣으셨네요 ㅋ 허접")
    else:
        st.write("잘못된 입력입니다 다시 입력해주세요")


st.divider()

