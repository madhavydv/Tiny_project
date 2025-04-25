from transformers import pipeline
import streamlit as st

# Move model loading inside functions to avoid loading at import time
def get_generator():
    return pipeline("text2text-generation", model="google/flan-t5-large", max_length=512)

# Import PyTorch-related modules only when needed
def generate_quiz(subject, topic, difficulty):
    # Import inside function to delay loading until needed
    
    
    generator = pipeline("text2text-generation", model="google/flan-t5-small", max_length=512)
    
    prompt = (
        f"Generate 5 multiple choice questions for a quiz on the topic '{topic}' "
        f"under the subject '{subject}' with {difficulty} difficulty. "
        "Each question should have 4 options labeled A, B, C, and D, and include the correct answer.\n\n"
        "Format:\n"
        "Q1. Question text?\n"
        "A. Option A\nB. Option B\nC. Option C\nD. Option D\nAnswer: B\n"
    )

    # Generate the quiz text
    result = generator(prompt)[0]["generated_text"]

    # Parse the result into question objects
    questions = []
    current = {}
    
    lines = result.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith("Q"):
            if current and "question" in current:
                questions.append(current)
                current = {}
            current["question"] = line
            current["options"] = []
        elif line.startswith(("A.", "B.", "C.", "D.")):
            current.setdefault("options", []).append(line)
        elif line.startswith("Answer:"):
            current["answer"] = line.replace("Answer:", "").strip()
        
        i += 1

    # Add the last question if it exists
    if current and "question" in current:
        questions.append(current)

    return questions

def evaluate_quiz(questions, answers):
    correct = 0
    for i in range(len(questions)):
        if i < len(answers) and answers[i]:  # Check if answer exists and is not empty
            expected = questions[i].get("answer", "").upper().strip()
            given = answers[i].upper().strip()
            if expected == given:
                correct += 1

    return correct