#!/usr/bin/env python3
"""
Demo script for the Knowledge Base Chatbot
"""

from simple_rag_system import SimpleRAGSystem

def demo():
    print("=== Knowledge Base Chatbot Demo ===\n")
    
    # Initialize the system
    rag = SimpleRAGSystem()
    
    # Show stats
    print("1. Knowledge Base Statistics:")
    stats = rag.get_knowledge_base_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "="*50)
    
    # Demo questions
    questions = [
        "What are the password requirements?",
        "How long should passwords be?",
        "What should I do if there's a security incident?", 
        "What is the incident response procedure?",
        "Tell me about ONT installation"
    ]
    
    print("2. Sample Q&A:\n")
    
    for i, question in enumerate(questions, 1):
        print(f"Q{i}: {question}")
        result = rag.ask_question(question, top_k=2)
        
        # Get the relevant snippet from the first source
        if result['sources']:
            # Find the most relevant content
            best_source = result['sources'][0]
            print(f"A{i}: From {best_source['file_name']} (similarity: {best_source['similarity']:.3f}):")
            
            # Show first few sentences of the context
            context_parts = result['context'].split('\n')
            content_line = None
            for part in context_parts:
                if part.startswith('Content:'):
                    content_line = part[9:].strip()  # Remove "Content: "
                    break
            
            if content_line:
                # Show first 200 characters
                snippet = content_line[:200] + "..." if len(content_line) > 200 else content_line
                print(f"   {snippet}")
        else:
            print(f"A{i}: No relevant information found.")
        
        print()
    
    print("="*50)
    print("\nTry asking your own questions with: python main.py chat")

if __name__ == "__main__":
    demo()