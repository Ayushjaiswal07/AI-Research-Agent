from src.agents.researcher import AIResearchAgent

def main():
    agent = AIResearchAgent()
    
    # Choose a complex, modern topic that requires real-time search
    topic = "What are the key differences between LangChain and LangGraph for AI Agents?"
    
    report = agent.run_research(topic)
    
    print("\n" + "="*60)
    print("🎯 FINAL RESEARCH REPORT")
    print("="*60 + "\n")
    print(report)

if __name__ == "__main__":
    main()