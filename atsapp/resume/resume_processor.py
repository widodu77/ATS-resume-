# resume/resume_processor.py

import io
import time
from copy import deepcopy
from typing import Dict, TypedDict, Optional

import PyPDF2
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

from django.conf import settings

#promps need a bit of work lol 

#update: just switch some of the promps, nexxt would be to remove and merge some, since each subagent is basically an additional api call, 
#it takes hella time and compute to get the final result, so might be a great idea to merge the prompts, i believe it would also kill some of 
#the repition that would happen in the final product 

prompt_clean = "Remove special characters, unnecessary text from this resume. Resume : {} "

subagent_desc = {"Impact": {
"Quantify impact, Repetition, weak verbs": "Use specific numbers, percentages, or metrics to demonstrate the scale and significance of your achievements;"
"Maintain consistent language and terminology, but avoid repeating the same phrases or descriptions across multiple sections; "
"Use strong, action-oriented verbs to effectively convey your contributions and responsibilities.",
"Verb tenses, Responsibilities, Spelling & consistency": "Use present tense for current roles and past tense for previous roles, maintaining consistency throughout;"
"Focus on key duties and tasks tailored to the job you're applying for, rather than generic job descriptions;"
"Ensure your resume is free of errors and maintains consistent formatting, capitalization, and punctuation."
},
"Brevity":{
"Length": "Keep your resume concise, typically one page, up to two pages for extensive experience.",
"Bullet Lengths, Filler Words": "Maintain concise bullet points, typically 1-2 lines, to highlight the most important information;"
"Minimize the use of filler words to maximize the impact and conciseness of your resume"
},
"Style": {
    "Buzzwords, Dates, Contact and Personal Details": "Ensure your resume includes relevant industry-specific keywords and buzzwords that match the job description;"
    "Format your employment dates consistently (e.g. MM/YYYY) and ensure there are no unexplained gaps in your work history"
    "Make sure your name, contact information, and other personal details are clearly displayed and up-to-date",
    "Readability, Personal Pronouns, Active Voice, Consistency": "Use a clean, simple layout and font that is easy for the ATS to parse. Avoid complex formatting, tables, and graphics."
    "Minimize the use of personal pronouns like 'I', 'me', and 'my' to keep the focus on your achievements and skills"
    "Use active voice to describe your responsibilities and accomplishments, making your resume more impactful."
    "Maintain consistent formatting, language, and style throughout your resume to present a professional and polished document",
},
"Sections": {
    "Education, Skills": "Details about your academic background, including degrees, schools, and relevant coursework or achievements;"
    "A list of your relevant technical, soft, and transferable skills that demonstrate your capabilities.",
    "Unnecessary Sections": "Sections that may not be relevant or add value to your resume, such as hobbies, interests, or irrelevant work experience.",
    
}
}

agent_desc = {
    "Impact": "Ensuring your resume content showcases your achievements, contributions, and the value you can bring to an employer.",
    "Brevity": "Keeping your resume concise, focused, and easy to scan, typically one page for entry-level and two pages for experienced candidates.",
    "Style": "The overall formatting, layout, and visual appeal of your resume, which should be clean, consistent, and professional.",
    "Sections": "The key components of a resume, such as Summary, Education, Work Experience, Skills, and any other relevant sections."
}

prompt_subagent = (
    "You are a Resume Expert. You need to analyse the given Resume on {} i.e. {}. "
    "Give a score on a scale of 10 & suggest improvements in 1-2 lines. "
    "Output the score and 1-2 line suggestion. No bullet and headings in output. Resume: {}"
)
prompt_agent = (
    "You are a Resume Expert. You need to analyse the given Resume on {} i.e. {}. "
    "You need to summarize the below reports about a resume from your sub-ordinates. "
    "Output a score out of 10 and suggest improvements in 1-2 lines. "
    "Output the score and 1-2 line suggestion. No bullet and headings in output. Report : {}"
)
prompt_superagent = (
    "You are a Resume Expert. Given the below feedback, Rate the resume on a scale of 10 alongside a reason in very short. "
    "Use the below analogy \nScore 3 or less: Trash, Score 5 or less: Needs major improvements, "
    "Score 6-7: Average, Score 8-9: Excellent, Score 10: Exceptional \n"
    "Output the score-label and a paragraph. Feedback : {}"
)


agent_subagent_pairs = {}
for main_key, nested_dict in subagent_desc.items():
    agent_subagent_pairs[main_key] = list(nested_dict.keys())


