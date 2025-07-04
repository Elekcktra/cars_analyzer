import streamlit as st
from streamlit.runtime.scriptrunner.script_runner import RerunException, RerunData
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
from generators.gpt_generator import generate_cars_content
import re

# ========== SETUP ========== #
st.set_page_config(
    page_title="Vrushti's CARS Analyzer",
    page_icon="📚",
    layout="centered"
)

# ========== CORE ANALYSIS ========== #
def analyze_errors(df):
    # Pattern detection
    error_patterns = {
        "Tone/Attitude": ["tone", "attitude", "perspective", "viewpoint", "neutral", "negative"],
        "Context Misread": ["context", "paragraph", "line", "section", "reread", "passage"],
        "Overthinking": ["assumed", "overthought", "bias", "should be", "reasoning"],
        "Detail Missed": ["missed", "overlooked", "didn't notice", "not stated"],
        "Question Misinterpretation": ["misunderstood", "misinterpreted", "question"],
        "Structure Error": ["main idea", "first sentence", "paragraph structure"],
        "Vocabulary": ["word", "term", "phrase", "meaning", "empirical"]
    }
    
    results = defaultdict(list)
    
    for _, row in df.iterrows():
        # Skip rows with missing error descriptions
        if pd.isna(row["Why_I_Got_It_Wrong"]):
            continue
            
        error_text = str(row["Why_I_Got_It_Wrong"]).lower() if pd.notna(row["Why_I_Got_It_Wrong"]) else ""
        passage = row["Passage_Title"]
        
        for pattern, keywords in error_patterns.items():
            if any(kw in error_text for kw in keywords):
                results[pattern].append(passage)
    
    return results
    
# ========== HELPER FUNCTIONS ========== #
def get_fix_suggestion(pattern):
    suggestions = {
        "Tone/Attitude": "Highlight adjectives/verbs that indicate tone. Practice identifying neutral vs. opinionated language.",
        "Context Misread": "Before answering, summarize each paragraph in 5 words. Check question references (e.g., 'paragraph 3').",
        "Overthinking": "Eliminate answers that require assumptions not in text. Stick to passage evidence only.",
        "Detail Missed": "Circle key nouns/numbers when reading. Verify answer choices against specific passage lines.",
        "Question Misinterpretation": "Restate the question in your own words before looking at answers.",
        "Structure Error": "Note the first/last sentences of paragraphs - they often contain main ideas.",
        "Vocabulary": "Make flashcards for unfamiliar terms. Look for defining phrases like 'means' or 'refers to'."
    }
    return suggestions.get(pattern, "Review similar question types in practice passages.")

def generate_sample_question(error_report):
    if not error_report:
        return "Practice identifying main ideas in 3 passages today."
    
    top_error = max(error_report.items(), key=lambda x: len(x[1]))
    samples = {
        "Tone/Attitude": "Read a passage and highlight all tone words (e.g., 'criticizes', 'admires').",
        "Context Misread": "Find a passage with multiple viewpoints. Map which paragraphs support each view.",
        "Overthinking": "Do 5 questions where you must justify each answer with exact passage text.",
        "Detail Missed": "Annotate a passage by underlining: dates, names, and specialized terms.",
        "Question Misinterpretation": "Restate 3 hard questions in your own words before answering.",
        "Structure Error": "Outline a passage's structure: main idea → evidence → conclusion.",
        "Vocabulary": "Identify 5 unfamiliar words from passages and guess meanings from context."
    }
    return f"{samples.get(top_error[0], '')} (Your top error: {top_error[0]})"

# ========== UI ========== #
st.title("Vrushti's CARS Analyzer")
st.subheader("Upload your error log")

