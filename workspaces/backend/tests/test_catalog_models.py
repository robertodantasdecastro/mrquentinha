import pytest
from django.db import IntegrityError

from apps.catalog.models import Ingredient, IngredientUnit


@pytest.mark.django_db(transaction=True)
def test_ingredient_normaliza_nome_e_impede_duplicidade_case_insensitive():
    ingrediente = Ingredient.objects.create(
        name="  Tomate   Italiano  ",
        unit=IngredientUnit.KILOGRAM,
    )

    assert ingrediente.name == "tomate italiano"

    with pytest.raises(IntegrityError):
        Ingredient.objects.create(name="TOMATE ITALIANO", unit=IngredientUnit.KILOGRAM)
