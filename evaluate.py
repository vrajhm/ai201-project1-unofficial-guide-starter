"""Run the 5 evaluation questions from planning.md and print results."""

from query import ask

QUESTIONS = [
    "Which dining hall has the shortest lunch wait?",
    "Does the housing lottery affect which dining hall I can use?",
    "What gluten-free options do students recommend?",
    "What are the late-night food options on campus?",
    "What do students say about the dining app wait time estimates?",
]

if __name__ == "__main__":
    for i, question in enumerate(QUESTIONS, 1):
        print(f"\n{'='*60}")
        print(f"Q{i}: {question}")
        print("=" * 60)
        result = ask(question)
        print(f"\nANSWER:\n{result['answer']}")
        print(f"\nSOURCES: {', '.join(result['sources'])}")
        print("\nRETRIEVED CHUNKS:")
        for j, chunk in enumerate(result["chunks"], 1):
            print(f"  [{j}] {chunk['source']} (distance={chunk['distance']:.3f})")
            print(f"      {chunk['text'][:150]}...")
