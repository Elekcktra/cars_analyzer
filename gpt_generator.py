# generators/gpt_generator.py
from openai import OpenAI
from dotenv import load_dotenv
import os
import random

# Initialize OpenAI
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

def generate_cars_content(error_type, conversation_history=None):
    """
    Generates MCAT CARS-style passage + questions or responds to a user follow-up.
    """

    ERROR_MISTAKES = {
        "Tone/Attitude": ["misidentifying neutral tone", "overlooking qualifying words"],
        "Context Misread": ["taking quotes out of context", "ignoring paragraph transitions"],
        "Detail Missed": ["skimming complex sentences", "missing parenthetical details"],
        "Structure Error": ["confusing evidence for conclusion", "missing counterarguments"],
        "Vocabulary": ["assuming familiar definitions", "ignoring contextual clues"]
    }

    if not conversation_history:
        # ----- SYSTEM PROMPT FOR FULL GENERATION ----- #
        system_prompt = f"""
You are a witty and sharp med student who scored 132 on the MCAT CARS section.
You're helping a premed friend practice their weakest CARS skill: {error_type}.

Write a ~550-word AAMC-style passage followed by **3 multiple choice questions**:
- Q1: [MAIN IDEA] (easiest)
- Q2: [DETAIL/INFERENCE]
- Q3: [TONE/STRUCTURE] (hardest)

Passage rules:
- Use at least **3 direct quotes** ("...") like AAMC does
- No outside knowledge — base logic only on the passage
- Include transitional words like "however", "notably", etc.
- Topic should be challenging but interesting — philosophy, history, ethics, literature, sociology, etc.

Question formatting:
[MAIN IDEA]  
What is the author’s central argument?  
A) ...  
B) ...  
C) ...  
D) ...  

Then include a section like this:

### Answer & Explanation  
**Question 1**  
Correct Answer: B  
- B is correct because "..." (Para 2)  
- A is wrong because "..."  
- C is flawed because "..."  
- D contradicts "..."  

**Question 2**  
Correct Answer: C  
...  

**Question 3**  
Correct Answer: D  
...  

Other instructions:
- Randomize the correct answer between A-D for each question
- Make distractors **plausible but wrong**
- Make explanations sound human — like a med student tutoring a friend
- No fluff. Be kind, clear, and quote the passage often
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Create a full CARS passage and 3 MCQs targeting: {error_type}"}
        ]
        model = "gpt-4o"  # Use gpt-4o if available

    else:
        # ----- FOLLOW-UP QUESTION ----- #
        system_prompt = f"""
You are a friendly MCAT CARS tutor trained in AAMC logic.
Your student needs help with a question about a passage involving the skill: {error_type}.

Use quotes and paragraph references to explain things clearly and kindly.
Make it sound like you're explaining it to a smart premed friend, not a robot.
"""

        messages = [
            {"role": "system", "content": system_prompt}
        ] + conversation_history
        model = "gpt-4o"

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        presence_penalty=0.3,
        frequency_penalty=0.2
    )

    return response.choices[0].message.content