history = deepcopy(subagent_desc)
for key, value in history.items():
    if isinstance(value, dict):
        value["Overall"] = ""
        for nested_key in value.keys():
            value[nested_key] = ""


agent = list(agent_subagent_pairs.keys())[0]
subagent = agent_subagent_pairs[agent][0]


GOOGLE_API_KEY = settings.GEMINI_API_KEY
genai.configure(api_key=GOOGLE_API_KEY)
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", google_api_key=GOOGLE_API_KEY)


def llm(prompt: str) -> str:
    """Simple wrapper for invoking the language model."""
    return model.invoke(prompt).content


class GraphState(TypedDict):
    subagent_feedback: Optional[list]
    agent_feedback: Optional[list]
    history: Optional[dict]
    resume: Optional[str]
    final_verdict: Optional[str]
    all_pairs: Optional[dict]
    subagent: Optional[str]
    agent: Optional[str]

workflow = StateGraph(GraphState)

def handle_clean(state: dict) -> dict:
    resume_text = state.get('resume')
    print("Cleaning loaded text...")
    cleaned_resume = llm(prompt_clean.format(resume_text))
    return {'resume': cleaned_resume}

def handle_subagent(state: dict) -> dict:
    print("In sub-agent...")
    time.sleep(1)  
    current_history = state.get('history')
    subagent_feedback = state.get('subagent_feedback')
    resume_text = state.get("resume")
    all_pairs = state.get('all_pairs')
    current_agent = list(all_pairs.keys())[0]
    current_subagent = all_pairs[current_agent][0]
    current_feedback = llm(prompt_subagent.format(
        current_subagent,
        subagent_desc[current_agent][current_subagent],
        resume_text
    ))
    subagent_feedback.append(f"{current_subagent} : {current_feedback}")
    current_history[current_agent][current_subagent] = current_feedback
    
    all_pairs[current_agent].remove(current_subagent)
    return {
        'subagent_feedback': subagent_feedback,
        'history': current_history,
        "all_pairs": all_pairs,
        'agent': current_agent
    }

def handle_agent(state: dict) -> dict:
    print("In agent...")
    time.sleep(1)
    feedback_list = state.get('subagent_feedback')
    agent_feedback = state.get('agent_feedback')
    all_pairs = state.get('all_pairs')
    current_history = state.get("history")
    current_agent = list(all_pairs.keys())[0]
    print(f"Reviewing {current_agent} ...")
    summary = llm(prompt_agent.format(
        current_agent,
        agent_desc[current_agent],
        feedback_list
    ))
    agent_feedback.append(f"{current_agent} : {summary}")
    current_history[current_agent]["Overall"] = summary
    del all_pairs[current_agent]

    try:
        next_agent = list(all_pairs.keys())[0]
    except IndexError:
        next_agent = None
    return {
        'agent_feedback': agent_feedback,
        'history': current_history,
        "all_pairs": all_pairs,
        "agent": next_agent
    }

def handle_superagent(state: dict) -> dict:
    print("In superagent...")
    time.sleep(1)
    current_history = state.get("history")
    feedback_list = state.get('agent_feedback')
    result = llm(prompt_superagent.format(feedback_list))
    current_history.update({"Final Verdict": result})
    return {'final_verdict': result, 'history': current_history}

def subagent_check(state: dict) -> str:
    current_agent = state.get('agent')
    all_pairs = state.get('all_pairs')
    if all_pairs[current_agent]:
        return "handle_subagent"
    else:
        return "handle_agent"

def agent_check(state: dict) -> str:
    all_pairs = state.get('all_pairs')
    if all(all(not subs for subs in all_pairs.get(agent, [])) for agent in all_pairs):
        return "handle_superagent"
    else:
        return "handle_subagent"

workflow.add_node("handle_clean", handle_clean)
workflow.add_node("handle_subagent", handle_subagent)
workflow.add_node("handle_agent", handle_agent)
workflow.add_node("handle_superagent", handle_superagent)

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
workflow.add_edge('handle_superagent', END)

app = workflow.compile()


def score_resume(pdf_file) -> Dict:
    """
    this is the big guy that does everything
    """
    
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    lines = []
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            lines.append(page_text)
    full_text = "\n".join(lines)
    
    initial_state = {
        "subagent_feedback": [],
        "agent_feedback": [],
        "history": deepcopy(history),
        "resume": full_text,
        "all_pairs": deepcopy(agent_subagent_pairs),
        "agent": agent,
        "subagent": subagent
    }
    
    result_state = app.invoke(initial_state, {"recursion_limit": 100})
    return result_state