# File upload
uploaded_file = st.file_uploader(
    "📤 Upload CSV", 
    type="csv",
    help="Columns needed: Passage_Title, #, Why_I_Got_It_Wrong"
)

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Clean data - handle empty/missing values
        df = df.dropna(subset=["Why_I_Got_It_Wrong"])
        df["Why_I_Got_It_Wrong"] = df["Why_I_Got_It_Wrong"].astype(str)

        st.success(f"Loaded {len(df)} errors for analysis!")

        # Analysis
        error_report = analyze_errors(df)

        # Show results
        st.subheader("Your Error Patterns")
        if error_report:
            for pattern, passages in error_report.items():
                with st.expander(f"{pattern} ({len(passages)}x)"):
                    st.write(f"**Examples:** {', '.join(map(str, set(passages)))}")
                    st.write(f"**Fix:** {get_fix_suggestion(pattern)}")

            # Progress chart
            st.subheader("Error Trends")
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.bar(error_report.keys(), [len(v) for v in error_report.values()])
            plt.xticks(rotation=45, ha='right')
            st.pyplot(fig)

            # Sample question
            st.subheader("Targeted Practice")
            st.write(generate_sample_question(error_report))

            # ========== ✅ PASSAGE GENERATION ========== #
            top_errors = sorted(error_report.items(), key=lambda x: len(x[1]), reverse=True)[:3]
            st.subheader("🧠 Custom Practice Passages")

            for idx, (err_type, _) in enumerate(top_errors):
                with st.expander(f"{err_type} Practice"):
                    passage_key = f'passage_{err_type}_{idx}'
                    chat_key = f'chat_{err_type}_{idx}'
                    reveal_key = f'reveal_{err_type}_{idx}'

                    # Generate passage only once
                    if passage_key not in st.session_state:
                        st.session_state[passage_key] = generate_cars_content(err_type)

                    # Parse passage and answers
                    full_text = st.session_state[passage_key]
                    parts = full_text.split("### Answer & Explanation")
                    passage_text = parts[0].strip()
                    answers_text = parts[1].strip() if len(parts) > 1 else "⚠️ Answers not available."

                    # Show the passage + questions by default
                    st.markdown("### 📘 Passage + Questions")
                    st.markdown(passage_text)

                    # Reveal answers button logic
                    if reveal_key not in st.session_state:
                        st.session_state[reveal_key] = False

                    if not st.session_state[reveal_key]:
                        if st.button("🔍 Reveal Answers & Explanations", key=f"btn_{reveal_key}"):
                            st.session_state[reveal_key] = True

                    if st.session_state[reveal_key]:
                        st.markdown("### ✅ Answers & Explanations")
                        st.markdown(answers_text)

                    # ========== CHAT INTERFACE ========== #
                    st.markdown("---")
                    st.markdown("💬 **Ask a question about the passage:**")

                    if chat_key not in st.session_state:
                        st.session_state[chat_key] = []

                    for msg in st.session_state[chat_key]:
                        with st.chat_message(msg["role"]):
                            st.markdown(msg["content"])

                    if prompt := st.chat_input("Ask about this passage...", key=f"input_{chat_key}"):
                        st.session_state[chat_key].append({"role": "user", "content": prompt})

                        try:
                            full_context = [{"role": "assistant", "content": st.session_state[passage_key]}] + st.session_state[chat_key][-5:]
                            reply = generate_cars_content(error_type=err_type, conversation_history=full_context)
                            st.session_state[chat_key].append({"role": "assistant", "content": reply})

                            # Immediately rerun so the UI updates and shows the assistant reply now
                            raise RerunException(RerunData())
                        except Exception as e:
                            st.error(f"GPT failed: {str(e)}")


        else:
            st.warning("No analyzable error patterns found. Add more detailed descriptions.")

        # Show raw data
        with st.expander("View Raw Data"):
            st.dataframe(df)

    except Exception as e:
        st.error(f"Error processing file: {str(e)}")

# ========== FOOTER ========== #
st.divider()
st.caption("MCAT CARS Analyzer v2.0 | Now with interactive Q&A")