import pytest

@pytest.fixture 
def panier():
    return ["bao", "the"]

def test_panier(panier):
    assert len(panier) == 2

@pytest.fixture
def ressource():
    print("ouverture")
    yield {"etat": "ouvert"}
    print("fermeture")
