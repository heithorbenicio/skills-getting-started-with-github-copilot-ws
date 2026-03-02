import copy
import pytest

from fastapi.testclient import TestClient

from src.app import app, activities


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Arrange: snapshot the in-memory database and restore after each test.

    The application stores activity state in the module-level `activities`
    dictionary.  To prevent one test from mutating state for another we make a
    deep copy before the test executes and then restore it afterwards.
    """

    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_root_redirect():
    # Act: disable automatic redirects so we can inspect the response directly
    response = client.get("/", allow_redirects=False)

    # Assert
    assert response.status_code in (307, 308)
    assert "/static/index.html" in response.headers["location"]


def test_get_activities():
    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, dict)
    # check a few known keys
    assert "Chess Club" in payload
    assert "Programming Class" in payload


def test_signup_success():
    # Arrange
    email = "newstudent@mergington.edu"

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert email in activities["Chess Club"]["participants"]
    assert response.json()["message"].startswith("Signed up")


def test_signup_nonexistent_activity():
    # Act
    response = client.post("/activities/Nonexistent/signup", params={"email": "x@x.com"})

    # Assert
    assert response.status_code == 404


def test_signup_already_registered():
    # Arrange
    existing = activities["Chess Club"]["participants"][0]

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": existing})

    # Assert
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()


def test_remove_participant_success():
    # Arrange
    email = activities["Chess Club"]["participants"][0]

    # Act
    response = client.delete(f"/activities/Chess Club/participants/{email}")

    # Assert
    assert response.status_code == 200
    assert email not in activities["Chess Club"]["participants"]


def test_remove_participant_activity_not_found():
    # Act
    response = client.delete("/activities/Nope/participants/x@x.com")

    # Assert
    assert response.status_code == 404


def test_remove_participant_not_signed_up():
    # Arrange
    email = "nobody@mergington.edu"

    # Act
    response = client.delete(f"/activities/Chess Club/participants/{email}")

    # Assert
    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()
