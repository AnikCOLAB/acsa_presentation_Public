import json
import streamlit as st
import plotly.graph_objects as go
import math


from aws_function import (list_folders,
                          read_file)


#process the data
with open("question_mapped.json", "r", encoding="utf-8") as f:
    question_data = json.load(f)

with open("user_record.json", "r", encoding="utf-8") as f:
    user_record = json.load(f)

stop_index = [2,4,7,10,12,15,17,19,22,25]
intro_index = [0,3,5,8,11,13,16,18,20,23]
index_dict = {}
for each in range(len(stop_index)):
    index_dict[stop_index[each]] = intro_index[each]

user_list = list_folders()
username_list = []
username_dict = {}
master_data = {}


for user_id in user_list:
    user_fullname = user_id.split("@")[0]
    user_name = user_fullname[:-1]

    file_path = f"{user_id}/{user_fullname}_data"
    user_data = read_file(file_path)

    master_data[user_name] = user_data

    question_answered = 0
    total_criteria = 0
    for index, criteria in user_data.items():
        for criterion, value in criteria.items():
            if criterion != "comments":
                if value is not None:
                    question_answered += 1
                    if value == "LLM 01":
                        user_record[index][criterion]["GPT"].append(user_id)
                    if value == "LLM 02":
                        user_record[index][criterion]["Gemini"].append(user_id)
                    if value == "Both":
                        user_record[index][criterion]["GPT"].append(user_id)
                        user_record[index][criterion]["Gemini"].append(user_id)
                total_criteria += 1
    
    username_dict[user_name] = question_answered


sorted_items = dict(sorted(username_dict.items(), key=lambda item: item[1], reverse=True))



# Criteria we care about
criteria = ["Accuracy", "Relevance", "Clarity", "Critical Thinking"]


# --- Generate 10 charts (one per outer key) ---
fig_dict= {}
for outer_key in user_record:
    sub_topic = question_data[index_dict[int(outer_key)]]["data"]["sub_topic"]
    gpt_counts = []
    gemini_counts = []
    crit_labels = []

    for crit in criteria:
        if crit in user_record[outer_key]:
            gpt_counts.append(len(user_record[outer_key][crit].get("GPT", [])))
            gemini_counts.append(len(user_record[outer_key][crit].get("Gemini", [])))
            crit_labels.append(crit)

    if crit_labels:  # Only plot if there’s something
        fig = go.Figure(data=[
            go.Bar(name="GPT", x=crit_labels, y=gpt_counts),
            go.Bar(name="Gemini", x=crit_labels, y=gemini_counts)
        ])
        fig.update_layout(
            title=f"{sub_topic}",
            barmode="group",
            # yaxis_title="Votes",
            # xaxis_title="Criteria",
            barcornerradius=3,
            height=400
        )
        fig_dict[f"{sub_topic}"] = fig

# --- Final summary chart (sum over all keys) ---
summary_gpt = {c: 0 for c in criteria}
summary_gemini = {c: 0 for c in criteria}

for outer_key in user_record:
    for crit in criteria:
        if crit in user_record[outer_key]:
            summary_gpt[crit] += len(user_record[outer_key][crit].get("GPT", []))
            summary_gemini[crit] += len(user_record[outer_key][crit].get("Gemini", []))

# Create the summary bar chart
fig_summary = go.Figure(data=[
    go.Bar(name="GPT", x=criteria, y=[summary_gpt[c] for c in criteria]),
    go.Bar(name="Gemini", x=criteria, y=[summary_gemini[c] for c in criteria])
])
fig_summary.update_layout(
    title="Total Votes for GPT vs Gemini (All Criteria)",
    barmode="group",
    yaxis_title="Total Votes",
    xaxis_title="Criteria",
    barcornerradius=5
)

@st.dialog("Respose record")
def record_dialogue(data):
    for keys, values in data.items():
        sub_topic = question_data[index_dict[int(keys)]]["data"]["sub_topic"]
        st.markdown(sub_topic)
        with st.container(border=True):
            for criteris_key, criteria_value in values.items():
                if criteria_value == "LLM 01":
                    criteria_value = "GPT"
                elif criteria_value == "LLM 02":
                    criteria_value = "Gemini"
                st.markdown(f"   **{criteris_key}** : {criteria_value}")

def show_results():
    st.warning(f"***We are still collecting responses, this is not the final outcome!***")
    st.plotly_chart(fig_summary)
    st.divider()

    chunk_size = 5
    column_grid = (10 // chunk_size)
    column_list = st.columns(chunk_size)
    chunks = [[x for x,y in fig_dict.items()][i:i + column_grid] for i in range(0, 10, column_grid)]
    for each in range(chunk_size):
        with column_list[each]:
            for figure in chunks[each]:
                st.plotly_chart(fig_dict[figure])
                # st.markdown(f"**{figure}**")
    st.divider()


    
    st.subheader("Leaderboard")
    st.warning(f"***All user information is kept confidential, Please reach out to the authors to get user demographs.***")

    chunk_size = 4  # number of columns
    user_list = list(sorted_items.keys())
    total_users = len(user_list)

    # how many items go into each chunk
    chunk_length = math.ceil(total_users / chunk_size)

    # create chunks properly
    chunks = [user_list[i:i + chunk_length] for i in range(0, total_users, chunk_length)]

    # create columns
    column_list = st.columns(chunk_size)

    # display chunks
    user_count = 1
    total_progress = 0
    for each in range(len(chunks)):
        with column_list[each]:
            for user_name in chunks[each]:
                progress = sorted_items[user_name] / total_criteria
                my_bar = st.progress(
                    progress,
                    text=f"Participant {user_count}"
                )
                total_progress += progress
                user_count += 1

    total_progress_final = total_progress / (user_count)
    my_bar = st.progress(total_progress_final,text=f"**Total Progress: {total_progress_final * 100}%**")

    st.subheader("See individual reply:")
    # chunk_size = 3
    # column_grid = (len(user_list) // chunk_size)
    column_list = st.columns(chunk_size)

    # chunks = [user_list[i:i + column_grid] for i in range(0, len(user_list), column_grid)]
    user_count = 1
    for each in range(chunk_size):
        with column_list[each]:
            for user_name in chunks[each]:
                # user_fullname = user_id.split("@")[0]
                # user_name = user_fullname[:-1]
                if st.button(f"Participant {user_count}", use_container_width=True):
                    record_dialogue(master_data[user_name])
                user_count += 1
    
    json_str = json.dumps(master_data, indent=4)
    st.download_button(
        use_container_width=True,
        label="Download All User Record",
        data=json_str,
        file_name="data.json",
        mime="application/json",
        icon=":material/download:",
        type="primary"
    )

