import os
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fetch_topic_content(subject, topic, attempt=0, broader=False):
    """Fetch content about a topic from Wikipedia with multiple attempts"""
    import requests
    import json
    import time
    
    def clean_text(text):
        """Clean wiki text by removing special characters and extra whitespace"""
        import re
        # Remove citations [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)
        # Remove parenthetical text (often contains less relevant info)
        text = re.sub(r'\([^)]*\)', '', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:-]', '', text)
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        # Fix spacing around punctuation
        text = re.sub(r'\s*([.,!?;:])\s*', r'\1 ', text)
        return text.strip()
    
    try:
        # Modify search query based on attempt number and broader flag
        if broader:
            search_query = topic
        elif attempt == 0:
            search_query = f"{topic} {subject}"
        elif attempt == 1:
            search_query = f"{topic} definition {subject}"
        else:
            search_query = f"{topic} introduction"
        
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={search_query}&format=json"
        
        print(f"Searching Wikipedia for: {search_query}")
        search_response = requests.get(search_url)
        search_data = search_response.json()
        
        if not search_data.get('query', {}).get('search'):
            print("No Wikipedia articles found")
            return f"{topic} is an important concept in {subject}. It involves various principles and methods that are widely used in the field. Understanding {topic} is essential for mastering {subject} and its applications in real-world scenarios."
        
        # Get the page ID (use different result based on attempt number)
        results = search_data['query']['search']
        page_id = results[min(attempt, len(results)-1)]['pageid']
        
        # Fetch both the intro and the first few sections
        content_url = (
            f"https://en.wikipedia.org/w/api.php?"
            f"action=query&prop=extracts&explaintext=1&"
            f"pageids={page_id}&format=json"
        )
        
        print("Fetching article content...")
        content_response = requests.get(content_url)
        content_data = content_response.json()
        
        # Extract and clean the content
        content = content_data['query']['pages'][str(page_id)]['extract']
        
        # Take a reasonable chunk of content
        content = content[:3000]  # Get more content for better question generation
        cleaned_content = clean_text(content)
        
        if len(cleaned_content) < 200:
            print("Content too short after cleaning")
            return f"{topic} is a fundamental concept in {subject}. It encompasses various important principles and methodologies. Studying {topic} helps in understanding key aspects of {subject} and its practical applications."
        
        return cleaned_content
        
    except Exception as e:
        print(f"Error fetching content: {e}")
        return f"{topic} is a crucial element in {subject}. It plays a vital role in understanding and applying key concepts. Mastering {topic} is essential for success in {subject} and related fields."

def test_api_access():
    """Test if we can access the Hugging Face API with the provided key"""
    try:
        from transformers import AutoTokenizer
        
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            return False, "HUGGINGFACE_API_KEY not found in environment variables"
            
        # Try to load a model to test API access
        try:
            tokenizer = AutoTokenizer.from_pretrained("gpt2", token=api_key)
            return True, "API access successful"
        except Exception as e:
            if "401 Client Error" in str(e):
                return False, "Invalid API key or unauthorized access"
            elif "403 Client Error" in str(e):
                return False, "API key valid but lacks necessary permissions"
            else:
                return False, f"Error accessing API: {str(e)}"
                
    except ImportError:
        return False, "transformers library not installed"

def init_model():
    """Initialize the model only when needed"""
    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        import torch
        
        # Get API key from environment
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            raise ValueError("HUGGINGFACE_API_KEY not found in environment variables")
        
        # Use BART model which is more stable for text generation
        model_name = "facebook/bart-base"
        print(f"Loading {model_name}...")
        
        tokenizer = AutoTokenizer.from_pretrained(model_name, token=api_key)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name, token=api_key)
        
        def generate_text(prompt, max_length=1024):
            inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
            outputs = model.generate(
                inputs.input_ids,
                max_length=max_length,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                top_p=0.9
            )
            return tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return generate_text
        
    except Exception as e:
        print(f"Error initializing model: {str(e)}")
        return None

