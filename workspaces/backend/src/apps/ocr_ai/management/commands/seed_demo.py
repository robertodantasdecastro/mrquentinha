from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from apps.catalog.models import (
    Dish,
    Ingredient,
    IngredientUnit,
    MenuDay,
    NutritionFact,
    NutritionSource,
)
from apps.catalog.services import (
    create_dish_with_ingredients,
    set_menu_for_day,
    update_dish_with_ingredients,
)
from apps.finance.models import APBill, APBillStatus
from apps.finance.services import ensure_default_accounts, record_cash_out_from_ap
from apps.ocr_ai.models import OCRJob, OCRKind
from apps.ocr_ai.services import apply_ocr_job, create_ocr_job
from apps.orders.models import OrderStatus, Payment, PaymentStatus
from apps.orders.services import (
    create_order,
    update_order_status,
    update_payment_status,
)
from apps.procurement.models import Purchase, PurchaseItem
from apps.procurement.services import create_purchase_and_apply_stock
from apps.production.models import ProductionBatch, ProductionBatchStatus
from apps.production.services import complete_batch, create_batch_for_date


class Command(BaseCommand):
    help = (
        "Cria dataset DEMO idempotente para navegar todo o fluxo "
        "(catalogo -> financeiro)."
    )

    INGREDIENT_SPECS = [
        {
            "name": "arroz branco",
            "unit": IngredientUnit.KILOGRAM,
            "nutrition": {
                "energy_kcal_100g": Decimal("128"),
                "carbs_g_100g": Decimal("28.0"),
                "protein_g_100g": Decimal("2.5"),
                "fat_g_100g": Decimal("0.3"),
                "sat_fat_g_100g": Decimal("0.1"),
                "fiber_g_100g": Decimal("0.9"),
                "sodium_mg_100g": Decimal("1"),
            },
        },
        {
            "name": "arroz integral",
            "unit": IngredientUnit.KILOGRAM,
            "nutrition": {
                "energy_kcal_100g": Decimal("123"),
                "carbs_g_100g": Decimal("25.6"),
                "protein_g_100g": Decimal("2.7"),
                "fat_g_100g": Decimal("1.0"),
                "sat_fat_g_100g": Decimal("0.2"),
                "fiber_g_100g": Decimal("1.6"),
                "sodium_mg_100g": Decimal("2"),
            },
        },
        {
            "name": "feijao carioca",
            "unit": IngredientUnit.KILOGRAM,
            "nutrition": {
                "energy_kcal_100g": Decimal("143"),
                "carbs_g_100g": Decimal("25.0"),
                "protein_g_100g": Decimal("9.0"),
                "fat_g_100g": Decimal("0.8"),
                "sat_fat_g_100g": Decimal("0.2"),
                "fiber_g_100g": Decimal("8.5"),
                "sodium_mg_100g": Decimal("3"),
            },
        },
        {
            "name": "peito de frango",
            "unit": IngredientUnit.KILOGRAM,
            "nutrition": {
                "energy_kcal_100g": Decimal("165"),
                "carbs_g_100g": Decimal("0"),
                "protein_g_100g": Decimal("31.0"),
                "fat_g_100g": Decimal("3.6"),
                "sat_fat_g_100g": Decimal("1.0"),
                "fiber_g_100g": Decimal("0"),
                "sodium_mg_100g": Decimal("74"),
            },
        },
        {
            "name": "carne moida",
            "unit": IngredientUnit.KILOGRAM,
            "nutrition": {
                "energy_kcal_100g": Decimal("250"),
                "carbs_g_100g": Decimal("0"),
                "protein_g_100g": Decimal("26.0"),
                "fat_g_100g": Decimal("15.0"),
                "sat_fat_g_100g": Decimal("6.0"),
                "fiber_g_100g": Decimal("0"),
                "sodium_mg_100g": Decimal("72"),
            },
        },
        {
            "name": "tilapia",
            "unit": IngredientUnit.KILOGRAM,
            "nutrition": {
                "energy_kcal_100g": Decimal("129"),
                "carbs_g_100g": Decimal("0"),
                "protein_g_100g": Decimal("26.0"),
                "fat_g_100g": Decimal("2.7"),
                "sat_fat_g_100g": Decimal("1.0"),
                "fiber_g_100g": Decimal("0"),
                "sodium_mg_100g": Decimal("52"),
            },
        },
        {
            "name": "carne bovina",
            "unit": IngredientUnit.KILOGRAM,
            "nutrition": {
                "energy_kcal_100g": Decimal("217"),
                "carbs_g_100g": Decimal("0"),
                "protein_g_100g": Decimal("26.0"),
                "fat_g_100g": Decimal("12.0"),
                "sat_fat_g_100g": Decimal("5.0"),
                "fiber_g_100g": Decimal("0"),
                "sodium_mg_100g": Decimal("70"),
            },
        },
        {
            "name": "batata doce",
            "unit": IngredientUnit.KILOGRAM,
        },
        {
            "name": "alface",
            "unit": IngredientUnit.KILOGRAM,
        },
        {
            "name": "tomate",
            "unit": IngredientUnit.KILOGRAM,
        },
        {
            "name": "pepino",
            "unit": IngredientUnit.KILOGRAM,
        },
        {
            "name": "ovo",
            "unit": IngredientUnit.UNIT,
        },
        {"name": "cenoura", "unit": IngredientUnit.KILOGRAM},
        {"name": "abobrinha", "unit": IngredientUnit.KILOGRAM},
        {"name": "brocolis", "unit": IngredientUnit.KILOGRAM},
        {"name": "alho", "unit": IngredientUnit.KILOGRAM},
        {"name": "cebola", "unit": IngredientUnit.KILOGRAM},
        {"name": "azeite", "unit": IngredientUnit.LITER},
        {"name": "sal", "unit": IngredientUnit.KILOGRAM},
    ]

    DISH_SPECS = [
        {
            "name": "frango grelhado",
            "description": "Peito de frango temperado e grelhado.",
            "yield_portions": 20,
            "ingredients": [
                {
                    "ingredient": "peito de frango",
                    "quantity": Decimal("3.500"),
                    "unit": "kg",
                },
                {"ingredient": "alho", "quantity": Decimal("0.080"), "unit": "kg"},
                {"ingredient": "sal", "quantity": Decimal("0.025"), "unit": "kg"},
                {"ingredient": "azeite", "quantity": Decimal("0.150"), "unit": "l"},
            ],
        },
        {
            "name": "carne moida acebolada",
            "description": "Carne moida refogada com cebola.",
            "yield_portions": 20,
            "ingredients": [
                {
                    "ingredient": "carne moida",
                    "quantity": Decimal("3.000"),
                    "unit": "kg",
                },
                {"ingredient": "cebola", "quantity": Decimal("0.400"), "unit": "kg"},
                {"ingredient": "alho", "quantity": Decimal("0.070"), "unit": "kg"},
                {"ingredient": "azeite", "quantity": Decimal("0.120"), "unit": "l"},
            ],
        },
        {
            "name": "tilapia assada",
            "description": "File de tilapia assado com tempero leve.",
            "yield_portions": 20,
            "ingredients": [
                {"ingredient": "tilapia", "quantity": Decimal("3.200"), "unit": "kg"},
                {"ingredient": "alho", "quantity": Decimal("0.060"), "unit": "kg"},
                {"ingredient": "sal", "quantity": Decimal("0.020"), "unit": "kg"},
                {"ingredient": "azeite", "quantity": Decimal("0.100"), "unit": "l"},
            ],
        },
        {
            "name": "arroz soltinho",
            "description": "Arroz branco cozido.",
            "yield_portions": 30,
            "ingredients": [
                {
                    "ingredient": "arroz branco",
                    "quantity": Decimal("4.500"),
                    "unit": "kg",
                },
                {"ingredient": "alho", "quantity": Decimal("0.060"), "unit": "kg"},
                {"ingredient": "sal", "quantity": Decimal("0.020"), "unit": "kg"},
                {"ingredient": "azeite", "quantity": Decimal("0.120"), "unit": "l"},
            ],
        },
        {
            "name": "arroz integral",
            "description": "Arroz integral cozido.",
            "yield_portions": 30,
            "ingredients": [
                {
                    "ingredient": "arroz integral",
                    "quantity": Decimal("4.200"),
                    "unit": "kg",
                },
                {"ingredient": "alho", "quantity": Decimal("0.060"), "unit": "kg"},
                {"ingredient": "sal", "quantity": Decimal("0.020"), "unit": "kg"},
                {"ingredient": "azeite", "quantity": Decimal("0.100"), "unit": "l"},
            ],
        },
        {
            "name": "feijao caseiro",
            "description": "Feijao temperado no alho e cebola.",
            "yield_portions": 30,
            "ingredients": [
                {
                    "ingredient": "feijao carioca",
                    "quantity": Decimal("3.800"),
                    "unit": "kg",
                },
                {"ingredient": "cebola", "quantity": Decimal("0.300"), "unit": "kg"},
                {"ingredient": "alho", "quantity": Decimal("0.060"), "unit": "kg"},
                {"ingredient": "sal", "quantity": Decimal("0.020"), "unit": "kg"},
            ],
        },
        {
            "name": "legumes salteados",
            "description": "Mix de legumes no azeite.",
            "yield_portions": 25,
            "ingredients": [
                {"ingredient": "cenoura", "quantity": Decimal("1.500"), "unit": "kg"},
                {"ingredient": "abobrinha", "quantity": Decimal("1.500"), "unit": "kg"},
                {"ingredient": "brocolis", "quantity": Decimal("1.000"), "unit": "kg"},
                {"ingredient": "azeite", "quantity": Decimal("0.100"), "unit": "l"},
            ],
        },
        {
            "name": "pure de batata doce",
            "description": "Pure de batata doce com azeite.",
            "yield_portions": 25,
            "ingredients": [
                {
                    "ingredient": "batata doce",
                    "quantity": Decimal("4.000"),
                    "unit": "kg",
                },
                {"ingredient": "sal", "quantity": Decimal("0.020"), "unit": "kg"},
                {"ingredient": "azeite", "quantity": Decimal("0.080"), "unit": "l"},
            ],
        },
        {
            "name": "salada verde",
            "description": "Folhas e legumes frescos.",
            "yield_portions": 30,
            "ingredients": [
                {"ingredient": "alface", "quantity": Decimal("1.500"), "unit": "kg"},
                {"ingredient": "tomate", "quantity": Decimal("1.200"), "unit": "kg"},
                {"ingredient": "pepino", "quantity": Decimal("1.000"), "unit": "kg"},
                {"ingredient": "cenoura", "quantity": Decimal("0.800"), "unit": "kg"},
            ],
        },
        {
            "name": "omelete de legumes",
            "description": "Omelete com legumes salteados.",
            "yield_portions": 20,
            "ingredients": [
                {"ingredient": "ovo", "quantity": Decimal("60"), "unit": "unidade"},
                {"ingredient": "cenoura", "quantity": Decimal("0.600"), "unit": "kg"},
                {"ingredient": "abobrinha", "quantity": Decimal("0.600"), "unit": "kg"},
                {"ingredient": "cebola", "quantity": Decimal("0.300"), "unit": "kg"},
                {"ingredient": "sal", "quantity": Decimal("0.020"), "unit": "kg"},
                {"ingredient": "azeite", "quantity": Decimal("0.060"), "unit": "l"},
            ],
        },
        {
            "name": "carne de panela",
            "description": "Carne bovina cozida lentamente com temperos.",
            "yield_portions": 20,
            "ingredients": [
                {
                    "ingredient": "carne bovina",
                    "quantity": Decimal("3.200"),
                    "unit": "kg",
                },
                {"ingredient": "cebola", "quantity": Decimal("0.400"), "unit": "kg"},
                {"ingredient": "alho", "quantity": Decimal("0.080"), "unit": "kg"},
                {"ingredient": "sal", "quantity": Decimal("0.030"), "unit": "kg"},
                {"ingredient": "azeite", "quantity": Decimal("0.120"), "unit": "l"},
            ],
        },
    ]

    PURCHASE_SPECS = [
        {
            "invoice_number": "DEMO-NF-001",
            "supplier_name": "Atacado Paulista",
            "purchase_date_offset": -10,
            "items": [
                {
                    "ingredient": "arroz branco",
                    "qty": Decimal("20.000"),
                    "unit_price": Decimal("6.80"),
                    "tax_amount": Decimal("2.50"),
                },
                {
                    "ingredient": "arroz integral",
                    "qty": Decimal("16.000"),
                    "unit_price": Decimal("7.90"),
                    "tax_amount": Decimal("2.00"),
                },
                {
                    "ingredient": "feijao carioca",
                    "qty": Decimal("18.000"),
                    "unit_price": Decimal("7.20"),
                    "tax_amount": Decimal("2.10"),
                },
                {
                    "ingredient": "peito de frango",
                    "qty": Decimal("25.000"),
                    "unit_price": Decimal("14.90"),
                    "tax_amount": Decimal("3.80"),
                },
            ],
        },
        {
            "invoice_number": "DEMO-NF-002",
            "supplier_name": "Casa das Carnes Centro",
            "purchase_date_offset": -7,
            "items": [
                {
                    "ingredient": "carne moida",
                    "qty": Decimal("18.000"),
                    "unit_price": Decimal("19.80"),
                    "tax_amount": Decimal("4.20"),
                },
                {
                    "ingredient": "tilapia",
                    "qty": Decimal("16.000"),
                    "unit_price": Decimal("21.30"),
                    "tax_amount": Decimal("3.90"),
                },
                {
                    "ingredient": "carne bovina",
                    "qty": Decimal("14.000"),
                    "unit_price": Decimal("23.50"),
                    "tax_amount": Decimal("4.10"),
                },
            ],
        },
        {
            "invoice_number": "DEMO-NF-003",
            "supplier_name": "Horti Prime",
            "purchase_date_offset": -5,
            "items": [
                {
                    "ingredient": "batata doce",
                    "qty": Decimal("14.000"),
                    "unit_price": Decimal("4.90"),
                    "tax_amount": Decimal("1.20"),
                },
                {
                    "ingredient": "cenoura",
                    "qty": Decimal("12.000"),
                    "unit_price": Decimal("4.50"),
                    "tax_amount": Decimal("1.10"),
                },
                {
                    "ingredient": "abobrinha",
                    "qty": Decimal("10.000"),
                    "unit_price": Decimal("5.10"),
                    "tax_amount": Decimal("1.00"),
                },
                {
                    "ingredient": "brocolis",
                    "qty": Decimal("8.000"),
                    "unit_price": Decimal("6.30"),
                    "tax_amount": Decimal("0.90"),
                },
                {
                    "ingredient": "alface",
                    "qty": Decimal("6.000"),
                    "unit_price": Decimal("3.80"),
                    "tax_amount": Decimal("0.60"),
                },
                {
                    "ingredient": "tomate",
                    "qty": Decimal("10.000"),
                    "unit_price": Decimal("5.40"),
                    "tax_amount": Decimal("1.10"),
                },
                {
                    "ingredient": "pepino",
                    "qty": Decimal("6.000"),
                    "unit_price": Decimal("4.20"),
                    "tax_amount": Decimal("0.70"),
                },
                {
                    "ingredient": "azeite",
                    "qty": Decimal("6.000"),
                    "unit_price": Decimal("18.00"),
                    "tax_amount": Decimal("2.20"),
                },
            ],
        },
        {
            "invoice_number": "DEMO-NF-004",
            "supplier_name": "Granja Santa Luzia",
            "purchase_date_offset": -3,
            "items": [
                {
                    "ingredient": "ovo",
                    "qty": Decimal("200"),
                    "unit_price": Decimal("0.85"),
                    "tax_amount": Decimal("0.00"),
                },
            ],
        },
    ]

    @transaction.atomic
    def handle(self, *args, **options):
        ensure_default_accounts()

        demo_customer = self._ensure_demo_customer()
        ingredients = self._seed_ingredients()
        dishes = self._seed_dishes(ingredients)
        menu_days = self._seed_menu_days(dishes)
        purchases = self._seed_purchases(ingredients)

        self._seed_production(menu_days)
        self._seed_ocr_jobs(ingredients, purchases)
        self._seed_orders(demo_customer, menu_days)
        self._seed_finance_expenses()

        self.stdout.write(self.style.SUCCESS("seed_demo concluido com sucesso."))

    def _ensure_demo_customer(self):
        user_model = get_user_model()
        user, _ = user_model.objects.get_or_create(
            username="cliente_demo",
            defaults={
                "email": "cliente.demo@mrquentinha.com.br",
            },
        )
        return user

    def _create_text_image(self, *, slug: str, lines: list[str]) -> ContentFile:
        width = 1000
        height = 680
        image = Image.new("RGB", (width, height), color=(250, 247, 243))
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()

        y = 30
        for line in lines:
            draw.text((30, y), line, fill=(35, 35, 35), font=font)
            y += 28

        draw.rectangle([(20, 20), (980, 660)], outline=(255, 106, 0), width=3)

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return ContentFile(buffer.getvalue(), name=f"demo/{slug}.png")

    def _seed_ingredients(self) -> dict[str, Ingredient]:
        ingredients: dict[str, Ingredient] = {}

        for spec in self.INGREDIENT_SPECS:
            name = str(spec["name"]).strip().lower()
            unit = str(spec["unit"])

            ingredient, _ = Ingredient.objects.get_or_create(
                name=name,
                defaults={
                    "unit": unit,
                    "is_active": True,
                },
            )

            updated_fields: list[str] = []
            if ingredient.unit != unit:
                ingredient.unit = unit
                updated_fields.append("unit")
            if not ingredient.is_active:
                ingredient.is_active = True
                updated_fields.append("is_active")

            if not ingredient.image:
                image = self._create_text_image(
                    slug=f"ingredient-{ingredient.id}",
                    lines=[
                        f"Ingrediente DEMO: {name}",
                        f"Unidade: {unit}",
                        "Imagem sintetica para ambiente de desenvolvimento.",
                    ],
                )
                ingredient.image.save(image.name, image, save=False)
                updated_fields.append("image")

            if updated_fields:
                updated_fields.append("updated_at")
                ingredient.save(update_fields=updated_fields)

            nutrition_spec = spec.get("nutrition")
            if nutrition_spec:
                nutrition_fact, _ = NutritionFact.objects.get_or_create(
                    ingredient=ingredient
                )
                for field_name, field_value in nutrition_spec.items():
                    setattr(nutrition_fact, field_name, field_value)
                nutrition_fact.source = NutritionSource.ESTIMATED
                nutrition_fact.save()

            ingredients[name] = ingredient

        return ingredients

    def _build_dish_payload(
        self, *, dish_spec: dict, ingredients: dict[str, Ingredient]
    ) -> list[dict]:
        payload = []
        for item in dish_spec["ingredients"]:
            payload.append(
                {
                    "ingredient": ingredients[item["ingredient"]],
                    "quantity": item["quantity"],
                    "unit": item["unit"],
                }
            )
        return payload

    def _seed_dishes(self, ingredients: dict[str, Ingredient]) -> dict[str, Dish]:
        dishes: dict[str, Dish] = {}

        for dish_spec in self.DISH_SPECS:
            name = dish_spec["name"]
            dish_data = {
                "name": name,
                "description": dish_spec["description"],
                "yield_portions": dish_spec["yield_portions"],
            }
            ingredient_payload = self._build_dish_payload(
                dish_spec=dish_spec,
                ingredients=ingredients,
            )

            dish = Dish.objects.filter(name__iexact=name).first()
            if dish is None:
                dish = create_dish_with_ingredients(
                    dish_data=dish_data,
                    ingredients_payload=ingredient_payload,
                )
            else:
                dish = update_dish_with_ingredients(
                    dish=dish,
                    dish_data=dish_data,
                    ingredients_payload=ingredient_payload,
                )

            if not dish.image:
                image = self._create_text_image(
                    slug=f"dish-{dish.id}",
                    lines=[
                        f"Prato DEMO: {dish.name}",
                        f"Rendimento: {dish.yield_portions} porcoes",
                        dish.description or "",
                    ],
                )
                dish.image.save(image.name, image, save=True)

            dishes[dish.name.lower()] = dish

        return dishes

    def _resolve_monday(self, base_date: date) -> date:
        return base_date - timedelta(days=base_date.weekday())

    def _list_weekdays(self, *, start_date: date, weeks: int) -> list[date]:
        dates: list[date] = []
        current = start_date

        while len(dates) < weeks * 5:
            if current.weekday() < 5:
                dates.append(current)
            current += timedelta(days=1)

        return dates

    def _seed_menu_days(self, dishes: dict[str, Dish]) -> list[MenuDay]:
        today = timezone.localdate()
        start_monday = self._resolve_monday(today)
        weekdays = self._list_weekdays(start_date=start_monday, weeks=2)

        protein_cycle = [
            dishes["frango grelhado"],
            dishes["carne moida acebolada"],
            dishes["tilapia assada"],
            dishes["carne de panela"],
            dishes["omelete de legumes"],
        ]

        menu_days: list[MenuDay] = []

        for idx, menu_date in enumerate(weekdays):
            protein = protein_cycle[idx % len(protein_cycle)]
            base_dish = (
                dishes["arroz integral"] if idx % 2 == 0 else dishes["arroz soltinho"]
            )
            acompanhamento_extra = (
                dishes["pure de batata doce"]
                if idx % 3 == 0
                else dishes["salada verde"]
            )

            items_payload = [
                {
                    "dish": base_dish,
                    "sale_price": Decimal("9.90"),
                    "available_qty": 80,
                    "is_active": True,
                },
                {
                    "dish": dishes["feijao caseiro"],
                    "sale_price": Decimal("9.90"),
                    "available_qty": 70,
                    "is_active": True,
                },
                {
                    "dish": dishes["legumes salteados"],
                    "sale_price": Decimal("11.90"),
                    "available_qty": 60,
                    "is_active": True,
                },
                {
                    "dish": acompanhamento_extra,
                    "sale_price": Decimal("12.90"),
                    "available_qty": 50,
                    "is_active": True,
                },
                {
                    "dish": protein,
                    "sale_price": (
                        Decimal("24.90")
                        if protein.name.lower() != "tilapia assada"
                        else Decimal("27.90")
                    ),
                    "available_qty": 50,
                    "is_active": True,
                },
            ]

            menu_day = MenuDay.objects.filter(menu_date=menu_date).first()
            if menu_day is None:
                menu_day = set_menu_for_day(
                    menu_date=menu_date,
                    title=f"Cardapio DEMO {menu_date.isoformat()}",
                    items_payload=items_payload,
                    created_by=None,
                )
            menu_days.append(menu_day)

        return menu_days

    def _build_label_text(self, ingredient_name: str) -> str:
        return (
            f"DEMO_TAG:{ingredient_name}\n"
            f"Produto: {ingredient_name.title()}\n"
            "Marca: MrQ Insumos\n"
            "Peso liquido: 1 kg\n"
            "Porcao: 100 g\n"
            "Porcoes por embalagem: 10\n"
            "Valor energetico 120 kcal\n"
            "Carboidratos 15 g\n"
            "Proteinas 9 g\n"
            "Gorduras totais 3 g\n"
            "Gorduras saturadas 1 g\n"
            "Fibras 4 g\n"
            "Sodio 150 mg\n"
            "Acucares totais 2 g\n"
            "Acucares adicionados 1 g\n"
        )

    def _seed_purchases(self, ingredients: dict[str, Ingredient]) -> list[Purchase]:
        purchases: list[Purchase] = []
        today = timezone.localdate()

        for purchase_spec in self.PURCHASE_SPECS:
            invoice_number = purchase_spec["invoice_number"]
            purchase = Purchase.objects.filter(invoice_number=invoice_number).first()

            if purchase is None:
                purchase_date = today + timedelta(
                    days=purchase_spec["purchase_date_offset"]
                )
                receipt_image = self._create_text_image(
                    slug=f"receipt-{invoice_number.lower()}",
                    lines=[
                        f"Fornecedor: {purchase_spec['supplier_name']}",
                        f"Nota fiscal: {invoice_number}",
                        f"Data: {purchase_date.isoformat()}",
                        "Documento sintetico DEMO.",
                    ],
                )

                items_payload = []
                for index, item in enumerate(purchase_spec["items"], start=1):
                    ingredient = ingredients[item["ingredient"]]
                    label_front = self._create_text_image(
                        slug=f"{invoice_number.lower()}-item-{index}-front",
                        lines=[
                            f"ROTULO FRONTAL DEMO {invoice_number}",
                            f"Produto: {ingredient.name}",
                            f"Quantidade: {item['qty']} {ingredient.unit}",
                        ],
                    )
                    label_back = self._create_text_image(
                        slug=f"{invoice_number.lower()}-item-{index}-back",
                        lines=[
                            f"ROTULO NUTRICIONAL DEMO {invoice_number}",
                            self._build_label_text(ingredient.name),
                        ],
                    )

                    items_payload.append(
                        {
                            "ingredient": ingredient,
                            "qty": item["qty"],
                            "unit": ingredient.unit,
                            "unit_price": item["unit_price"],
                            "tax_amount": item.get("tax_amount") or Decimal("0"),
                            "label_front_image": label_front,
                            "label_back_image": label_back,
                        }
                    )

                purchase = create_purchase_and_apply_stock(
                    purchase_data={
                        "supplier_name": purchase_spec["supplier_name"],
                        "invoice_number": invoice_number,
                        "purchase_date": purchase_date,
                        "receipt_image": receipt_image,
                    },
                    items_payload=items_payload,
                    buyer=None,
                )

            purchases.append(purchase)

        return purchases

    def _seed_production(self, menu_days: list[MenuDay]) -> None:
        if not menu_days:
            return

        target_days = sorted(menu_days, key=lambda menu_day: menu_day.menu_date)[:2]

        for menu_day in target_days:
            batch = ProductionBatch.objects.filter(
                production_date=menu_day.menu_date
            ).first()
            if batch is None:
                active_items = list(menu_day.items.filter(is_active=True)[:3])
                if not active_items:
                    continue

                items_payload = []
                for menu_item in active_items:
                    planned = menu_item.available_qty or 20
                    produced = max(1, int(planned * 0.5))
                    items_payload.append(
                        {
                            "menu_item": menu_item,
                            "qty_planned": planned,
                            "qty_produced": produced,
                            "qty_waste": 1,
                        }
                    )

                batch = create_batch_for_date(
                    production_date=menu_day.menu_date,
                    items_payload=items_payload,
                    note=f"Lote DEMO {menu_day.menu_date.isoformat()}",
                    created_by=None,
                )

            if batch.status != ProductionBatchStatus.DONE:
                try:
                    complete_batch(batch_id=batch.id)
                except Exception:
                    # Se faltar estoque para o lote, mantemos sem quebrar o seed.
                    pass

    def _seed_ocr_jobs(
        self, ingredients: dict[str, Ingredient], purchases: list[Purchase]
    ) -> None:
        ingredient_targets = [
            ingredients["arroz branco"],
            ingredients["feijao carioca"],
            ingredients["peito de frango"],
        ]

        for ingredient in ingredient_targets:
            tag = f"DEMO_TAG:{ingredient.name}"
            ocr_job = (
                OCRJob.objects.filter(raw_text__contains=tag).order_by("-id").first()
            )

            if ocr_job is None:
                image = self._create_text_image(
                    slug=f"ocr-{ingredient.id}",
                    lines=[
                        "Tabela nutricional sintetica",
                        self._build_label_text(ingredient.name),
                    ],
                )
                ocr_job = create_ocr_job(
                    kind=OCRKind.LABEL_BACK,
                    image=image,
                    raw_text=self._build_label_text(ingredient.name),
                )

            apply_ocr_job(
                job_id=ocr_job.id,
                target_type="INGREDIENT",
                target_id=ingredient.id,
                mode="merge",
            )

        if purchases:
            purchase_items = PurchaseItem.objects.filter(
                purchase__in=purchases
            ).order_by("id")[:2]
            for purchase_item in purchase_items:
                tag = f"DEMO_TAG:{purchase_item.ingredient.name}"
                ocr_job = (
                    OCRJob.objects.filter(raw_text__contains=tag)
                    .order_by("-id")
                    .first()
                )
                if ocr_job is None:
                    continue

                apply_ocr_job(
                    job_id=ocr_job.id,
                    target_type="PURCHASE_ITEM",
                    target_id=purchase_item.id,
                    mode="merge",
                )

    def _ensure_order_status(self, *, order_id: int, target_status: str) -> None:
        order = (
            Payment.objects.select_related("order")
            .filter(order_id=order_id)
            .first()
            .order
        )

        if order.status == target_status:
            return

        if target_status == OrderStatus.CANCELED:
            if order.status in {
                OrderStatus.CREATED,
                OrderStatus.CONFIRMED,
                OrderStatus.IN_PROGRESS,
            }:
                update_order_status(order_id=order.id, new_status=OrderStatus.CANCELED)
            return

        transitions = [
            OrderStatus.CONFIRMED,
            OrderStatus.IN_PROGRESS,
            OrderStatus.DELIVERED,
        ]

        for transition in transitions:
            order.refresh_from_db()
            if order.status == target_status:
                break
            if order.status == OrderStatus.CANCELED:
                break
            if order.status == OrderStatus.DELIVERED:
                break

            if (
                transition == OrderStatus.CONFIRMED
                and order.status == OrderStatus.CREATED
            ):
                update_order_status(order_id=order.id, new_status=OrderStatus.CONFIRMED)
            elif (
                transition == OrderStatus.IN_PROGRESS
                and order.status == OrderStatus.CONFIRMED
            ):
                update_order_status(
                    order_id=order.id, new_status=OrderStatus.IN_PROGRESS
                )
            elif (
                transition == OrderStatus.DELIVERED
                and order.status == OrderStatus.IN_PROGRESS
            ):
                update_order_status(order_id=order.id, new_status=OrderStatus.DELIVERED)

    def _seed_orders(self, demo_customer, menu_days: list[MenuDay]) -> None:
        ordered_menu_days = sorted(menu_days, key=lambda menu_day: menu_day.menu_date)
        target_statuses = [
            OrderStatus.DELIVERED,
            OrderStatus.DELIVERED,
            OrderStatus.CONFIRMED,
            OrderStatus.CREATED,
            OrderStatus.CANCELED,
            OrderStatus.IN_PROGRESS,
        ]

        for index, menu_day in enumerate(ordered_menu_days[:6], start=1):
            marker = f"DEMO-ORDER-{index:03d}"
            target_status = target_statuses[index - 1]

            payment = (
                Payment.objects.select_related("order")
                .filter(provider_ref=marker)
                .first()
            )
            if payment is None:
                active_items = list(
                    menu_day.items.filter(is_active=True).order_by("id")[:2]
                )
                if not active_items:
                    continue

                order = create_order(
                    customer=demo_customer,
                    delivery_date=menu_day.menu_date,
                    items_payload=[
                        {
                            "menu_item": active_items[0],
                            "qty": 1 + (index % 2),
                        },
                        {
                            "menu_item": active_items[-1],
                            "qty": 1,
                        },
                    ],
                )
                payment = order.payments.first()
                payment.provider_ref = marker
                payment.save(update_fields=["provider_ref"])

            self._ensure_order_status(
                order_id=payment.order_id, target_status=target_status
            )

            if target_status in {OrderStatus.DELIVERED, OrderStatus.IN_PROGRESS}:
                update_payment_status(
                    payment_id=payment.id,
                    update_data={
                        "status": PaymentStatus.PAID,
                        "provider_ref": marker,
                    },
                )
            else:
                update_payment_status(
                    payment_id=payment.id,
                    update_data={
                        "provider_ref": marker,
                    },
                )

    def _seed_finance_expenses(self) -> None:
        today = timezone.localdate()

        manual_bills = [
            {
                "reference_id": 1001,
                "supplier_name": "Conta de Luz DEMO",
                "amount": Decimal("350.00"),
                "due_date": today - timedelta(days=3),
            },
            {
                "reference_id": 1002,
                "supplier_name": "Conta de Internet DEMO",
                "amount": Decimal("199.90"),
                "due_date": today - timedelta(days=2),
            },
            {
                "reference_id": 1003,
                "supplier_name": "Aluguel DEMO",
                "amount": Decimal("1800.00"),
                "due_date": today - timedelta(days=1),
            },
        ]

        expense_account = ensure_default_accounts()[1]

        for item in manual_bills:
            bill = APBill.objects.filter(
                reference_type="MANUAL",
                reference_id=item["reference_id"],
            ).first()

            if bill is None:
                bill = APBill.objects.create(
                    supplier_name=item["supplier_name"],
                    account=expense_account,
                    amount=item["amount"],
                    due_date=item["due_date"],
                    status=APBillStatus.OPEN,
                    reference_type="MANUAL",
                    reference_id=item["reference_id"],
                )

            record_cash_out_from_ap(bill.id)
