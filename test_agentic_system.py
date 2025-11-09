"""
Comprehensive test suite for the agentic system.
Tests all agents, tools, and workflow components.
"""

import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add solution to path
sys.path.insert(0, str(Path(__file__).parent))

from agentic.agents.classifier import classify
from agentic.agents.resolver import resolve
from agentic.agents.ops import operate
from agentic.agents.escalation import escalate
from agentic.tools.kb_tool import knowledge_search
from agentic.tools.cultpass_tools import get_user_profile, get_subscription_status
from agentic.tools.udahub_tools import append_ticket_message
from agentic.workflow import build_graph
from langchain_core.messages import HumanMessage

# Check if OpenAI API key is available
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    print("⚠️  WARNING: OPENAI_API_KEY not found in environment variables")
    print("   Some tests may fail due to LLM API calls")
    print("   Set OPENAI_API_KEY in .env file or environment variables")
else:
    print("✅ OPENAI_API_KEY found - LLM tests should work")


class TestClassifierAgent(unittest.TestCase):
    """Test the classifier agent functionality."""
    
    def test_classify_subscription_intent(self):
        """Test classification of subscription-related queries."""
        result = classify("I want to upgrade my subscription")
        self.assertEqual(result["intent"], "subscription")
    
    def test_classify_reservation_intent(self):
        """Test classification of reservation-related queries."""
        result = classify("How do I book an event?")
        self.assertEqual(result["intent"], "reservation")
    
    def test_classify_knowledge_intent(self):
        """Test classification of knowledge-related queries."""
        result = classify("What is CultPass?")
        self.assertEqual(result["intent"], "knowledge")
    
    def test_classify_login_intent(self):
        """Test classification of login-related queries."""
        result = classify("I forgot my password")
        self.assertEqual(result["intent"], "login")
    
    def test_classify_unknown_intent(self):
        """Test classification of unclear queries."""
        result = classify("asdfasdf random text")
        self.assertEqual(result["intent"], "unknown")


