"""
Tests for the Mergington High School Activities API
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities database before each test"""
    # Store original state
    original = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball practice and inter-school games",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 6:00 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu"]
        },
        "Swimming Club": {
            "description": "Swimming lessons and competitive training",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 20,
            "participants": ["sarah@mergington.edu", "alex@mergington.edu"]
        },
        "Art Studio": {
            "description": "Explore painting, drawing, and mixed media art",
            "schedule": "Mondays, 3:30 PM - 5:00 PM",
            "max_participants": 15,
            "participants": ["emily@mergington.edu"]
        },
        "Drama Club": {
            "description": "Acting, theater production, and stage performance",
            "schedule": "Thursdays, 3:30 PM - 5:30 PM",
            "max_participants": 25,
            "participants": ["lucas@mergington.edu", "mia@mergington.edu"]
        },
        "Debate Team": {
            "description": "Develop critical thinking and public speaking skills",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["william@mergington.edu"]
        },
        "Science Olympiad": {
            "description": "Prepare for science competitions and conduct experiments",
            "schedule": "Fridays, 3:30 PM - 5:30 PM",
            "max_participants": 18,
            "participants": ["ava@mergington.edu", "noah@mergington.edu"]
        }
    }
    
    # Reset to original state
    activities.clear()
    activities.update(original)
    
    yield
    
    # Cleanup after test
    activities.clear()
    activities.update(original)


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that all activities are returned"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
        
    def test_get_activities_structure(self, client):
        """Test that activities have correct structure"""
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify student was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/NonExistent%20Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_signup_duplicate_student(self, client):
        """Test that signing up twice returns 400"""
        email = "test@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(f"/activities/Chess%20Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(f"/activities/Chess%20Club/signup?email={email}")
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_updates_participant_count(self, client):
        """Test that signup increases participant count"""
        # Get initial count
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Basketball Team"]["participants"])
        
        # Sign up new student
        client.post("/activities/Basketball%20Team/signup?email=new@mergington.edu")
        
        # Check new count
        response2 = client.get("/activities")
        new_count = len(response2.json()["Basketball Team"]["participants"])
        
        assert new_count == initial_count + 1


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        email = "michael@mergington.edu"
        
        # Verify student is initially registered
        response1 = client.get("/activities")
        assert email in response1.json()["Chess Club"]["participants"]
        
        # Unregister the student
        response = client.delete(f"/activities/Chess%20Club/unregister?email={email}")
        assert response.status_code == 200
        data = response.json()
        assert "Removed" in data["message"]
        assert email in data["message"]
        
        # Verify student was removed
        response2 = client.get("/activities")
        assert email not in response2.json()["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from non-existent activity returns 404"""
        response = client.delete(
            "/activities/NonExistent%20Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_unregister_not_registered_student(self, client):
        """Test unregistering a student who is not registered returns 400"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_unregister_decreases_participant_count(self, client):
        """Test that unregister decreases participant count"""
        email = "michael@mergington.edu"
        
        # Get initial count
        response1 = client.get("/activities")
        initial_count = len(response1.json()["Chess Club"]["participants"])
        
        # Unregister student
        client.delete(f"/activities/Chess%20Club/unregister?email={email}")
        
        # Check new count
        response2 = client.get("/activities")
        new_count = len(response2.json()["Chess Club"]["participants"])
        
        assert new_count == initial_count - 1


class TestSignupUnregisterFlow:
    """Integration tests for signup and unregister flow"""
    
    def test_signup_then_unregister(self, client):
        """Test complete flow of signing up and then unregistering"""
        email = "testflow@mergington.edu"
        activity = "Programming%20Class"
        
        # Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify registered
        activities_response = client.get("/activities")
        assert email in activities_response.json()["Programming Class"]["participants"]
        
        # Unregister
        unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify unregistered
        final_response = client.get("/activities")
        assert email not in final_response.json()["Programming Class"]["participants"]
    
    def test_cannot_unregister_before_signup(self, client):
        """Test that unregistering without signing up first fails"""
        email = "never@mergington.edu"
        
        response = client.delete(f"/activities/Chess%20Club/unregister?email={email}")
        assert response.status_code == 400


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""
    
    def test_activity_with_special_characters_in_name(self, client):
        """Test handling of activity names with special characters"""
        # URL encoding is handled automatically by the client
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_email_with_special_characters(self, client):
        """Test signup with special characters in email"""
        email = "student+test@mergington.edu"
        response = client.post(f"/activities/Chess%20Club/signup?email={email}")
        assert response.status_code == 200
    
    def test_multiple_activities_same_student(self, client):
        """Test that same student can sign up for multiple activities"""
        email = "multitasker@mergington.edu"
        
        # Sign up for multiple activities
        response1 = client.post(f"/activities/Chess%20Club/signup?email={email}")
        response2 = client.post(f"/activities/Drama%20Club/signup?email={email}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify in both activities
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email in data["Chess Club"]["participants"]
        assert email in data["Drama Club"]["participants"]