def validate_question(question):
    """Validate that a question meets our quality criteria"""
    if not question.get("question") or not question.get("options"):
        return False
        
    # Check if we have exactly 4 options
    if len(question.get("options", [])) != 4:
        return False
        
    # Check if we have an answer and it's valid
    answer = question.get("answer", "").upper().strip()
    if not answer or answer not in ["A", "B", "C", "D"]:
        return False
        
    # Check if the question text is reasonable length
    if len(question["question"]) < 10:
        return False
        
    return True

def parse_quiz_text(text):
    """Parse the generated text into quiz questions with improved validation"""
    questions = []
    current = {}
    
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    for line in lines:
        if line.startswith(("Q", "Question")):
            if current and validate_question(current):
                questions.append(current)
            current = {"question": line.split(".", 1)[-1].strip(), "options": []}
        elif line.startswith(("A.", "B.", "C.", "D.")):
            option = line.split(".", 1)
            if len(option) == 2:
                current.setdefault("options", []).append(line)
        elif "Answer:" in line.upper():
            answer = line.upper().replace("ANSWER:", "").strip()
            if answer in ["A", "B", "C", "D"]:
                current["answer"] = answer
    
    # Add the last question if it exists and is valid
    if current and validate_question(current):
        questions.append(current)
    
    return questions

