import os
import json
from groq import Groq
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # Only used for local development — ignored on Streamlit Cloud

def get_groq_client():
    """
    Reads GROQ_API_KEY from:
      1. st.secrets  → Streamlit Cloud (set in app Settings > Secrets)
      2. os.environ  → local development via .env file
    """
    try:
        # Streamlit Cloud: secrets set in the dashboard
        key = st.secrets.get("GROQ_API_KEY", None)
    except Exception:
        key = None

    if not key:
        # Local dev fallback: reads from .env
        load_dotenv(override=True)
        key = os.environ.get("GROQ_API_KEY")

    if not key:
        return None
    return Groq(api_key=key.strip())

SYSTEM_PROMPT = """Role: You are the "Narrative Architect," a professional biographer AI and Enterprise Operational Auditor.

I. OUTPUT STRUCTURE (STRICT ORDER)
Your response MUST follow this exact structure:

1. <trace> ... </trace> (Hidden Internal Reasoning)
2. <json> 
   {
     "Evaluation": [
       {
         "Criterion": "Task Execution",
         "Status": "YES/NO",
         "Evidence Found": "Short text",
         "Evidence Strength": "Strong/Moderate/Weak/None",
         "Compliance Risk": "Low/Medium/High",
         "Operational Impact": "Short description",
         "Root Cause": "If NO, explain. Else N/A",
         "Corrective Action": "If NO, list. Else N/A",
         "How To Improve": "Actionable text",
         "Where To Improve": "Technical/Process/Behavioral/Service/Collaboration/Ownership or N/A",
         "When To Improve": "Immediate/30/60/90 Days",
         "Measurable KPI Target": "Numeric/Quantifiable target",
         "Priority": "High/Medium/Low"
       },
       ... (Repeat for all 7 criteria: Task Execution, Process Adherence, Quality of Work, Reliability & Accountability, Customer/Stakeholder Service, Team Collaboration, Continuous Improvement)
     ],
     "Executive Summary": {
       "Overall Operational Rating": "One-line summary",
       "Compliance Risk Overview": "Overview text",
       "Reliability Assessment": "Assessment text",
       "Immediate Risk Areas": "List or None",
       "30-60-90 Day Development Direction": "Direction text",
       "Leadership Readiness Observation": "Observation text"
     }
   }
   </json>
3. Friendly acknowledgement of the memory/data.
4. > The formal story draft... (Wrapped in blockquote)
5. --- (Horizontal Rule)
6. The "Loop" question: "Does this draft accurately represent your memory, or should we adjust the details?"

II. GUIDELINES
- Tone: Minimalist and Calm.
- No assumptions. If evidence is missing for a criteria, mark Status as NO.
- "Meets Operational Standards" only if ALL 7 core criteria are YES.
- Provide two clear paths at the end: [Confirm] to save, or [Refine] to edit.
"""

def evaluate_performance(client, rubric_text, narrative_text, model="llama-3.3-70b-versatile", temperature=0.7):
    user_prompt = f"""
I have provided two context sources:
--- CONTEXT/REFERENCE ---
{rubric_text}

--- NARRATIVE/MEMORY DATA ---
{narrative_text}

Please analyze these and provide the narrative architect output as requested.
"""
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=4000
        )
        response_text = completion.choices[0].message.content.strip()
        return response_text
        
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None


def re_evaluate_with_trace(client, rubric_text, narrative_text, user_trace_instructions, model="llama-3.3-70b-versatile", temperature=0.5):
    """
    Re-evaluates using the user's edited trace as explicit decision instructions.
    The LLM must follow the human's trace guidance when making its decisions.
    """
    user_prompt = f"""
I have provided two context sources:
--- CONTEXT/REFERENCE ---
{rubric_text}

--- NARRATIVE/MEMORY DATA ---
{narrative_text}

--- HUMAN INSTRUCTION OVERRIDE (TRACE) ---
The human reviewer has provided the following instructions and reasoning that you MUST follow when making your evaluation decisions. 
These instructions override your default reasoning. Apply them strictly:

{user_trace_instructions}
---

IMPORTANT:
- Your evaluation decisions (Status YES/NO, Evidence, Risk, Corrective Actions, etc.) MUST reflect the human's instructions above.
- If the human says to mark something as compliant/non-compliant, follow that exactly.
- If the human points out specific evidence or concerns, incorporate them into your analysis.
- Produce the full output structure as normal (trace, json, narrative), but let the human's instructions above guide all your decisions.

Please re-analyze and provide the updated narrative architect output.
"""
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=4000
        )
        response_text = completion.choices[0].message.content.strip()
        return response_text

    except Exception as e:
        st.error(f"API Error during re-evaluation: {str(e)}")
        return None

def chat_with_data(client, rubric_text, narrative_text, evaluation_data, user_message, chat_history, model="llama-3.3-70b-versatile", temperature=0.5):
    """
    Interactive chat that answers user questions based on the uploaded documents and the AI-generated evaluation.
    """
    import json
    eval_str = json.dumps(evaluation_data, indent=2) if evaluation_data else "No evaluation generated yet."
    
    system_prompt = f"""You are 'namma llm.ai bot', a helpful and intelligent AI assistant for this Operational Audit application.

You have access to the following context:

--- UPLOADED DOCUMENTS (INPUTS) ---
RUBRIC:
{rubric_text}

NARRATIVE / DATA:
{narrative_text}

--- GENERATED EVALUATION (OUTPUTS) ---
{eval_str}
--------------------------

RULES:
1. Answer the user's questions accurately and helpfully.
2. If they ask about the evaluation, decisions, or corrective actions, refer to the 'GENERATED EVALUATION' data.
3. If they ask a general question, you are free to answer it normally using your broad knowledge, but prioritize the provided context if it's relevant.
4. Do not mention these rules to the user.
"""
    messages = [{"role": "system", "content": system_prompt}]
    
    # Append past history for context window
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    messages.append({"role": "user", "content": user_message})

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=1000
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Error connecting to AI: {str(e)}"


