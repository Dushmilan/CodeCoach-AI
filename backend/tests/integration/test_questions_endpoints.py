"""
Integration tests for questions endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


class TestQuestionsEndpoints:
    """Test cases for questions endpoints."""
    
    def test_get_all_questions_basic(self, test_client: TestClient):
        """Test getting all questions with basic parameters."""
        response = test_client.get("/api/questions/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "questions" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        
        assert isinstance(data["questions"], list)
        assert len(data["questions"]) <= data["per_page"]
        assert data["page"] == 1
        assert data["per_page"] == 20
    
    def test_get_all_questions_with_pagination(self, test_client: TestClient):
        """Test getting questions with pagination."""
        response = test_client.get("/api/questions/?page=2&per_page=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 2
        assert data["per_page"] == 10
        assert len(data["questions"]) <= 10
    
    def test_get_all_questions_with_difficulty_filter(self, test_client: TestClient):
        """Test filtering questions by difficulty."""
        response = test_client.get("/api/questions/?difficulty=easy")
        
        assert response.status_code == 200
        data = response.json()
        
        for question in data["questions"]:
            assert question["difficulty"] == "easy"
    
    def test_get_all_questions_with_category_filter(self, test_client: TestClient):
        """Test filtering questions by category."""
        response = test_client.get("/api/questions/?category=arrays")
        
        assert response.status_code == 200
        data = response.json()
        
        for question in data["questions"]:
            assert question["category"] == "arrays"
    
    def test_get_all_questions_with_combined_filters(self, test_client: TestClient):
        """Test filtering questions with multiple parameters."""
        response = test_client.get("/api/questions/?difficulty=easy&category=arrays&page=1&per_page=5")
        
        assert response.status_code == 200
        data = response.json()
        
        for question in data["questions"]:
            assert question["difficulty"] == "easy"
            assert question["category"] == "arrays"
        assert len(data["questions"]) <= 5
    
    def test_get_question_by_id(self, test_client: TestClient):
        """Test getting a specific question by ID."""
        # First get a question ID from the list
        list_response = test_client.get("/api/questions/")
        assert list_response.status_code == 200
        
        questions = list_response.json()["questions"]
        if questions:
            question_id = questions[0]["id"]
            
            response = test_client.get(f"/api/questions/{question_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["id"] == question_id
            assert "title" in data
            assert "description" in data
            assert "starter" in data
            assert "examples" in data
            assert "test_cases" in data
    
    def test_get_question_by_invalid_id(self, test_client: TestClient):
        """Test getting a question with invalid ID."""
        response = test_client.get("/api/questions/invalid-id-12345")
        
        assert response.status_code == 404
    
    def test_get_categories(self, test_client: TestClient):
        """Test getting all available categories."""
        response = test_client.get("/api/questions/categories")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "categories" in data
        assert isinstance(data["categories"], list)
        assert len(data["categories"]) > 0
    
    def test_get_companies(self, test_client: TestClient):
        """Test getting all company tags."""
        response = test_client.get("/api/questions/companies")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "companies" in data
        assert isinstance(data["companies"], list)
        # Should contain common tech companies
        expected_companies = ["Google", "Amazon", "Microsoft", "Facebook", "Apple"]
        for company in expected_companies:
            assert company in data["companies"]
    
    def test_search_questions(self, test_client: TestClient):
        """Test searching questions."""
        response = test_client.get("/api/questions/search?q=two sum")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "questions" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        
        # Results should contain "two" or "sum" in title or description
        for question in data["questions"]:
            text = f"{question['title']} {question.get('description', '')}".lower()
            assert "two" in text or "sum" in text
    
    def test_search_questions_empty_query(self, test_client: TestClient):
        """Test searching with empty query."""
        response = test_client.get("/api/questions/search?q=")
        
        assert response.status_code == 400
    
    def test_search_questions_with_filters(self, test_client: TestClient):
        """Test searching questions with additional filters."""
        response = test_client.get("/api/questions/search?q=array&difficulty=easy&category=arrays")
        
        assert response.status_code == 200
        data = response.json()
        
        for question in data["questions"]:
            assert question["difficulty"] == "easy"
            assert question["category"] == "arrays"
    
    def test_get_question_stats(self, test_client: TestClient):
        """Test getting question statistics."""
        response = test_client.get("/api/questions/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data
        assert "difficulty_counts" in data
        assert "category_counts" in data
        assert "categories" in data
        assert "companies" in data
        
        assert isinstance(data["total"], int)
        assert data["total"] >= 0
        
        assert isinstance(data["difficulty_counts"], dict)
        assert isinstance(data["category_counts"], dict)
    
    def test_get_questions_by_category(self, test_client: TestClient):
        """Test getting questions filtered by category."""
        response = test_client.get("/api/questions/category/arrays")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "questions" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        
        for question in data["questions"]:
            assert question["category"] == "arrays"
    
    def test_get_questions_by_difficulty(self, test_client: TestClient):
        """Test getting questions filtered by difficulty."""
        response = test_client.get("/api/questions/difficulty/medium")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "questions" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        
        for question in data["questions"]:
            assert question["difficulty"] == "medium"
    
    def test_questions_pagination_limits(self, test_client: TestClient):
        """Test pagination limits."""
        # Test minimum per_page
        response = test_client.get("/api/questions/?per_page=1")
        assert response.status_code == 200
        
        # Test maximum per_page
        response = test_client.get("/api/questions/?per_page=100")
        assert response.status_code == 200
        
        # Test invalid per_page (too low)
        response = test_client.get("/api/questions/?per_page=0")
        assert response.status_code == 422
        
        # Test invalid per_page (too high)
        response = test_client.get("/api/questions/?per_page=101")
        assert response.status_code == 422
        
        # Test invalid page
        response = test_client.get("/api/questions/?page=0")
        assert response.status_code == 422
    
    def test_questions_invalid_filters(self, test_client: TestClient):
        """Test questions with invalid filter values."""
        # Invalid difficulty
        response = test_client.get("/api/questions/?difficulty=invalid")
        assert response.status_code == 422
        
        # Invalid category (should still work as string)
        response = test_client.get("/api/questions/?category=invalid-category")
        assert response.status_code == 200
    
    def test_questions_response_format(self, test_client: TestClient):
        """Test questions response format consistency."""
        response = test_client.get("/api/questions/")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        
        # Validate response schema
        required_fields = ["questions", "total", "page", "per_page"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Validate question structure
        if data["questions"]:
            question = data["questions"][0]
            required_question_fields = ["id", "title", "difficulty", "category", "company_tags"]
            for field in required_question_fields:
                assert field in question, f"Missing question field: {field}"
    
    def test_question_detail_response_format(self, test_client: TestClient):
        """Test question detail response format."""
        # Get a question ID
        list_response = test_client.get("/api/questions/")
        if list_response.json()["questions"]:
            question_id = list_response.json()["questions"][0]["id"]
            
            response = test_client.get(f"/api/questions/{question_id}")
            
            assert response.status_code == 200
            data = response.json()
            
            required_fields = [
                "id", "title", "difficulty", "category", "company_tags",
                "description", "starter", "examples", "test_cases"
            ]
            
            for field in required_fields:
                assert field in data, f"Missing question detail field: {field}"
    
    def test_questions_error_handling(self, test_client: TestClient):
        """Test questions error handling."""
        # Test with wrong HTTP method
        response = test_client.post("/api/questions/")
        assert response.status_code == 405
        
        response = test_client.put("/api/questions/")
        assert response.status_code == 405
        
        response = test_client.delete("/api/questions/")
        assert response.status_code == 405
    
    @pytest.mark.asyncio
    async def test_questions_async(self, async_client: AsyncClient):
        """Test questions with async client."""
        response = await async_client.get("/api/questions/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "questions" in data
        assert isinstance(data["questions"], list)
    
    def test_questions_response_time(self, test_client: TestClient):
        """Test questions response time."""
        import time
        
        start_time = time.time()
        response = test_client.get("/api/questions/")
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Response should be fast (< 200ms)
        response_time = (end_time - start_time) * 1000
        assert response_time < 200, f"Questions endpoint took {response_time}ms, expected < 200ms"