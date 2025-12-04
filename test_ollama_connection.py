"""
Test script to verify Ollama connection and Llama 3.2 3B model is working.
"""
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from google.adk.models.lite_llm import LiteLlm
from src.utils.config import DEFAULT_MODEL, MODEL_OLLAMA_LLAMA_32_3B
from src.utils.logger import logger

def test_ollama_connection():
    """Test if Ollama is running and Llama 3.2 3B responds correctly."""
    print("=" * 60)
    print("Testing Ollama Connection with Llama 3.2 3B")
    print("=" * 60)
    print(f"\nModel: {MODEL_OLLAMA_LLAMA_32_3B}")
    print(f"Default Model: {DEFAULT_MODEL}\n")
    
    try:
        # Initialize LLM
        print("1. Initializing LiteLLM with Ollama...")
        llm = LiteLlm(model=MODEL_OLLAMA_LLAMA_32_3B)
        print("   [OK] LiteLLM initialized successfully\n")
        
        # Test simple completion
        print("2. Testing simple completion...")
        test_messages = [
            {"role": "user", "content": "Say 'Hello, Ollama is working!' if you can read this."}
        ]
        
        response = llm.llm_client.completion(
            model=llm.model,
            messages=test_messages,
            tools=[]
        )
        
        if response and response.choices:
            response_text = response.choices[0].message.content
            print(f"   [OK] Response received: {response_text}\n")
        else:
            print("   [ERROR] No response received\n")
            return False
        
        # Test with a more complex query (similar to agent use case)
        print("3. Testing structured reasoning (like schema proposal)...")
        complex_messages = [
            {"role": "user", "content": "What is a knowledge graph schema? Answer in one sentence."}
        ]
        
        response2 = llm.llm_client.completion(
            model=llm.model,
            messages=complex_messages,
            tools=[]
        )
        
        if response2 and response2.choices:
            response_text2 = response2.choices[0].message.content
            print(f"   [OK] Complex response received: {response_text2}\n")
        else:
            print("   [ERROR] No response received for complex query\n")
            return False
        
        print("=" * 60)
        print("[SUCCESS] All tests passed! Ollama is working correctly.")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error occurred: {e}\n")
        print("=" * 60)
        print("Troubleshooting:")
        print("1. Install Ollama: https://ollama.com/download/windows")
        print("2. After installation, Ollama should start automatically")
        print("3. Pull the model: ollama pull llama3.2:3b")
        print("4. Test manually: ollama run llama3.2:3b 'Hello'")
        print("5. Check if Ollama is running: ollama list")
        print("")
        print("See docs/OLLAMA_SETUP.md for detailed setup instructions.")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = test_ollama_connection()
    sys.exit(0 if success else 1)

