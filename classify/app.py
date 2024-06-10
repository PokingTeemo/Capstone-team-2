import os
from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

def scrape_scholarships():
    service = Service(executable_path=ChromeDriverManager().install())

    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    
    driver = webdriver.Chrome(service=service, options=chrome_options)

    main_url = 'https://www.kosaf.go.kr/ko/main.do?currentMain=1'
    driver.get(main_url)

    wait = WebDriverWait(driver, 10)

    try:
        scholarship_link1 = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="top_submenu_a03"]')))
        driver.execute_script("arguments[0].click();", scholarship_link1)
    except Exception as e:
        print(f"An error occurred while clicking the scholarship link: {e}")
        driver.quit()
        return []

    try:
        scholarship_link2 = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="container"]/div/div/div/dl[3]/dd/ul/li[1]/a')))
        driver.execute_script("arguments[0].click();", scholarship_link2)
    except Exception as e:
        print(f"An error occurred while clicking the scholarship link: {e}")
        driver.quit()
        return []

    driver.find_element(By.XPATH, '//*[@id="tableList04"]/tbody/tr[5]/td/ul/li').click()
    driver.find_element(By.XPATH, '//*[@id="sorting"]/option[2]').click()
    driver.find_element(By.XPATH, '//*[@id="tableList04"]/tbody/tr[6]/td/span/a').click()

    scholarship_details = []

    for p in range(4):
        for i in range(10):
            try:
                detail_xpath = '//*[@id="tableList02"]/tbody/tr[%d]/td[8]/span[1]/a' % (i+1)
                driver.find_element(By.XPATH, detail_xpath).click()

                scholarship_name = driver.find_element(By.CLASS_NAME, 'bg_title').text
                scholarship_target = driver.find_element(By.XPATH, '//*[@id="content"]/div/div[1]/div/div/table/tbody/tr[9]/td[2]').text
                scholarship_amount = driver.find_element(By.XPATH, '//*[@id="content"]/div/div[1]/div/div/table/tbody/tr[8]/td[2]').text
                scholarship_due = driver.find_element(By.XPATH, '//*[@id="content"]/div/div[1]/div/div/table/tbody/tr[10]/td[4]').text
                scholarship_url_element = driver.find_elements(By.XPATH, '//*[@id="content"]/div/div[1]/div/div/table/tbody/tr[15]/td[4]/a')
                if scholarship_url_element:
                    scholarship_url_href = scholarship_url_element[0].get_attribute('href')
                else:
                    scholarship_url_href = "N/A"

                scholarship_details.append({
                    'name': scholarship_name,
                    'amount': scholarship_amount,
                    'target': scholarship_target,
                    'due': scholarship_due,
                    'url': scholarship_url_href
                })
                
                driver.back()
            
            except Exception as e:
                print(f"An error occurred: {e}")
                break
        
        try:
            page_xpath = '//*[@id="paging"]/div/a[%d]' % (p+4)
            driver.find_element(By.XPATH, page_xpath).click()
            
        except Exception as e:
            print(f"An error occurred: {e}")
            break

    driver.quit()
    return scholarship_details

@app.route('/scrape_scholarships', methods=['GET'])
def get_scholarships():
    try:
        scholarships = scrape_scholarships()
        return jsonify(scholarships)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def scholarship_recommandation(scholarship_details, user_details,today):
    load_dotenv()

    # Initialize OpenAI Client
    client = OpenAI(api_key='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')

    ###############기존 assistant 사용하기###############
    assistant = client.beta.assistants.retrieve(
        assistant_id="asst_8m0KncQCp9RFXsrOtlmg1aat"
    )

    # #######################쓰레드 생성#######################
    thread = client.beta.threads.create()
    
    #thread = client.beta.threads.retrieve("thread_nfRDm9bQxMD22jezibDIQoYD")


    #######################메세지 생성#######################
    input_tuning = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="사용자 정보: " + user_details
    )
    input_tuning1 = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="오늘 날짜: " + today
    )
    input = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="장학금 정보: " + scholarship_details
    )

    ###############Run#################
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=assistant.id,
        instructions="""답변은 쓸데없는 설명 없이 해당 5개의 장학금들이 각각 몇 번째 장학금인지 숫자만 출력해. 예를 들어 1번, 10번, 11번, 30번, 39번 장학금이 추천 결과라면 "1 10 11 30 39" 를 출력해줘."""
        # tools = [{"type": "file_search"}]
    )
    
    ###############답변 출력###############
    output = list(client.beta.threads.messages.list(thread_id=thread.id))

    output_content = output[0].content[0].text
    annotations = output_content.annotations

    for index, annotation in enumerate(annotations):
        output_content.value = output_content.value.replace(annotation.text)

    # #############사용한 쓰레드 삭제: 토큰 조절용################
    # response = client.beta.threads.delete(thread.id)
    
    return output_content.value

@app.route('/scholarship', methods=['POST'])
def scholarship():
    data = request.json
    scholarship_details = data.get('scholarship_details')
    user_details = data.get('user_details')
    today = data.get('today')
    
    print(scholarship_details)
    print(user_details)
    print(today)

    if not scholarship_details or not user_details or not today:
        return jsonify({"error": "All parameters are required"}), 400
    
    result = scholarship_recommandation(str(scholarship_details), str(user_details), today)
    print(result)
    return jsonify({"result": result})
    # try:
    #     return jsonify({"result": result})
    # except Exception as e:
    #     return jsonify({"error": str(e)}),


def classify_transactions(transaction_details):
    load_dotenv()

    # Initialize OpenAI Client
    client = OpenAI(api_key='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')

    ###############기존 assistant 사용하기###############
    assistant = client.beta.assistants.retrieve(
        assistant_id="asst_nYFqYu06UjZBDJ36MbtZG4yh"
    )

    # #######################쓰레드 생성#######################
    # thread = client.beta.threads.create()
    
    thread = client.beta.threads.retrieve("thread_Z9pAbr3AmtZ3otbnSwAS819L")


    # #######################메세지 생성#######################
    # input_tuning = client.beta.threads.messages.create(
    #     thread_id=thread.id,
    #     role="user",
    #     content="'0'으로 분류되는 경우가 가능한 발생하지 않도록 업태와 가게 이름을 꼼꼼하게 읽고 판단해. 예를 들어 '기타 비알코올 음료점업' 이라는 업태는 카페를 의미하는 업태야. "
    # )

    input = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=transaction_details
    )

    ###############Run#################
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=assistant.id,
        instructions="답변은 쓸데없는 설명 없이 해당 카테고리의 숫자만 출력해. 예를 들어 카페로 분류 된 항목이 입력되었을 때의 답변은 '3' 이야. 아무 카테고리에도 속하지 않으면 '0'을 출력해.",
        tools = [{"type": "file_search"}]
    )
    
    ###############답변 출력###############
    output = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))

    output_content = output[0].content[0].text
    annotations = output_content.annotations

    for index, annotation in enumerate(annotations):
        output_content.value = output_content.value.replace(annotation.text)

    # #############사용한 쓰레드 삭제: 토큰 조절용################
    # response = client.beta.threads.delete(thread.id)
    
    return output_content.value

@app.route('/classify', methods=['POST'])
def classify():
    data = request.json
    transaction_details = data.get('transaction_details')
    if not transaction_details:
        return jsonify({"error": "transaction_details is required"}), 400
    
    try:
        result = classify_transactions(transaction_details)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)