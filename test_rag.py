#!/usr/bin/env python3
"""
Test the simple RAG system with local storage
"""

from simple_rag_system import SimpleRAGSystem

def main():
    print("Testing Simple RAG System...")
    
    # Initialize the system
    rag_system = SimpleRAGSystem()
    
    # Update knowledge base with SOP directory
    print("\n1. Updating knowledge base...")
    rag_system.update_knowledge_base("./SOP")
    
    # Get stats
    print("\n2. Knowledge base stats:")
    stats = rag_system.get_knowledge_base_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Ask some questions
    questions = [
        "What are the password requirements?",
        "How often should passwords be changed?",
        "What is the incident response procedure?",
        "Tell me about data protection requirements"
    ]
    
    print("\n3. Testing questions:")
    for question in questions:
        print(f"\nQ: {question}")
        result = rag_system.ask_question(question, top_k=3)
        print(f"A: {result['response'][:200]}...")
        if result['sources']:
            print(f"Sources: {[s['file_name'] for s in result['sources']]}")

if __name__ == "__main__":
    main()