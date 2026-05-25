import copy
import urllib.parse

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


INITIAL_ACTIVITIES = copy.deepcopy(activities)


def reset_activities():
    activities.clear()
    activities.update(copy.deepcopy(INITIAL_ACTIVITIES))


@pytest.fixture(autouse=True)
def restore_activities():
    reset_activities()
    yield
    reset_activities()


client = TestClient(app)


def make_activity_url(activity_name: str, action: str, email: str) -> str:
    encoded_activity = urllib.parse.quote(activity_name, safe="")
    encoded_email = urllib.parse.quote(email, safe="")
    return f"/activities/{encoded_activity}/{action}?email={encoded_email}"


def test_get_activities_returns_all_activities():
    # Arrange
    expected_description = "Learn strategies and compete in chess tournaments"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert data["Chess Club"]["description"] == expected_description


def test_signup_for_activity_adds_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "test.student@mergington.edu"
    url = make_activity_url(activity_name, "signup", email)

    # Act
    response = client.post(url)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_for_activity_returns_400_if_duplicate():
    # Arrange
    activity_name = "Chess Club"
    existing_email = activities[activity_name]["participants"][0]
    url = make_activity_url(activity_name, "signup", existing_email)

    # Act
    response = client.post(url)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_for_unknown_activity_returns_404():
    # Arrange
    unknown_activity = "Unknown"
    email = "test@mergington.edu"
    url = make_activity_url(unknown_activity, "signup", email)

    # Act
    response = client.post(url)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_participant_removes_participant():
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]
    url = make_activity_url(activity_name, "unregister", email)

    # Act
    response = client.post(url)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_unregister_nonexistent_participant_returns_400():
    # Arrange
    activity_name = "Chess Club"
    email = "missing@mergington.edu"
    url = make_activity_url(activity_name, "unregister", email)

    # Act
    response = client.post(url)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_unknown_activity_returns_404():
    # Arrange
    unknown_activity = "Unknown"
    email = "test@mergington.edu"
    url = make_activity_url(unknown_activity, "unregister", email)

    # Act
    response = client.post(url)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
