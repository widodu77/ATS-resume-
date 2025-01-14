from copy import deepcopy
from typing import Dict, TypedDict, Optional
from langgraph.graph import StateGraph, END
import random
import time
import PyPDF2
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
import time
import streamlit as st

prompt_clean = "Remove special characters, unnecessary text from this resume. Resume : {} "

subagent_desc = {"Impact": {
"Quantify impact": "Use specific numbers, percentages, or metrics to demonstrate the scale and significance of your achievements.",
"Repetition": "Maintain consistent language and terminology, but avoid repeating the same phrases or descriptions across multiple sections.",
"Weak verbs": "Use strong, action-oriented verbs to effectively convey your contributions and responsibilities.",
"Verb tenses": "Use present tense for current roles and past tense for previous roles, maintaining consistency throughout.",
"Responsibilities": "Focus on key duties and tasks tailored to the job you're applying for, rather than generic job descriptions.",
"Spelling & consistency": "Ensure your resume is free of errors and maintains consistent formatting, capitalization, and punctuation."
},
"Brevity":{
"Length": "Keep your resume concise, typically one page, up to two pages for extensive experience.",
"Bullet Lengths": "Maintain concise bullet points, typically 1-2 lines, to highlight the most important information.",
"Filler Words": "Minimize the use of filler words to maximize the impact and conciseness of your resume."
},
"Style": {
    "Buzzwords": "Ensure your resume includes relevant industry-specific keywords and buzzwords that match the job description.",
    "Dates": "Format your employment dates consistently (e.g. MM/YYYY) and ensure there are no unexplained gaps in your work history.",
    "Contact and Personal Details": "Make sure your name, contact information, and other personal details are clearly displayed and up-to-date.",
    "Readability": "Use a clean, simple layout and font that is easy for the ATS to parse. Avoid complex formatting, tables, and graphics.",
    "Personal Pronouns": "Minimize the use of personal pronouns like 'I', 'me', and 'my' to keep the focus on your achievements and skills.",
    "Active Voice": "Use active voice to describe your responsibilities and accomplishments, making your resume more impactful.",
    "Consistency": "Maintain consistent formatting, language, and style throughout your resume to present a professional and polished document."
},
"Sections": {
    "Summary": "A concise overview of your key qualifications, experience, and career goals.",
    "Education": "Details about your academic background, including degrees, schools, and relevant coursework or achievements.",
    "Unnecessary Sections": "Sections that may not be relevant or add value to your resume, such as hobbies, interests, or irrelevant work experience.",
    "Skills": "A list of your relevant technical, soft, and transferable skills that demonstrate your capabilities."
}
}

agent_desc = {
    "Impact": "Ensuring your resume content showcases your achievements, contributions, and the value you can bring to an employer.",
    "Brevity": "Keeping your resume concise, focused, and easy to scan, typically one page for entry-level and two pages for experienced candidates.",
    "Style": "The overall formatting, layout, and visual appeal of your resume, which should be clean, consistent, and professional.",
    "Sections": "The key components of a resume, such as Summary, Education, Work Experience, Skills, and any other relevant sections."
}

prompt_subagent = "You are a Resume Expert. You need to analyse the given Resume on {} i.e. {}. Give a score on a scale of 10 & suggest improvements in 1-2 lines. Output the score and 1-2 line suggestion.No bullet and headings in output. Resume: {}"
prompt_agent = "You are a Resume Expert. You need to analyse the given Resume on {} i.e. {}. You need to summarize the below reports about a resume from your sub-ordinates. \
Output a score out of 10 and suggest improvements in 1-2 lines. Output the score and 1-2 line suggestion. No bullet and headings in output. Report : {}"
prompt_superagent = "You are a Resume Expert. Given the below feedback, Rate the resume on a scale of 10 alongside a reason in very short. Use the below analogy \
Score 3 or less: Trash, Score 5 or less: Needs major improvements,Score 6-7: Average,Score 8-9: Excellent,Score 10: Exceptional \n  Output the score-label and a paragraph. Feedback : {}"

agent_subagent_pairs = {}
for main_key, nested_dict in subagent_desc.items():
        pairs = {main_key:list(nested_dict.keys())}
        agent_subagent_pairs.update(pairs)

history = deepcopy(subagent_desc)

agent = list(agent_subagent_pairs.keys())[0]
subagent = agent_subagent_pairs[agent][0]

for key, value in history.items():
    if isinstance(value, dict):
        value["Overall"] = ""
        for nested_key, nested_value in value.items():
            value[nested_key] = ""
			
GOOGLE_API_KEY= st.text_input("Enter Password", type="password")
if GOOGLE_API_KEY:
	genai.configure(api_key=GOOGLE_API_KEY)
	model = ChatGoogleGenerativeAI(model="gemini-pro",google_api_key=GOOGLE_API_KEY)

