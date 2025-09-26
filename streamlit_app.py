import streamlit as st
import json
import random
import mimetypes
from io import BytesIO

random.seed(12)
from aws_function import(read_image)
from utilities import (load_conversation_data,
                       extract_conversations,
                       get_response,
                       first_match)
from results import (show_results)



st.set_page_config(page_title="AI Conversation Viewer",layout="wide")
voting_options = ["LLM 01", "LLM 02", "Both", "None"]

with open("question_mapped.json", "r", encoding="utf-8") as f:
    question_data = json.load(f)

with open("file_record.json", "r", encoding="utf-8") as f:
    file_record = json.load(f)

with open("pdf_record.json", "r", encoding="utf-8") as f:
    pdf_record = json.load(f)


stop_index = [2,4,7,10,12,15,17,19,22,25]
intro_index = [0,3,5,8,11,13,16,18,20,23]
index_dict = {}
for each in range(len(stop_index)):
    index_dict[stop_index[each]] = intro_index[each]

intro_dict = {0:6, 3:5, 5:0, 8:5, 11:11, 13:9, 16:0, 18:18, 20:0, 23:0}

# --- Initialize session_state ---
if "current_index" not in st.session_state:
    st.session_state.current_index = 0

if "user_data" not in st.session_state:
    st.session_state.user_data = {}


# ---- Sidebar ----
main_sidebar = st.sidebar
with main_sidebar:
    st.warning(f"***This site is not actively seeking responses. Prepared to share publicly.***")
    openai_file = st.file_uploader(
        "Upload OpenAI JSON file",
        type=['json'],
        key="openai_upload"
    )
    gemini_file = st.file_uploader(
        "Upload Gemini JSON file",
        type=['json'],
        key="gemini_upload"
    )

    if openai_file and gemini_file:
        openai_data = load_conversation_data(openai_file, history="OpenAI")
        gemini_data = load_conversation_data(gemini_file, history="Gemini")

        data = [openai_data, gemini_data]
        conversations = extract_conversations(data)

llm_titles = ["GPT", "Gemini"]
# Determine the number of conversation pairs
max_conversations = len(question_data)
# random_index = [random.randint(0, 1) for _ in range(max_conversations)]


with main_sidebar:
    slider_index = st.slider("Select section you want to see", 1, max_conversations+1) - 1 
    if st.button("Get Section", use_container_width=True):
        st.session_state.current_index = slider_index
    column_view =st.toggle("Column View", value=True)
    reveal_view =st.toggle("Reveal LLM")


if max_conversations == 0:
    st.warning("No conversations found in the uploaded files.")

# Ensure current_index is within bounds
if st.session_state.current_index >= max_conversations:
    st.session_state.current_index = max_conversations - 1
elif st.session_state.current_index < 0:
    st.session_state.current_index = 0

current_idx = st.session_state.current_index

survey, results = st.tabs(["Questionnaire", "Results"])