def generate_template_questions(content, subject, topic, difficulty, num_questions):
    """Generate questions using templates and NLP processing"""
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.tag import pos_tag
    from nltk.corpus import stopwords
    import random
    import re
    
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
        nltk.download('averaged_perceptron_tagger')
        nltk.download('stopwords')
    
    # Clean and prepare content
    sentences = sent_tokenize(content)
    
    # Filter out very short or very long sentences
    sentences = [s for s in sentences if 20 <= len(s) <= 200]
    
    # Remove sentences with unwanted patterns
    sentences = [s for s in sentences if not any(pattern in s.lower() for pattern in [
        "click", "copyright", "cookies", "website", "http", "https"
    ])]
    
    questions = []
    used_sentences = set()
    
    # Question templates based on difficulty
    templates = {
        "beginner": [
            {
                "pattern": "What is {}?",
                "answer_pattern": "The {} is {}.",
                "type": "definition"
            },
            {
                "pattern": "Which of the following best describes {}?",
                "answer_pattern": "{} is {}.",
                "type": "description"
            }
        ],
        "intermediate": [
            {
                "pattern": "How does {} relate to {}?",
                "answer_pattern": "{} is related to {} through {}.",
                "type": "relationship"
            },
            {
                "pattern": "What is the main purpose of {} in {}?",
                "answer_pattern": "The main purpose of {} in {} is {}.",
                "type": "purpose"
            }
        ],
        "advanced": [
            {
                "pattern": "What is the significance of {} in the context of {}?",
                "answer_pattern": "The significance of {} in {} is {}.",
                "type": "analysis"
            },
            {
                "pattern": "How does {} impact {}?",
                "answer_pattern": "{} impacts {} by {}.",
                "type": "impact"
            }
        ]
    }
    
    def extract_key_phrases(sentence):
        """Extract important phrases from a sentence"""
        words = word_tokenize(sentence)
        tagged = pos_tag(words)
        
        # Extract noun phrases and important words
        phrases = []
        current_phrase = []
        
        for word, tag in tagged:
            if tag.startswith(('NN', 'JJ', 'VB')):  # Nouns, adjectives, verbs
                current_phrase.append(word)
            elif current_phrase:
                phrases.append(' '.join(current_phrase))
                current_phrase = []
        
        if current_phrase:
            phrases.append(' '.join(current_phrase))
        
        return [p for p in phrases if len(p.split()) <= 3 and len(p) >= 4]
    
    def generate_distractors(correct_answer, key_phrases, num_distractors=3):
        """Generate plausible but incorrect options"""
        distractors = []
        
        # Use other key phrases as distractors
        other_phrases = [p for p in key_phrases if p != correct_answer]
        distractors.extend(other_phrases[:num_distractors])
        
        # If we need more distractors, generate variations
        while len(distractors) < num_distractors:
            if isinstance(correct_answer, str):
                # For text answers, use alternative phrases
                alternatives = [
                    f"the opposite of {correct_answer}",
                    f"a different aspect of {topic}",
                    f"an unrelated concept in {subject}"
                ]
                distractors.extend(alternatives)
            
        return list(set(distractors))[:num_distractors]
    
    for sentence in sentences:
        if len(questions) >= num_questions:
            break
            
        # Skip if we've used this sentence
        if sentence in used_sentences:
            continue
        
        # Extract key information
        key_phrases = extract_key_phrases(sentence)
        if not key_phrases:
            continue
        
        # Select template based on difficulty
        available_templates = templates.get(difficulty.lower(), templates["intermediate"])
        template = random.choice(available_templates)
        
        try:
            # Generate question and answer
            key_term = random.choice(key_phrases)
            
            if template["type"] == "definition":
                question = template["pattern"].format(key_term)
                correct_answer = sentence
            elif template["type"] == "description":
                question = template["pattern"].format(key_term)
                correct_answer = sentence
            elif template["type"] == "relationship":
                question = template["pattern"].format(key_term, topic)
                correct_answer = sentence
            elif template["type"] == "purpose":
                question = template["pattern"].format(key_term, subject)
                correct_answer = sentence
            elif template["type"] == "analysis":
                question = template["pattern"].format(key_term, topic)
                correct_answer = sentence
            else:
                question = template["pattern"].format(key_term, topic)
                correct_answer = sentence
            
            # Generate distractors
            other_key_phrases = []
            for s in sentences:
                if s != sentence:
                    other_key_phrases.extend(extract_key_phrases(s))
            
            distractors = generate_distractors(correct_answer, other_key_phrases)
            
            # Ensure we have enough distractors
            while len(distractors) < 3:
                distractors.append(f"None of the above statements about {key_term} are correct")
            
            # Create options dictionary with correct answer randomly placed
            options = distractors[:3]
            correct_option = random.choice(['A', 'B', 'C', 'D'])
            options_dict = {}
            
            option_index = 0
            for letter in ['A', 'B', 'C', 'D']:
                if letter == correct_option:
                    options_dict[letter] = correct_answer
                else:
                    if option_index < len(options):
                        options_dict[letter] = options[option_index]
                        option_index += 1
                    else:
                        options_dict[letter] = f"Alternative explanation of {key_term}"
            
            # Create question dictionary
            question_dict = {
                'question': question,
                'options': options_dict,
                'answer': correct_option,
                'explanation': f"The correct answer is {correct_option}. {correct_answer}"
            }
            
            questions.append(question_dict)
            used_sentences.add(sentence)
            
        except Exception as e:
            print(f"Error generating question: {e}")
            continue
    
    return questions

