from quiz_generator import generate_quiz_questions

def test_quiz_generation():
    print("\n=== Testing Quiz Generator ===\n")
    
    # Test cases
    test_cases = [
        {
            "subject": "Computer Science",
            "topic": "Python Programming",
            "difficulty": "intermediate",
            "num_questions": 5
        },
        {
            "subject": "Science",
            "topic": "Solar System",
            "difficulty": "beginner",
            "num_questions": 3
        }
    ]
    
    for test_case in test_cases:
        print(f"\nGenerating quiz for {test_case['topic']} in {test_case['subject']}")
        print(f"Difficulty: {test_case['difficulty']}")
        print(f"Number of questions requested: {test_case['num_questions']}\n")
        
        questions = generate_quiz_questions(
            test_case['subject'],
            test_case['topic'],
            test_case['difficulty'],
            test_case['num_questions']
        )
        
        print("\nGenerated Questions:")
        for i, q in enumerate(questions, 1):
            print(f"\n{q['question']}")
            for option, text in q['options'].items():
                print(f"{option}. {text}")
            print(f"Correct Answer: {q['answer']}")
        
        print(f"\nTotal questions generated: {len(questions)}")
        print("-" * 50)

if __name__ == "__main__":
    test_quiz_generation()