with survey:
    if current_idx in intro_index:
        st.header(question_data[current_idx]["data"]["topic"])
        st.subheader(question_data[current_idx]["data"]["sub_topic"])
        st.divider()

        st.markdown("**Things to evaluate** ➡️")
        markdown_list = "\n".join([f"- {item}" for item in question_data[current_idx]["data"]["evaluation"]])
        st.markdown(markdown_list)
        st.divider()

        st.subheader("Given inputs: 📥")
        chat_history_Gemini = load_conversation_data(gemini_file, history="Gemini")
        match_found = False

        row_count = 0
        column_grid = intro_dict[current_idx]
        if column_grid > 0:
            column_grid = column_grid // 2
        column_list = st.columns(2)
        
        for message in chat_history_Gemini:
            if message["role"] == "user":
                stop_key = [key for key, value in index_dict.items() if value == current_idx][0]
                stop_question = question_data[stop_key]
                start_question = question_data[stop_index[stop_index.index(stop_key) - 1]]
                text = message["parts"][0]["text"]
                if current_idx == 0:
                    start_question = "This is the RFQ of the project we will be working on."
                if first_match(text, start_question, 10):
                    match_found =True
                elif first_match(text, stop_question, 10):
                    match_found = False
                
                if match_found:
                    if len(message["parts"]) == 2:
                        try:
                            file_uri = file_record[message["parts"][1]["file_data"]["file_uri"]]
                            mime_type, _ = mimetypes.guess_type(file_uri)

                            if column_view:
                                if row_count > column_grid:
                                    column_index = 1
                                else:
                                    column_index = 0

                                with column_list[column_index]:
                                    with st.container(border=True):
                                        st.markdown(text)
                                        if mime_type == "application/pdf":
                                            file_name =file_uri.split("/")[-1]
                                            st.link_button(f"{file_name}", pdf_record[file_uri])
                                        elif (mime_type == "image/png") or (mime_type == "image/jpeg"):
                                            image_aws =  read_image(file_uri)
                                            st.image(BytesIO(image_aws))
                                    row_count += 1

                            else:
                                with st.container(border=True):
                                    st.markdown(text)
                                    if mime_type == "application/pdf":
                                        file_name =file_uri.split("/")[-1]
                                        st.link_button(f"{file_name}", pdf_record[file_uri])
                                    elif (mime_type == "image/png") or (mime_type == "image/jpeg"):
                                        image_aws =  read_image(file_uri)
                                        st.image(BytesIO(image_aws))
                        except:
                            pass


    else:
        question = question_data[current_idx]
        st.subheader(f"Q{current_idx}.{question}")
        st.markdown("---")

        if column_view:
            column_list = st.columns(2)

            count = 0
            for each in column_list:
                with each:
                    running_llm = llm_titles[count]
                    if reveal_view:
                        st.subheader(f"➡️ {running_llm} Response")
                    else:
                        st.subheader(f"➡️ LLM 0{count + 1} Response")

                    if current_idx < len(question_data):
                        response = get_response(question, running_llm)
                        st.markdown(response)
                    else:
                        st.info("No response for this question")
                    count += 1
            
        else:
            count = 0
            for each in range(2):
                running_llm = llm_titles[count]
                if reveal_view:
                    st.subheader(f"➡️ {running_llm} Response")
                else:
                    st.subheader(f"➡️ LLM 0{count + 1} Response")

                if current_idx < len(question_data):
                    response = get_response(question, running_llm)
                    st.markdown(response)
                else:
                    st.info("No response for this question")
                count += 1

    # Navigation controls (bottom right)
    st.divider()
    nav_col1, nav_col2, nav_col3 = st.columns([6, 1, 1])
    with nav_col1:
        st.markdown(f"**Page {current_idx + 1} of {max_conversations}**")
    with nav_col2:
        if st.button("⬅️ Previous", disabled=(current_idx == 0)):
            st.session_state.current_index -= 1
            st.rerun()
    with nav_col3:
        if st.button("Next ➡️"):
            @st.dialog("Please cast vote before leaving")
            def cast_vote_dialogue():
                criteria = question_data[index_dict[current_idx]]["data"]["criteria"]
                st.warning(f"***This is a question has been asked, your replies will not be recorded. This site is not actively seeking responds***")
                st.subheader("Which LLM performed best in terms of:")

                vote_dict = {}
                for each in criteria:
                    with st.container(border=True):
                        st.header(f"***{each}***:")
                        key = f"Q{current_idx + 1}_{each}"

                        vote_cast = st.pills("label", voting_options, selection_mode="single", key=key, label_visibility="collapsed")
                        vote_dict[each] = vote_cast

                comments_entry = st.text_input("Please add additional **comments** about their responses:")
                vote_dict["comments"] = comments_entry

                if st.button("Continue", use_container_width=True, type="primary"):
                    st.session_state.current_index += 1
                    st.rerun()

            if current_idx in stop_index:
                cast_vote_dialogue()
            else:
                st.session_state.current_index += 1
                st.rerun()
            
        # Additional info
        st.sidebar.markdown("### 📊 Conversation Stats")
        st.sidebar.write(f"Current position: {current_idx + 1}/{max_conversations}")
        # st.sidebar.markdown(random_index)
        
with results:
    show_results()