def llm(x):
    return model.invoke(x).content
	
class GraphState(TypedDict):
    subagent_feedback: Optional[list] = []
    agent_feedback: Optional[list] = []
    history: Optional[dict] = {}
    resume: Optional[str] = None
    final_verdict: Optional[str] = None
    all_pairs: Optional[list]=[]
    subagent: Optional[str] = None
    agent: Optional[str] = None

workflow = StateGraph(GraphState)

def handle_clean(state):
    resume = state.get('resume')
    
    st.success("Cleaning loaded text..")
    resume = llm(prompt_clean.format(resume))
    return {'resume':resume}

def handle_subagent(state):
    print("In sub-agent")
    time.sleep(5)
    history = state.get('history')
    subagent_feedback = state.get('subagent_feedback')
    resume = state.get("resume")
    all_pairs = state.get('all_pairs')
    agent = state.get('agent')

    agent=list(all_pairs.keys())[0]
    subagent=all_pairs[agent][0]
    
    current_feedback = llm(prompt_subagent.format(subagent,subagent_desc[agent][subagent],resume))
    subagent_feedback.extend(["{} : {}".format(subagent,current_feedback)])
    history[agent][subagent]=current_feedback

    all_pairs[agent].remove(subagent)
    
    return {'subagent_feedback':subagent_feedback,'history':history,"all_pairs":all_pairs,'agent':agent}

def handle_agent(state):
    print("In agent")
    time.sleep(5)
    feedback = state.get('subagent_feedback')
    agent_feedback = state.get('agent_feedback')
    all_pairs = state.get('all_pairs')
    history = state.get("history")
    
    agent=list(all_pairs.keys())[0]

    st.info("Reviewing {} ...".format(agent))

    summary = llm(prompt_agent.format(agent,agent_desc[agent],feedback))
    agent_feedback.extend(["{} : {}".format(agent,summary)])
    history[agent]["Overall"]=summary
    
    del all_pairs[agent]

    try:
        agent = list(all_pairs.keys())[0]
    except:
        pass

    return {'agent_feedback':agent_feedback,'history':history,"all_pairs":all_pairs,"agent":agent}

def handle_superagent(state):
    print("In superagent")
    time.sleep(5)
    st.success("Final verdict getting updated...")
    history = state.get("history")
    feedback = state.get('agent_feedback')
    result = llm(prompt_superagent.format(feedback))
    history.update({"Final Verdict":result})

    return {'final_verdict':result,'history':history}
	
workflow.add_node("handle_clean",handle_clean)
workflow.add_node("handle_subagent",handle_subagent)
workflow.add_node("handle_agent",handle_agent)
workflow.add_node("handle_superagent",handle_superagent)

def subagent_check(state):
    agent = state.get('agent')
    all_pairs = state.get('all_pairs')
    
    if len(all_pairs[agent]):
        return "handle_subagent"
    else:
        return "handle_agent"

def agent_check(state):
    all_pairs = state.get('all_pairs')

    if len(all_pairs.keys()):
        return "handle_subagent"
    else:
        return "handle_superagent"

workflow.add_conditional_edges(
    "handle_subagent",
    subagent_check,
    {
        "handle_subagent": "handle_subagent",
        "handle_agent": "handle_agent"
    }
)

workflow.add_conditional_edges(
    "handle_agent",
    agent_check,
    {
        "handle_subagent": "handle_subagent",
        "handle_superagent": "handle_superagent"
    }
)

workflow.set_entry_point("handle_clean")
workflow.add_edge('handle_clean', "handle_subagent")
workflow.add_edge('handle_superagent',END)

app = workflow.compile()

lines = []
pdf_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if GOOGLE_API_KEY and pdf_file:
		pdf_reader = PyPDF2.PdfReader(pdf_file)
			
		# Get the number of pages in the PDF
		num_pages = len(pdf_reader.pages)
			
		# Loop through each page
		for page_num in range(num_pages):
				# Get the page object
				page = pdf_reader.pages[page_num]
				
				# Extract the text from the page
				page_text = page.extract_text()
				
				# Split the text into lines
				page_lines = page_text.split('\n')
				
				# Append the lines to the list
				lines.extend(page_lines)
				
		lines = '\n'.join(lines)
				
		st.subheader("Resume Review")
				
		conversation = app.invoke({"subagent_feedback":[],"agent_feedback":[],"history":history,"resume":lines,"all_pairs":deepcopy(agent_subagent_pairs),'agent':agent,'subagent':subagent},{"recursion_limit":100})
				
		print(conversation)
		for key, value in conversation['history'].items():
					with st.expander(key):
						st.write(value)
