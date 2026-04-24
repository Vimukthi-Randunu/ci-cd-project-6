import pytest
from unittest.mock import patch, MagicMock
import os

# Set environment variables before importing app
os.environ['DB_USER'] = 'test_user'
os.environ['DB_PASSWORD'] = 'test_password'
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_NAME'] = 'test_db'

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.json == {'status': 'ok'}

def test_get_users(client):
    # Create a fake user object
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.name = 'Test User'
    mock_user.email = 'test@example.com'

    with patch('app.User.query') as mock_query:
        mock_query.all.return_value = [mock_user]
        response = client.get('/users')

    assert response.status_code == 200
    data = response.json
    assert len(data) == 1
    assert data[0]['name'] == 'Test User'
    assert data[0]['email'] == 'test@example.com'