import openai
import os
import re
import csv
# from llama_index import VectorStoreIndex, SimpleDirectoryReader
# from llama_index import Prompt
from llama_index.core import StorageContext, load_index_from_storage
# from langchain.prompts.chat import (
#     ChatPromptTemplate,
#     HumanMessagePromptTemplate,
#     SystemMessagePromptTemplate,
# )
from Hopfield import retrieval_info

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, ChatPromptTemplate
from llama_index.core.embeddings import resolve_embed_model
from llama_index.llms.ollama import Ollama
# from llama_index.core import Prompt
from llama_index.core import PromptTemplate
import llama_index.core

llama_index.core.set_global_handler("simple")
documents = SimpleDirectoryReader("./dataset_folder/health_report_{0}/").load_data()

# bge embedding model
Settings.embed_model = resolve_embed_model("local:BAAI/bge-small-en-v1.5")

# ollama
Settings.llm = Ollama(model="mistral", request_timeout=30.0)


def answer_from_gpt(ques, context, work):

    storage_context = StorageContext.from_defaults(persist_dir='./storage')
    index = load_index_from_storage(storage_context, index_id="index_health")
    list_score = []

    t = 0
 
    for i in ques:
        # print(f"##### Question I is: {i} ######")
        my_context = context + work[t]
        # print(f"############## my_context is:\n {my_context} \n#####################")
        QA_PROMPT = get_systemprompt_template(my_context)
        # print(f"############## QA_PROMPT is:\n {QA_PROMPT} \n#####################")
        query_engine = index.as_query_engine(text_qa_template=QA_PROMPT, streaming=True, verbose=True)
        response = query_engine.query(i)
        # response.print_response_stream()
        # print(f"############## response is:\n {response} \n#####################")
        stt = str(response)
        score = extract_score(stt)
        list_score.append(score)
        print(score)
        t = t + 1

    return list_score



# def get_systemprompt_template(exist_context):

#     chat_text_qa_msgs = [
#         SystemMessagePromptTemplate.from_template(
#             exist_context
#         ),
#         HumanMessagePromptTemplate.from_template(
#         "Give the answer in jason format with only one number between 0 and 1 that is: 'score'\n"
#         "The score number must be an decimals\n"
#         "This is the rule of answer: 0-0.2 is mild or none, 0.3-0.6 is moderate, and above 0.7 is severe.\n"
#         "This is a patient‘s medical record. Context information in below\n"
#         "---------------------\n"
#         "{context_str}"
#         "Given the context information, you are a helpful health consultant "
#         "answer the question: {query_str}\n"
#     )
#     ]
#     chat_text_qa_msgs_lc = ChatPromptTemplate.from_messages(chat_text_qa_msgs)
#     print(f"chat_text_qa_msgs_lc is: {chat_text_qa_msgs_lc}")
#     # text_qa_template = Prompt.from_langchain_prompt(chat_text_qa_msgs_lc) # for llama-index==0.7.8
#     # text_qa_template = PromptTemplate.format_messages(chat_text_qa_msgs_lc)
#     # PromptTemplate.
#     text_qa_template = chat_text_qa_msgs_lc

#     return text_qa_template

def get_systemprompt_template(exist_context):

    chat_text_qa_msgs = [
        ("system",
            exist_context
        ),
        ("user",
        "Give the answer in json format with only one number between 0 and 1 that is: 'score'\n"
        "The score number must be an decimals\n"
        "This is the rule of answer: 0-0.2 is mild or none, 0.3-0.6 is moderate, and above 0.7 is severe.\n"
        "This is a patient‘s medical record. Context information in below\n"
        "---------------------\n"
        "{context_str}"
        "Given the context information, you are a helpful health consultant "
        "answer the question: {query_str}\n"
    )
    ]
    chat_text_qa_msgs_lc = ChatPromptTemplate.from_messages(chat_text_qa_msgs)
    # print(f"chat_text_qa_msgs_lc is: {chat_text_qa_msgs_lc}")



    return chat_text_qa_msgs_lc

def extract_score(string):
    numbers = re.findall(r'\d+\.\d+|\d+', string)
    if numbers:
        for i in numbers:
            return float(i)
    else:
        return 0.0


def generate_question(path):
    my_feature_list = []
    related_work = []
    with open(path, 'r') as file:
        for line in file:
            line = line.strip()
            my_feature_list.append(line)
    question = []
    for i in my_feature_list:
        # print(f"Does the person described in the case have {i} symptoms? Do you think it is serious?")
        sentence = f"Does the person described in the case have {i} symptoms? Do you think it is serious?"
        list_sentence = [sentence]
        retrieval = retrieval_info(list_sentence, './', 1)
        question.append(sentence)
        related_work.append(retrieval[0])
        # print(retrieval[0])

    return question, related_work, my_feature_list


def count_subfolders(folder_path):
    subfolder_count = 0
    subfolder_paths = []

    for root, dirs, files in os.walk(folder_path):
        if root != folder_path:
            subfolder_count += 1

    basepath = './dataset_folder/health_report_'
    for i in range(subfolder_count):
        path_rr = basepath+str({i})
        subfolder_paths.append(path_rr)

    return subfolder_count, subfolder_paths




def load_doc(folder_path,question,work):
    # print(f"Length of work is: {len(work)}")
    count, dict = count_subfolders(folder_path)
    list_k = []
    context = 'Here is some additional professional health knowledge that can help you better analyze the report. '
    for i in range(0,1): # just check 1 for now
        documents = SimpleDirectoryReader(dict[i]).load_data()
        print(f"Length of documents is: {len(documents)} and creating index now inside load_doc")
        index = VectorStoreIndex.from_documents(documents)
        index.set_index_id("index_health")
        index.storage_context.persist('./storage')
        content = context
        list = answer_from_gpt(question, content, work)
        list_k.append(list)
    return list_k



if __name__ == '__main__':


    # openai.api_key = os.environ.get("OPENAI_API_KEY")
    # path = '/Users/jmy/Desktop/ai_for_health_final/label and feature/input_feature.txt'
    path = './label_and_feature_input_feature_english_short.txt'
    question, related_work, features_list = generate_question(path)
    # print(f"Question is: {question}")
    folder_path = './dataset_folder'
    list = load_doc(folder_path, question, related_work)

    # with open('training/train.txt', 'w') as file:
    #      for item in list:
    #          file.write(''.join(str(item)) + '\n\n')

    # with open('training/combined7.csv', 'w', newline='') as file:
    #     writer = csv.writer(file)
    #     # 首先写入特征行
    #     writer.writerow(features_list)
    #     # 然后写入矩阵的每一行
    #     for row in list:
    #         writer.writerow(row)

    # print("CSV file has been created successfully.")
