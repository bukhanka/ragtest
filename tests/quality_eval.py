"""Quality evaluation for the LLM Assistant."""
import asyncio
import sys
import os
import json
import time
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests

API_URL = "http://localhost:8000"


class QualityEvaluator:
    """Evaluates the quality of the LLM Assistant."""
    
    def __init__(self):
        """Initialize evaluator."""
        self.test_cases = self._load_test_cases()
        self.results = []
    
    def _load_test_cases(self) -> List[Dict[str, Any]]:
        """Load test cases for evaluation."""
        return [
            # RAG tests
            {
                "id": "rag_1",
                "question": "Что такое RAG и как он работает?",
                "expected_tool": "RAG",
                "category": "documentation",
                "expected_keywords": ["retrieval", "документ", "поиск", "генерация"]
            },
            {
                "id": "rag_2",
                "question": "Объясни концепцию векторных баз данных",
                "expected_tool": "RAG",
                "category": "documentation",
                "expected_keywords": ["вектор", "embedding", "база данных"]
            },
            {
                "id": "rag_3",
                "question": "Как работают языковые модели?",
                "expected_tool": "RAG",
                "category": "documentation",
                "expected_keywords": ["модель", "обучение", "нейронн"]
            },
            
            # SQL tests
            {
                "id": "sql_1",
                "question": "Сколько человек работает в команде Machine Learning?",
                "expected_tool": "SQL",
                "category": "database",
                "expected_keywords": ["4", "команд", "machine learning"]
            },
            {
                "id": "sql_2",
                "question": "Кто занимает должность Senior ML Engineer?",
                "expected_tool": "SQL",
                "category": "database",
                "expected_keywords": ["александр", "иванов", "senior"]
            },
            {
                "id": "sql_3",
                "question": "Покажи всех разработчиков, которые знают Python",
                "expected_tool": "SQL",
                "category": "database",
                "expected_keywords": ["python", "разработчик"]
            },
            {
                "id": "sql_4",
                "question": "Какие проекты сейчас активны?",
                "expected_tool": "SQL",
                "category": "database",
                "expected_keywords": ["llm", "rag", "active", "активн"]
            },
            {
                "id": "sql_5",
                "question": "Список всех сотрудников отдела Engineering",
                "expected_tool": "SQL",
                "category": "database",
                "expected_keywords": ["engineering", "иван", "анна"]
            },
            
            # Web Search tests
            {
                "id": "web_1",
                "question": "Найди в интернете информацию о последних обновлениях GPT-4",
                "expected_tool": "Web Search",
                "category": "web_search",
                "expected_keywords": ["gpt", "openai"]
            },
            {
                "id": "web_2",
                "question": "Поищи последние новости о LangChain",
                "expected_tool": "Web Search",
                "category": "web_search",
                "expected_keywords": ["langchain"]
            },
            
            # Mixed/Complex tests
            {
                "id": "mixed_1",
                "question": "У кого в команде есть навыки работы с FastAPI?",
                "expected_tool": "SQL",
                "category": "database",
                "expected_keywords": ["fastapi", "дмитрий", "иван"]
            },
            {
                "id": "mixed_2",
                "question": "Кто работает над проектом LLM Assistant?",
                "expected_tool": "SQL",
                "category": "database",
                "expected_keywords": ["llm", "assistant"]
            },
        ]
    
    def check_health(self) -> bool:
        """Check if API is available."""
        try:
            response = requests.get(f"{API_URL}/health", timeout=5)
            if response.status_code == 200:
                health = response.json()
                print(f"✓ API Status: {health['status']}")
                print(f"  - LLM Available: {health['llm_available']}")
                print(f"  - Vector Store: {health['vector_store_available']}")
                print(f"  - Database: {health['database_available']}")
                return health['status'] == 'healthy'
            return False
        except Exception as e:
            print(f"✗ API Health Check Failed: {e}")
            return False
    
    def run_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test case."""
        print(f"\n[Test {test_case['id']}] {test_case['question']}")
        
        try:
            # Send request
            start_time = time.time()
            response = requests.post(
                f"{API_URL}/chat",
                json={"message": test_case["question"]},
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code != 200:
                return {
                    "test_id": test_case["id"],
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "response_time": response_time
                }
            
            result = response.json()
            
            # Extract tool names
            tools_used = [tool["name"] for tool in result.get("tools_used", [])]
            
            # Check if expected tool was used
            tool_match = any(test_case["expected_tool"].lower() in tool.lower() for tool in tools_used)
            
            # Check for expected keywords in response
            response_text = result["response"].lower()
            keyword_matches = sum(1 for kw in test_case["expected_keywords"] 
                                 if kw.lower() in response_text)
            keyword_score = keyword_matches / len(test_case["expected_keywords"])
            
            # Calculate overall score
            score = 0.0
            if tool_match:
                score += 0.5
            score += keyword_score * 0.5
            
            # Print results
            print(f"  Response Time: {response_time:.2f}s")
            print(f"  Tools Used: {', '.join(tools_used)}")
            print(f"  Expected Tool: {test_case['expected_tool']} - {'✓' if tool_match else '✗'}")
            print(f"  Keyword Match: {keyword_matches}/{len(test_case['expected_keywords'])} ({keyword_score*100:.0f}%)")
            print(f"  Score: {score*100:.0f}%")
            print(f"  Response: {result['response'][:200]}...")
            
            return {
                "test_id": test_case["id"],
                "category": test_case["category"],
                "success": True,
                "score": score,
                "tool_match": tool_match,
                "keyword_score": keyword_score,
                "response_time": response_time,
                "tools_used": tools_used,
                "response": result["response"]
            }
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return {
                "test_id": test_case["id"],
                "success": False,
                "error": str(e)
            }
    
    def run_evaluation(self):
        """Run all test cases and generate report."""
        print("=" * 80)
        print("LLM ASSISTANT QUALITY EVALUATION")
        print("=" * 80)
        
        # Check API health
        if not self.check_health():
            print("\n✗ API is not available. Please start the application first.")
            print("Run: docker-compose up -d")
            return
        
        print(f"\nRunning {len(self.test_cases)} test cases...")
        
        # Run all tests
        for test_case in self.test_cases:
            result = self.run_test_case(test_case)
            self.results.append(result)
        
        # Generate report
        self._generate_report()
    
    def _generate_report(self):
        """Generate evaluation report."""
        print("\n" + "=" * 80)
        print("EVALUATION REPORT")
        print("=" * 80)
        
        # Filter successful tests
        successful_tests = [r for r in self.results if r.get("success", False)]
        
        if not successful_tests:
            print("\n✗ No successful tests")
            return
        
        # Overall statistics
        total_tests = len(self.results)
        successful_count = len(successful_tests)
        success_rate = successful_count / total_tests * 100
        
        avg_score = sum(r["score"] for r in successful_tests) / len(successful_tests) * 100
        avg_response_time = sum(r["response_time"] for r in successful_tests) / len(successful_tests)
        
        tool_matches = sum(1 for r in successful_tests if r.get("tool_match", False))
        tool_accuracy = tool_matches / len(successful_tests) * 100
        
        print(f"\nOverall Statistics:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Successful: {successful_count} ({success_rate:.1f}%)")
        print(f"  Average Score: {avg_score:.1f}%")
        print(f"  Tool Routing Accuracy: {tool_accuracy:.1f}%")
        print(f"  Average Response Time: {avg_response_time:.2f}s")
        
        # Category breakdown
        print(f"\nBreakdown by Category:")
        categories = {}
        for result in successful_tests:
            cat = result.get("category", "unknown")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)
        
        for category, results in categories.items():
            avg_cat_score = sum(r["score"] for r in results) / len(results) * 100
            print(f"  {category.upper()}: {len(results)} tests, avg score {avg_cat_score:.1f}%")
        
        # Failed tests
        failed_tests = [r for r in self.results if not r.get("success", False)]
        if failed_tests:
            print(f"\nFailed Tests: {len(failed_tests)}")
            for result in failed_tests:
                print(f"  - {result['test_id']}: {result.get('error', 'Unknown error')}")
        
        # Save detailed results
        output_file = "tests/evaluation_results.json"
        os.makedirs("tests", exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "successful_tests": successful_count,
                    "success_rate": success_rate,
                    "average_score": avg_score,
                    "tool_routing_accuracy": tool_accuracy,
                    "average_response_time": avg_response_time
                },
                "results": self.results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Detailed results saved to: {output_file}")
        print("=" * 80)


if __name__ == "__main__":
    evaluator = QualityEvaluator()
    evaluator.run_evaluation()