class TestKnowledgeSearchTool(unittest.TestCase):
    """Test the knowledge base search functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.account_id = "cultpass"
    
    def test_knowledge_search_subscription(self):
        """Test knowledge search for subscription queries."""
        result = knowledge_search(
            account_id=self.account_id,
            query="subscription",
            top_k=3,
            min_confidence=0.1
        )
        self.assertTrue(result.ok)
        self.assertGreater(len(result.data["results"]), 0)
        self.assertGreater(result.data["best_score"], 0)
    
    def test_knowledge_search_reservation(self):
        """Test knowledge search for reservation queries."""
        result = knowledge_search(
            account_id=self.account_id,
            query="reserve",
            top_k=3,
            min_confidence=0.1
        )
        self.assertTrue(result.ok)
        self.assertGreater(len(result.data["results"]), 0)
    
    def test_knowledge_search_no_results(self):
        """Test knowledge search with no matching results."""
        result = knowledge_search(
            account_id=self.account_id,
            query="xyzabc123nonexistent",
            top_k=3,
            min_confidence=0.1
        )
        self.assertTrue(result.ok)
        self.assertEqual(len(result.data["results"]), 0)
        self.assertEqual(result.data["best_score"], 0.0)


class TestResolverAgent(unittest.TestCase):
    """Test the resolver agent functionality."""
    
    def test_resolve_with_high_confidence(self):
        """Test resolver with high confidence results."""
        with patch('agentic.tools.vocareum_llm.complete') as mock_llm:
            mock_llm.return_value = {"ok": True, "content": "Test answer"}
            
            result = resolve(
                account_id="cultpass",
                query="subscription",
                min_confidence=0.1
            )
            
            self.assertTrue(result["ok"])
            self.assertIn("answer", result)
    
    def test_resolve_with_low_confidence(self):
        """Test resolver with low confidence results."""
        result = resolve(
            account_id="cultpass",
            query="xyzabc123nonexistent",
            min_confidence=0.9
        )
        
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "low_confidence")


class TestOpsAgent(unittest.TestCase):
    """Test the operations agent functionality."""
    
    def test_ops_subscription_query(self):
        """Test ops agent with subscription query."""
        context = {
            "user_id": "a4ab87",
            "external_user_id": "a4ab87",
            "account_id": "cultpass",
            "intent": "subscription",
            "input": "subscription status"
        }
        
        result = operate("subscription status", context)
        self.assertTrue(result["ok"])
        self.assertIn("data", result)


class TestEscalationAgent(unittest.TestCase):
    """Test the escalation agent functionality."""
    
    def test_escalate_ticket(self):
        """Test escalation functionality."""
        context = {
            "intent": "unknown",
            "resolver_result": None,
            "ops_result": None
        }
        
        result = escalate(
            ticket_id="test-ticket",
            user_message="I need help",
            context=context,
            last_confidence=0.0
        )
        
        self.assertIn("udahub", result)
        self.assertIn("vocareum", result)
        self.assertIn("reason", result)


class TestWorkflowIntegration(unittest.TestCase):
    """Test the complete workflow integration."""
    
    def setUp(self):
        """Set up test environment."""
        self.orchestrator = build_graph()
    
    def test_workflow_subscription_query(self):
        """Test complete workflow with subscription query."""
        test_input = {"messages": [HumanMessage(content="subscription")]}
        config = {"configurable": {"thread_id": "test"}}
        
        result = self.orchestrator.invoke(input=test_input, config=config)
        
        self.assertIn("messages", result)
        self.assertIn("intent", result)
        self.assertEqual(result["intent"], "subscription")
        self.assertGreater(len(result["messages"]), 1)
    
    def test_workflow_knowledge_query(self):
        """Test complete workflow with knowledge query."""
        test_input = {"messages": [HumanMessage(content="how to reserve")]}
        config = {"configurable": {"thread_id": "test"}}
        
        result = self.orchestrator.invoke(input=test_input, config=config)
        
        self.assertIn("messages", result)
        self.assertIn("intent", result)
        self.assertEqual(result["intent"], "knowledge")
    
    def test_workflow_unknown_query(self):
        """Test complete workflow with unknown query."""
        test_input = {"messages": [HumanMessage(content="asdfasdf")]}
        config = {"configurable": {"thread_id": "test"}}
        
        result = self.orchestrator.invoke(input=test_input, config=config)
        
        self.assertIn("messages", result)
        self.assertIn("intent", result)
        self.assertEqual(result["intent"], "unknown")
        self.assertIn("escalation", result)


class TestDatabaseTools(unittest.TestCase):
    """Test database tool functionality."""
    
    def test_get_user_profile(self):
        """Test user profile retrieval."""
        result = get_user_profile("a4ab87")
        self.assertTrue(result.ok)
        # The actual structure returns the data directly, not wrapped in a "data" key
        self.assertIsNotNone(result.data)
        self.assertIn("user_id", result.data)
    
    def test_get_subscription_status(self):
        """Test subscription status retrieval."""
        result = get_subscription_status("a4ab87")
        self.assertTrue(result.ok)
        # The actual structure returns the data directly, not wrapped in a "data" key
        self.assertIsNotNone(result.data)
        self.assertIn("status", result.data)


class TestSystemIntegration(unittest.TestCase):
    """Test end-to-end system integration."""
    
    def setUp(self):
        """Set up test environment."""
        self.orchestrator = build_graph()
    
    def test_end_to_end_subscription_flow(self):
        """Test complete subscription flow."""
        # Test subscription query
        test_input = {"messages": [HumanMessage(content="subscription")]}
        config = {"configurable": {"thread_id": "integration-test"}}
        
        result = self.orchestrator.invoke(input=test_input, config=config)
        
        # Verify the flow
        self.assertEqual(result["intent"], "subscription")
        self.assertIn("ops_result", result)
        self.assertTrue(result["ops_result"]["ok"])
        
        # Check that a response was generated
        messages = result["messages"]
        self.assertGreater(len(messages), 1)
        self.assertIn("Done:", messages[-1].content)
    
    def test_end_to_end_knowledge_flow(self):
        """Test complete knowledge flow."""
        # Test knowledge query
        test_input = {"messages": [HumanMessage(content="how to reserve")]}
        config = {"configurable": {"thread_id": "integration-test"}}
        
        result = self.orchestrator.invoke(input=test_input, config=config)
        
        # Verify the flow
        self.assertEqual(result["intent"], "knowledge")
        self.assertIn("resolver_result", result)
        
        # Check that a response was generated
        messages = result["messages"]
        self.assertGreater(len(messages), 1)


def run_tests():
    """Run all tests and return results."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestClassifierAgent,
        TestKnowledgeSearchTool,
        TestResolverAgent,
        TestOpsAgent,
        TestEscalationAgent,
        TestWorkflowIntegration,
        TestDatabaseTools,
        TestSystemIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result


if __name__ == "__main__":
    print("Running Agentic System Test Suite...")
    print("=" * 50)
    
    result = run_tests()
    
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ {len(result.failures + result.errors)} test(s) failed")
