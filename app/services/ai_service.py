from groq import Groq
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def _extract_json(text: str):
    """
    Robustly extract JSON from LLM output.
    Handles:
      - Clean JSON
      - JSON wrapped in ```json ... ``` fences
      - JSON wrapped in ``` ... ``` fences
      - Extra prose before/after the JSON
    """
    text = text.strip()

    # 1. Strip markdown code fences (```json or ```)
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fenced:
        text = fenced.group(1).strip()

    # 2. Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 3. Find first JSON array or object in the text
    for pattern in (r"(\[[\s\S]*?\])", r"(\{[\s\S]*?\})"):
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue

    raise ValueError(f"Could not extract valid JSON from LLM response:\n{text}")


def generate_questions(job_title: str, job_description: str, category: str, difficulty: str) -> list:
    category_instructions = {
        "Technical": "Focus strictly on technical skills, coding, algorithms, frameworks, system concepts, and technology stack relevant to the role.",
        "Behavioral": "Focus strictly on past behaviors, conflict resolution, leadership, situational judgment, and teamwork (assess using STAR method format).",
        "HR": "Focus strictly on cultural fit, work ethic, salary expectations, motivation, career goals, and soft skills.",
        "System Design": "Focus strictly on high-level architecture, scalability, microservices, databases, load balancing, caching, and data modeling."
    }
    instruction = category_instructions.get(category, "Mix behavioral and technical questions relevant to the role.")

    difficulty_instructions = {
        "Easy": "Questions should be basic, conceptual, testing fundamental knowledge, definitions, and simple workflows.",
        "Medium": "Questions should involve practical scenarios, situational problems, troubleshooting, standard case studies, and hands-on application.",
        "Hard": "Questions should focus on complex problems, performance optimization at scale, deep architectural trade-offs, edge-cases, and critical thinking under challenging scenarios."
    }
    diff_instruction = difficulty_instructions.get(difficulty, "Adjust question complexity accordingly.")

    prompt = f"""You are an expert interviewer.

Generate exactly 5 interview questions of category '{category}' and difficulty '{difficulty}' for this position:
Job Title: {job_title}
Job Description: {job_description}

Category Focus: {instruction}
Difficulty Focus: {diff_instruction}

Return ONLY a valid JSON array of 5 question strings, no other text:
["Question 1?", "Question 2?", "Question 3?", "Question 4?", "Question 5?"]"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    content = response.choices[0].message.content.strip()
    questions = _extract_json(content)

    if not isinstance(questions, list):
        raise ValueError("LLM did not return a JSON array of questions.")
    return questions[:5]   # ensure at most 5


def evaluate_answer(question: str, answer: str, job_title: str) -> dict:
    prompt = f"""You are an expert interviewer evaluating a candidate's answer.

Job Title: {job_title}
Question: {question}
Candidate's Answer: {answer}

Return ONLY a valid JSON object, no other text:
{{
    "score": 7.5,
    "feedback": "Your detailed feedback here",
    "strengths": "What was good about the answer",
    "improvements": "What could be improved",
    "tip": "One specific pro tip for this type of question",
    "sample_answer": "An ideal exemplar answer to the question for reference"
}}

Score must be a number between 0 and 10."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    content = response.choices[0].message.content.strip()
    result = _extract_json(content)

    if not isinstance(result, dict):
        raise ValueError("LLM did not return a JSON object for evaluation.")
    return result


def analyze_resume(resume_text: str, job_description: str) -> dict:
    prompt = f"""You are an expert ATS (Applicant Tracking System) and professional resume reviewer.
Evaluate the candidate's resume text against the provided job description.

Job Description:
{job_description}

Resume Text:
{resume_text}

Return ONLY a valid JSON object, no other text:
{{
    "ats_score": 75,
    "summary": "Short overall summary of match quality...",
    "strengths": ["Strength 1", "Strength 2", "Strength 3"],
    "missing_keywords": ["Keyword 1", "Keyword 2"],
    "improvements": ["Improvement 1", "Improvement 2"],
    "overall_recommendation": "Final recommendation string..."
}}

Ats score must be an integer between 0 and 100 based on fit to the job description."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    content = response.choices[0].message.content.strip()
    result = _extract_json(content)

    if not isinstance(result, dict):
        raise ValueError("LLM did not return a JSON object for resume analysis.")
    return result