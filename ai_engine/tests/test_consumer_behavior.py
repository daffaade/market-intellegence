import sys
import os

# Add the parent directory to sys.path so we can import ai_engine modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.consumer_behavior.consumer_behavior_model import ConsumerBehaviorModel
from core.data_loader import UnifiedDataLoader

def test_consumer_behavior():
    print("Testing Consumer Behavior Model...")
    
    # Initialize the model
    data_loader = UnifiedDataLoader()
    model = ConsumerBehaviorModel(data_loader=data_loader)
    
    # Perform an analysis
    keyword = "makanan"
    industry = "makanan & minuman"
    
    print(f"\nAnalyzing keyword '{keyword}' for industry '{industry}'...")
    result = model.analyze(keyword, industry)
    
    print("\n--- RESULTS ---")
    print(f"Keyword: {result.get('keyword')}")
    print(f"Industry: {result.get('industry')}")
    
    signal = result.get('impact_signal', {})
    print(f"\nImpact Signal:")
    print(f"  Score: {signal.get('impact_score')}")
    print(f"  Direction: {signal.get('impact_direction')}")
    print(f"  Confidence: {signal.get('confidence_level')}")
    
    print(f"\nEvidence ({len(result.get('evidence', []))} items):")
    for item in result.get('evidence', []):
        print(f"  - [{item.get('source')}] {item.get('metric')} ({item.get('value')}): {item.get('description')}")
        
    print(f"\nDisclaimer: {result.get('disclaimer')}")
    
if __name__ == "__main__":
    test_consumer_behavior()
