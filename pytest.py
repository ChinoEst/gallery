import httpx
import pytest


#test_
def test_1():
    assert 1 + 1 == 2

def test_2():
    assert "hello" + " world" == "hello world"

def test_登入():
    BASE_URL = "http://127.0.0.1:8000"
    res = httpx.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "1234"})
    assert res.status_code == 200
    assert "token" in res.json()