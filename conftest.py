import pytest
from app.main import app
from app.accounts import current_user, _attempts

@pytest.fixture(autouse=True)
def isolated_auth(request):
    _attempts.clear()
    app.dependency_overrides.clear()
    if request.node.path.name != "test_accounts.py":
        app.dependency_overrides[current_user] = lambda: {"id":"test-user","email":"test@example.com","verified":True}
    yield
    app.dependency_overrides.clear()
    _attempts.clear()