def generate_generic_questions(subject, topic, difficulty, num_questions):
    """Generate generic questions when specific content is not available"""
    templates = [
        {
            "question": f"Which of the following best describes {topic} in {subject}?",
            "options": {
                "A": f"A fundamental concept in {subject}",
                "B": f"An advanced topic in {subject}",
                "C": f"A specialized area of {subject}",
                "D": f"A theoretical framework in {subject}"
            },
            "answer": "A"
        },
        {
            "question": f"What is the primary purpose of studying {topic} in {subject}?",
            "options": {
                "A": "To understand theoretical concepts",
                "B": "To solve practical problems",
                "C": "To develop new methodologies",
                "D": "To advance research in the field"
            },
            "answer": "B"
        },
        {
            "question": f"How is {topic} typically applied in {subject}?",
            "options": {
                "A": "Through practical experiments",
                "B": "Through theoretical analysis",
                "C": "Through computational methods",
                "D": "Through systematic study"
            },
            "answer": "A"
        },
        {
            "question": f"Which field is most closely related to {topic} in {subject}?",
            "options": {
                "A": "Theoretical research",
                "B": "Applied sciences",
                "C": "Practical applications",
                "D": "Experimental studies"
            },
            "answer": "B"
        },
        {
            "question": f"What is a key characteristic of {topic} in {subject}?",
            "options": {
                "A": "Its practical applications",
                "B": "Its theoretical foundation",
                "C": "Its systematic approach",
                "D": "Its research methodology"
            },
            "answer": "C"
        }
    ]
    
    # Shuffle the templates and return the requested number
    from random import shuffle
    shuffle(templates)
    return templates[:num_questions]

def generate_quiz_questions(subject, topic, difficulty, num_questions=5):
    """Generate quiz questions using template-based approach"""
    print(f"Generating quiz about {topic} in {subject} at {difficulty} level...")
    
    cache_dir = Path("quiz_cache")
    cache_dir.mkdir(exist_ok=True)
    
    cache_key = f"{subject}_{topic}_{difficulty}".lower().replace(" ", "_")
    cache_file = cache_dir / f"{cache_key}.json"
    
    # Try to load from cache first
    if cache_file.exists():
        try:
            print("Checking cache...")
            with open(cache_file, "r") as f:
                questions = json.load(f)
                if len(questions) >= num_questions:
                    print(f"Found {len(questions)} cached questions")
                    return questions[:num_questions]
        except Exception as e:
            print(f"Cache error: {e}")
    
    # Keep trying until we get enough questions
    all_questions = []
    attempts = 0
    max_attempts = 3  # Maximum number of attempts to get enough questions
    
    while len(all_questions) < num_questions and attempts < max_attempts:
        # Fetch content about the topic
        print(f"\nAttempt {attempts + 1}: Fetching content...")
        content = fetch_topic_content(subject, topic, attempts)
        print(f"Retrieved {len(content)} characters of content")
        
        # Generate questions using templates
        print("Generating questions...")
        new_questions = generate_template_questions(content, subject, topic, difficulty, num_questions)
        
        # Add new unique questions
        for q in new_questions:
            # Check if this question is unique (not already in all_questions)
            if not any(existing_q['question'] == q['question'] for existing_q in all_questions):
                all_questions.append(q)
        
        print(f"Total unique questions so far: {len(all_questions)}/{num_questions}")
        attempts += 1
        
        # If we still don't have enough questions, try with related topics
        if len(all_questions) < num_questions and attempts == max_attempts - 1:
            print("\nTrying with broader topic scope...")
            content = fetch_topic_content(subject, topic, broader=True)
            new_questions = generate_template_questions(content, subject, topic, difficulty, num_questions)
            for q in new_questions:
                if not any(existing_q['question'] == q['question'] for existing_q in all_questions):
                    all_questions.append(q)
    
    # If we still don't have enough questions, generate some generic ones
    if len(all_questions) < num_questions:
        print("\nGenerating additional generic questions...")
        generic_questions = generate_generic_questions(subject, topic, difficulty, num_questions - len(all_questions))
        all_questions.extend(generic_questions)
    
    # Save to cache if we got any questions
    if all_questions:
        try:
            print("\nSaving questions to cache...")
            with open(cache_file, "w") as f:
                json.dump(all_questions, f)
            print("Questions saved successfully")
        except Exception as e:
            print(f"Error saving to cache: {e}")
    
    return all_questions[:num_questions]

def evaluate_quiz(questions, answers):
    """Evaluate the quiz answers and return the score"""
    if not questions or not answers:
        return 0
    
    score = 0
    for i, question in enumerate(questions, 1):
        if i in answers and question.get('answer') == answers[i]:
            score += 1
    
    return score