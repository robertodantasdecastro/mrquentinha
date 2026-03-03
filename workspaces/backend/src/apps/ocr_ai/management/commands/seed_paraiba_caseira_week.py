from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from apps.catalog.models import Dish, Ingredient, IngredientUnit, MenuDay
from apps.catalog.services import (
    create_dish_with_ingredients,
    set_menu_for_day,
    update_dish_with_ingredients,
)
from apps.finance.services import ensure_default_accounts
from apps.ocr_ai.models import OCRKind
from apps.ocr_ai.services import apply_ocr_job, create_ocr_job
from apps.procurement.models import Purchase
from apps.procurement.services import (
    create_purchase_and_apply_stock,
    generate_purchase_request_from_menu,
)
from apps.production.models import ProductionBatch, ProductionBatchStatus
from apps.production.services import complete_batch, create_batch_for_date


class Command(BaseCommand):
    help = (
        "Cria fluxo semanal idempotente de culinaria paraibana caseira "
        "(cardapio -> compra OCR -> producao -> financeiro)."
    )

    MARKUP_FACTOR = Decimal("1.75")
    OVERHEAD_FACTOR = Decimal("1.18")
    PACKAGING_COST = Decimal("1.80")
    MONEY_SCALE = Decimal("0.01")
    QTY_SCALE = Decimal("0.001")

    INGREDIENT_SPECS = [
        {"name": "arroz branco", "unit": IngredientUnit.KILOGRAM},
        {"name": "feijao verde", "unit": IngredientUnit.KILOGRAM},
        {"name": "feijao macassar", "unit": IngredientUnit.KILOGRAM},
        {"name": "feijao carioca", "unit": IngredientUnit.KILOGRAM},
        {"name": "carne de sol", "unit": IngredientUnit.KILOGRAM},
        {"name": "charque", "unit": IngredientUnit.KILOGRAM},
        {"name": "frango caipira", "unit": IngredientUnit.KILOGRAM},
        {"name": "file de tilapia", "unit": IngredientUnit.KILOGRAM},
        {"name": "macaxeira", "unit": IngredientUnit.KILOGRAM},
        {"name": "jerimum", "unit": IngredientUnit.KILOGRAM},
        {"name": "queijo coalho", "unit": IngredientUnit.KILOGRAM},
        {"name": "leite de coco", "unit": IngredientUnit.LITER},
        {"name": "farinha de mandioca", "unit": IngredientUnit.KILOGRAM},
        {"name": "cebola", "unit": IngredientUnit.KILOGRAM},
        {"name": "alho", "unit": IngredientUnit.KILOGRAM},
        {"name": "tomate", "unit": IngredientUnit.KILOGRAM},
        {"name": "coentro", "unit": IngredientUnit.KILOGRAM},
        {"name": "pimentao", "unit": IngredientUnit.KILOGRAM},
        {"name": "manteiga da terra", "unit": IngredientUnit.LITER},
        {"name": "sal", "unit": IngredientUnit.KILOGRAM},
    ]

    # Quantidade por porcao (1 marmita). Produzimos 20 por dia.
    DISH_SPECS = [
        {
            "weekday": 0,
            "name": "rubacao paraibano com carne de sol",
            "description": (
                "Arroz, feijao verde, carne de sol e queijo coalho no estilo caseiro "
                "paraibano."
            ),
            "ingredients": [
                {
                    "ingredient": "arroz branco",
                    "quantity": Decimal("0.110"),
                    "unit": "kg",
                },
                {
                    "ingredient": "feijao verde",
                    "quantity": Decimal("0.080"),
                    "unit": "kg",
                },
                {
                    "ingredient": "carne de sol",
                    "quantity": Decimal("0.120"),
                    "unit": "kg",
                },
                {
                    "ingredient": "queijo coalho",
                    "quantity": Decimal("0.030"),
                    "unit": "kg",
                },
                {"ingredient": "cebola", "quantity": Decimal("0.015"), "unit": "kg"},
                {"ingredient": "alho", "quantity": Decimal("0.004"), "unit": "kg"},
                {"ingredient": "coentro", "quantity": Decimal("0.003"), "unit": "kg"},
                {
                    "ingredient": "manteiga da terra",
                    "quantity": Decimal("0.004"),
                    "unit": "l",
                },
            ],
        },
        {
            "weekday": 1,
            "name": "baiao de dois com pacoca de carne de sol",
            "description": "Baião de dois cremoso com paçoca de carne de sol.",
            "ingredients": [
                {
                    "ingredient": "arroz branco",
                    "quantity": Decimal("0.105"),
                    "unit": "kg",
                },
                {
                    "ingredient": "feijao macassar",
                    "quantity": Decimal("0.085"),
                    "unit": "kg",
                },
                {
                    "ingredient": "carne de sol",
                    "quantity": Decimal("0.115"),
                    "unit": "kg",
                },
                {
                    "ingredient": "farinha de mandioca",
                    "quantity": Decimal("0.020"),
                    "unit": "kg",
                },
                {"ingredient": "cebola", "quantity": Decimal("0.014"), "unit": "kg"},
                {"ingredient": "alho", "quantity": Decimal("0.004"), "unit": "kg"},
                {"ingredient": "coentro", "quantity": Decimal("0.003"), "unit": "kg"},
                {
                    "ingredient": "manteiga da terra",
                    "quantity": Decimal("0.004"),
                    "unit": "l",
                },
            ],
        },
        {
            "weekday": 2,
            "name": "arrumadinho paraibano de charque",
            "description": "Charque desfiado com feijao, farofa e vinagrete caseiro.",
            "ingredients": [
                {"ingredient": "charque", "quantity": Decimal("0.125"), "unit": "kg"},
                {
                    "ingredient": "feijao carioca",
                    "quantity": Decimal("0.090"),
                    "unit": "kg",
                },
                {
                    "ingredient": "farinha de mandioca",
                    "quantity": Decimal("0.030"),
                    "unit": "kg",
                },
                {"ingredient": "tomate", "quantity": Decimal("0.020"), "unit": "kg"},
                {"ingredient": "cebola", "quantity": Decimal("0.015"), "unit": "kg"},
                {"ingredient": "pimentao", "quantity": Decimal("0.010"), "unit": "kg"},
                {"ingredient": "coentro", "quantity": Decimal("0.003"), "unit": "kg"},
                {"ingredient": "sal", "quantity": Decimal("0.003"), "unit": "kg"},
            ],
        },
        {
            "weekday": 3,
            "name": "galinha guisada com macaxeira",
            "description": "Frango caipira guisado com macaxeira e tempero de quintal.",
            "ingredients": [
                {
                    "ingredient": "frango caipira",
                    "quantity": Decimal("0.180"),
                    "unit": "kg",
                },
                {"ingredient": "macaxeira", "quantity": Decimal("0.140"), "unit": "kg"},
                {"ingredient": "cebola", "quantity": Decimal("0.015"), "unit": "kg"},
                {"ingredient": "alho", "quantity": Decimal("0.004"), "unit": "kg"},
                {"ingredient": "tomate", "quantity": Decimal("0.020"), "unit": "kg"},
                {"ingredient": "coentro", "quantity": Decimal("0.003"), "unit": "kg"},
                {"ingredient": "sal", "quantity": Decimal("0.003"), "unit": "kg"},
            ],
        },
        {
            "weekday": 4,
            "name": "peixe ao coco com arroz caseiro",
            "description": "Tilápia ao molho de coco com arroz soltinho.",
            "ingredients": [
                {
                    "ingredient": "file de tilapia",
                    "quantity": Decimal("0.170"),
                    "unit": "kg",
                },
                {
                    "ingredient": "leite de coco",
                    "quantity": Decimal("0.035"),
                    "unit": "l",
                },
                {
                    "ingredient": "arroz branco",
                    "quantity": Decimal("0.090"),
                    "unit": "kg",
                },
                {"ingredient": "cebola", "quantity": Decimal("0.015"), "unit": "kg"},
                {"ingredient": "alho", "quantity": Decimal("0.004"), "unit": "kg"},
                {"ingredient": "pimentao", "quantity": Decimal("0.010"), "unit": "kg"},
                {"ingredient": "coentro", "quantity": Decimal("0.003"), "unit": "kg"},
                {"ingredient": "sal", "quantity": Decimal("0.003"), "unit": "kg"},
            ],
        },
        {
            "weekday": 5,
            "name": "carne de panela com jerimum",
            "description": (
                "Carne de sol cozida lentamente com jerimum e tempero regional."
            ),
            "ingredients": [
                {
                    "ingredient": "carne de sol",
                    "quantity": Decimal("0.150"),
                    "unit": "kg",
                },
                {"ingredient": "jerimum", "quantity": Decimal("0.130"), "unit": "kg"},
                {
                    "ingredient": "arroz branco",
                    "quantity": Decimal("0.080"),
                    "unit": "kg",
                },
                {"ingredient": "cebola", "quantity": Decimal("0.015"), "unit": "kg"},
                {"ingredient": "alho", "quantity": Decimal("0.004"), "unit": "kg"},
                {"ingredient": "coentro", "quantity": Decimal("0.003"), "unit": "kg"},
                {"ingredient": "sal", "quantity": Decimal("0.003"), "unit": "kg"},
            ],
        },
        {
            "weekday": 6,
            "name": "escondidinho de macaxeira com charque",
            "description": "Macaxeira cremosa gratinada com charque desfiado.",
            "ingredients": [
                {"ingredient": "macaxeira", "quantity": Decimal("0.170"), "unit": "kg"},
                {"ingredient": "charque", "quantity": Decimal("0.120"), "unit": "kg"},
                {
                    "ingredient": "leite de coco",
                    "quantity": Decimal("0.030"),
                    "unit": "l",
                },
                {
                    "ingredient": "queijo coalho",
                    "quantity": Decimal("0.020"),
                    "unit": "kg",
                },
                {"ingredient": "cebola", "quantity": Decimal("0.014"), "unit": "kg"},
                {"ingredient": "alho", "quantity": Decimal("0.004"), "unit": "kg"},
                {"ingredient": "coentro", "quantity": Decimal("0.003"), "unit": "kg"},
                {"ingredient": "sal", "quantity": Decimal("0.003"), "unit": "kg"},
            ],
        },
    ]

    INGREDIENT_PRICE_MAP = {
        "arroz branco": Decimal("6.90"),
        "feijao verde": Decimal("12.50"),
        "feijao macassar": Decimal("11.90"),
        "feijao carioca": Decimal("8.10"),
        "carne de sol": Decimal("38.00"),
        "charque": Decimal("34.00"),
        "frango caipira": Decimal("22.50"),
        "file de tilapia": Decimal("29.90"),
        "macaxeira": Decimal("5.90"),
        "jerimum": Decimal("4.80"),
        "queijo coalho": Decimal("32.00"),
        "leite de coco": Decimal("14.50"),
        "farinha de mandioca": Decimal("9.20"),
        "cebola": Decimal("5.40"),
        "alho": Decimal("14.80"),
        "tomate": Decimal("8.00"),
        "coentro": Decimal("12.00"),
        "pimentao": Decimal("8.50"),
        "manteiga da terra": Decimal("36.00"),
        "sal": Decimal("2.50"),
    }

    WEEKDAY_LABELS = {
        0: "Segunda",
        1: "Terca",
        2: "Quarta",
        3: "Quinta",
        4: "Sexta",
        5: "Sabado",
        6: "Domingo",
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--start-date",
            type=str,
            default="",
            help="Data inicial (YYYY-MM-DD). Se omitido, usa a proxima segunda-feira.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        start_date = self._resolve_start_date(options.get("start_date") or "")
        week_dates = [start_date + timedelta(days=offset) for offset in range(7)]
        operator_user = self._resolve_operator_user()

        ensure_default_accounts()
        ingredients = self._seed_ingredients()
        dishes = self._seed_dishes(ingredients)
        menu_days = self._seed_menu_week(
            week_dates=week_dates,
            dishes_by_weekday=dishes,
            operator_user=operator_user,
        )

        purchase_requests = self._simulate_purchase_requests(menu_days, operator_user)
        purchase = self._seed_purchase_for_week(
            week_dates=week_dates,
            menu_days=menu_days,
            operator_user=operator_user,
        )
        ingredient_cost_map = self._extract_ingredient_cost_map(purchase)
        self._simulate_ocr_flow(purchase=purchase)
        self._update_menu_prices_from_production_cost(
            menu_days=menu_days,
            ingredient_cost_map=ingredient_cost_map,
        )
        batches = self._seed_production(
            menu_days=menu_days, operator_user=operator_user
        )

        self.stdout.write(self.style.SUCCESS("Fluxo paraibano semanal concluido."))
        self.stdout.write(
            f"- Semana: {week_dates[0].isoformat()} a {week_dates[-1].isoformat()}"
        )
        self.stdout.write(f"- Cardapios processados: {len(menu_days)}")
        self.stdout.write(f"- Purchase requests simuladas: {purchase_requests}")
        self.stdout.write(
            f"- Compra utilizada: #{purchase.id} ({purchase.invoice_number})"
        )
        self.stdout.write(f"- Lotes de producao processados: {batches}")

    def _resolve_start_date(self, start_date_raw: str) -> date:
        if start_date_raw:
            try:
                return datetime.strptime(start_date_raw, "%Y-%m-%d").date()
            except ValueError as exc:
                raise CommandError(
                    "Formato invalido em --start-date. Use YYYY-MM-DD."
                ) from exc

        today = timezone.localdate()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        return today + timedelta(days=days_until_monday)

    def _resolve_operator_user(self):
        user_model = get_user_model()
        return (
            user_model.objects.filter(is_superuser=True).order_by("id").first()
            or user_model.objects.filter(is_staff=True).order_by("id").first()
        )

    def _create_text_image(self, *, slug: str, lines: list[str]) -> ContentFile:
        image = Image.new("RGB", (1200, 800), color=(255, 251, 245))
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        draw.rectangle([(24, 24), (1176, 776)], outline=(255, 106, 0), width=4)

        y = 52
        for line in lines:
            draw.text((52, y), line, fill=(32, 24, 18), font=font)
            y += 30

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return ContentFile(buffer.getvalue(), name=f"paraiba/{slug}.png")

    def _seed_ingredients(self) -> dict[str, Ingredient]:
        ingredient_map: dict[str, Ingredient] = {}
        for spec in self.INGREDIENT_SPECS:
            name = str(spec["name"]).strip().lower()
            unit = str(spec["unit"])
            ingredient, _ = Ingredient.objects.get_or_create(
                name=name,
                defaults={"unit": unit, "is_active": True},
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
                    slug=f"ingrediente-{name.replace(' ', '-')}",
                    lines=[
                        f"Insumo paraibano: {name}",
                        f"Unidade padrao: {unit}",
                        "Imagem sintetica para ambiente de producao local.",
                    ],
                )
                ingredient.image.save(image.name, image, save=False)
                updated_fields.append("image")

            if updated_fields:
                updated_fields.append("updated_at")
                ingredient.save(update_fields=updated_fields)

            ingredient_map[name] = ingredient

        return ingredient_map

    def _build_dish_ingredient_payload(
        self, *, spec: dict, ingredients: dict[str, Ingredient]
    ) -> list[dict]:
        return [
            {
                "ingredient": ingredients[item["ingredient"]],
                "quantity": item["quantity"],
                "unit": item["unit"],
            }
            for item in spec["ingredients"]
        ]

    def _seed_dishes(self, ingredients: dict[str, Ingredient]) -> dict[int, Dish]:
        dishes_by_weekday: dict[int, Dish] = {}

        for spec in self.DISH_SPECS:
            dish = Dish.objects.filter(name__iexact=spec["name"]).first()
            dish_data = {
                "name": spec["name"],
                "description": spec["description"],
                "yield_portions": 1,
            }
            payload = self._build_dish_ingredient_payload(
                spec=spec, ingredients=ingredients
            )

            if dish is None:
                dish = create_dish_with_ingredients(
                    dish_data=dish_data,
                    ingredients_payload=payload,
                )
            else:
                dish = update_dish_with_ingredients(
                    dish=dish,
                    dish_data=dish_data,
                    ingredients_payload=payload,
                )

            if not dish.image:
                image = self._create_text_image(
                    slug=f"prato-{spec['weekday']}-{dish.id}",
                    lines=[
                        "Cardapio paraibano caseiro",
                        f"Prato: {dish.name}",
                        f"Descricao: {dish.description}",
                    ],
                )
                dish.image.save(image.name, image, save=True)

            dishes_by_weekday[int(spec["weekday"])] = dish

        return dishes_by_weekday

    def _seed_menu_week(
        self,
        *,
        week_dates: list[date],
        dishes_by_weekday: dict[int, Dish],
        operator_user,
    ) -> list[MenuDay]:
        menu_days: list[MenuDay] = []
        for menu_date in week_dates:
            weekday = menu_date.weekday()
            dish = dishes_by_weekday[weekday]
            label = self.WEEKDAY_LABELS[weekday]
            existing_menu_day = MenuDay.objects.filter(menu_date=menu_date).first()
            if (
                existing_menu_day
                and existing_menu_day.items.filter(order_items__isnull=False).exists()
            ):
                # Evita excluir itens ja usados em pedidos confirmados.
                menu_days.append(existing_menu_day)
                continue

            menu_day = set_menu_for_day(
                menu_date=menu_date,
                title=f"Almoco paraibano - {label}",
                items_payload=[
                    {
                        "dish": dish,
                        "sale_price": Decimal("19.90"),
                        "available_qty": 20,
                        "is_active": True,
                    }
                ],
                created_by=operator_user,
                menu_day=existing_menu_day,
            )
            menu_days.append(menu_day)

        return menu_days

    def _simulate_purchase_requests(
        self, menu_days: list[MenuDay], operator_user
    ) -> int:
        created = 0
        for menu_day in menu_days:
            result = generate_purchase_request_from_menu(
                menu_day.id, requested_by=operator_user
            )
            if result.get("created"):
                created += 1
        return created

    def _build_week_requirement_map(
        self,
        *,
        menu_days: list[MenuDay],
    ) -> dict[int, dict]:
        requirement_map: dict[int, dict] = {}
        for menu_day in menu_days:
            menu_item = menu_day.items.select_related("dish").first()
            if menu_item is None:
                continue
            qty = Decimal(menu_item.available_qty or 20)
            for composition in menu_item.dish.dish_ingredients.select_related(
                "ingredient"
            ).all():
                ingredient = composition.ingredient
                ref = requirement_map.setdefault(
                    ingredient.id,
                    {
                        "ingredient": ingredient,
                        "unit": composition.unit or ingredient.unit,
                        "required_qty": Decimal("0"),
                    },
                )
                ref["required_qty"] += composition.quantity * qty
        return requirement_map

    def _seed_purchase_for_week(
        self,
        *,
        week_dates: list[date],
        menu_days: list[MenuDay],
        operator_user,
    ) -> Purchase:
        invoice_number = f"PB-CASEIRA-{week_dates[0].strftime('%Y%m%d')}"
        existing = Purchase.objects.filter(invoice_number=invoice_number).first()
        if existing is not None:
            return existing

        requirement_map = self._build_week_requirement_map(menu_days=menu_days)
        items_payload: list[dict] = []
        for payload in sorted(
            requirement_map.values(),
            key=lambda item: item["ingredient"].name,
        ):
            ingredient = payload["ingredient"]
            required_qty = Decimal(payload["required_qty"])
            purchase_qty = (required_qty * Decimal("1.20")).quantize(
                self.QTY_SCALE, rounding=ROUND_HALF_UP
            )
            if purchase_qty <= 0:
                continue

            unit_price = self.INGREDIENT_PRICE_MAP.get(
                ingredient.name, Decimal("10.00")
            )
            slug = ingredient.name.replace(" ", "-")
            label_front = self._create_text_image(
                slug=f"compra-{invoice_number.lower()}-{slug}-front",
                lines=[
                    "Compra paraibana - rotulo frontal",
                    f"Insumo: {ingredient.name}",
                    f"Quantidade: {purchase_qty} {ingredient.unit}",
                ],
            )
            label_back = self._create_text_image(
                slug=f"compra-{invoice_number.lower()}-{slug}-back",
                lines=[
                    "Compra paraibana - tabela nutricional (OCR)",
                    f"Produto: {ingredient.name}",
                    "Valor energetico 120 kcal",
                    "Carboidratos 10 g | Proteinas 8 g",
                    "Gorduras totais 3 g | Fibras 2 g | Sodio 90 mg",
                ],
            )
            product_img = self._create_text_image(
                slug=f"compra-{invoice_number.lower()}-{slug}-produto",
                lines=[
                    "Foto do produto (OCR)",
                    f"Produto: {ingredient.name}",
                ],
            )
            price_tag = self._create_text_image(
                slug=f"compra-{invoice_number.lower()}-{slug}-preco",
                lines=[
                    "Etiqueta de preco (OCR)",
                    f"Produto: {ingredient.name}",
                    f"Preco unitario: R$ {unit_price}",
                ],
            )

            items_payload.append(
                {
                    "ingredient": ingredient,
                    "qty": purchase_qty,
                    "unit": ingredient.unit,
                    "unit_price": unit_price,
                    "tax_amount": Decimal("0.00"),
                    "label_front_image": label_front,
                    "label_back_image": label_back,
                    "product_image": product_img,
                    "price_tag_image": price_tag,
                }
            )

        receipt_image = self._create_text_image(
            slug=f"recibo-{invoice_number.lower()}",
            lines=[
                "Compra semanal - culinaria paraibana",
                f"Nota fiscal: {invoice_number}",
                f"Periodo: {week_dates[0].isoformat()} a {week_dates[-1].isoformat()}",
                "Fornecedor: Mercado Central de Joao Pessoa",
            ],
        )

        return create_purchase_and_apply_stock(
            purchase_data={
                "supplier_name": "Mercado Central de Joao Pessoa",
                "invoice_number": invoice_number,
                "purchase_date": week_dates[0] - timedelta(days=1),
                "receipt_image": receipt_image,
            },
            items_payload=items_payload,
            buyer=operator_user,
        )

    def _extract_ingredient_cost_map(self, purchase: Purchase) -> dict[int, Decimal]:
        cost_map: dict[int, Decimal] = {}
        for item in purchase.items.select_related("ingredient").all():
            cost_map[item.ingredient_id] = Decimal(item.unit_price)
        return cost_map

    def _build_label_text_for_ocr(self, *, ingredient_name: str) -> str:
        return (
            f"PARAIBA_FLOW:{ingredient_name}\n"
            f"Produto: {ingredient_name}\n"
            "Marca: Mr Quentinha Insumos\n"
            "Peso liquido: 1 kg\n"
            "Porcao: 100 g\n"
            "Porcoes por embalagem: 10\n"
            "Valor energetico 130 kcal\n"
            "Carboidratos 12 g\n"
            "Proteinas 9 g\n"
            "Gorduras totais 3 g\n"
            "Gorduras saturadas 1 g\n"
            "Fibras 2 g\n"
            "Sodio 90 mg\n"
        )

    def _simulate_ocr_flow(self, *, purchase: Purchase) -> None:
        purchase_items = list(
            purchase.items.select_related("ingredient").order_by("id")
        )

        for item in purchase_items:
            ingredient_name = item.ingredient.name

            label_job = create_ocr_job(
                kind=OCRKind.LABEL_BACK,
                image=self._create_text_image(
                    slug=f"ocr-label-{purchase.id}-{item.id}",
                    lines=[
                        "OCR rotulo nutricional",
                        self._build_label_text_for_ocr(ingredient_name=ingredient_name),
                    ],
                ),
                raw_text=self._build_label_text_for_ocr(
                    ingredient_name=ingredient_name
                ),
            )
            apply_ocr_job(
                job_id=label_job.id,
                target_type="PURCHASE_ITEM",
                target_id=item.id,
                mode="merge",
            )

            if item.id % 3 == 0:
                apply_ocr_job(
                    job_id=label_job.id,
                    target_type="INGREDIENT",
                    target_id=item.ingredient_id,
                    mode="merge",
                )

            product_job = create_ocr_job(
                kind=OCRKind.PRODUCT,
                image=self._create_text_image(
                    slug=f"ocr-product-{purchase.id}-{item.id}",
                    lines=[
                        "OCR produto",
                        f"Produto: {ingredient_name}",
                        "Descricao: insumo regional paraibano",
                    ],
                ),
                raw_text=(
                    f"PARAIBA_FLOW_PRODUCT:{purchase.id}:{item.id}\n"
                    f"Produto: {ingredient_name}\n"
                    "Descricao: insumo regional paraibano"
                ),
            )
            apply_ocr_job(
                job_id=product_job.id,
                target_type="PURCHASE_ITEM",
                target_id=item.id,
                mode="merge",
            )

            price_job = create_ocr_job(
                kind=OCRKind.PRICE_TAG,
                image=self._create_text_image(
                    slug=f"ocr-price-{purchase.id}-{item.id}",
                    lines=[
                        "OCR etiqueta de preco",
                        f"Produto: {ingredient_name}",
                        f"R$ {item.unit_price}",
                    ],
                ),
                raw_text=(
                    f"PARAIBA_FLOW_PRICE:{purchase.id}:{item.id}\n"
                    f"Produto: {ingredient_name}\n"
                    f"Preco: {item.unit_price}\n"
                    f"Valor total: {item.unit_price}"
                ),
            )
            apply_ocr_job(
                job_id=price_job.id,
                target_type="PURCHASE_ITEM",
                target_id=item.id,
                mode="overwrite",
            )

        receipt_job = create_ocr_job(
            kind=OCRKind.RECEIPT,
            image=self._create_text_image(
                slug=f"ocr-receipt-{purchase.id}",
                lines=[
                    "OCR comprovante de compra",
                    f"Fornecedor: {purchase.supplier_name}",
                    f"NF: {purchase.invoice_number}",
                    f"Total: {purchase.total_amount}",
                ],
            ),
            raw_text=(
                f"Fornecedor: {purchase.supplier_name}\n"
                f"NF: {purchase.invoice_number}\n"
                f"Total: {purchase.total_amount}"
            ),
        )
        apply_ocr_job(
            job_id=receipt_job.id,
            target_type="PURCHASE",
            target_id=purchase.id,
            mode="overwrite",
        )

    def _calculate_dish_cost(
        self, *, dish: Dish, ingredient_cost_map: dict[int, Decimal]
    ) -> Decimal:
        base_cost = Decimal("0")
        for row in dish.dish_ingredients.select_related("ingredient").all():
            unit_cost = ingredient_cost_map.get(row.ingredient_id, Decimal("0"))
            base_cost += Decimal(row.quantity) * unit_cost
        return base_cost.quantize(self.MONEY_SCALE, rounding=ROUND_HALF_UP)

    def _build_sale_price(self, *, dish_cost: Decimal) -> Decimal:
        operational = (dish_cost * self.OVERHEAD_FACTOR) + self.PACKAGING_COST
        sale_price = operational * self.MARKUP_FACTOR
        if sale_price < Decimal("18.00"):
            sale_price = Decimal("18.00")
        return sale_price.quantize(self.MONEY_SCALE, rounding=ROUND_HALF_UP)

    def _update_menu_prices_from_production_cost(
        self,
        *,
        menu_days: list[MenuDay],
        ingredient_cost_map: dict[int, Decimal],
    ) -> None:
        for menu_day in menu_days:
            menu_item = menu_day.items.select_related("dish").first()
            if menu_item is None:
                continue
            dish_cost = self._calculate_dish_cost(
                dish=menu_item.dish,
                ingredient_cost_map=ingredient_cost_map,
            )
            sale_price = self._build_sale_price(dish_cost=dish_cost)
            if menu_item.sale_price != sale_price:
                menu_item.sale_price = sale_price
                menu_item.save(update_fields=["sale_price"])

    def _seed_production(self, *, menu_days: list[MenuDay], operator_user) -> int:
        processed = 0
        for menu_day in menu_days:
            menu_item = menu_day.items.first()
            if menu_item is None:
                continue
            batch = ProductionBatch.objects.filter(
                production_date=menu_day.menu_date
            ).first()
            if batch is None:
                batch = create_batch_for_date(
                    production_date=menu_day.menu_date,
                    items_payload=[
                        {
                            "menu_item": menu_item,
                            "qty_planned": 20,
                            "qty_produced": 20,
                            "qty_waste": 0,
                            "note": "Lote semanal culinaria paraibana",
                        }
                    ],
                    note=(
                        "Producao semanal paraibana - "
                        f"{menu_day.menu_date.isoformat()}"
                    ),
                    created_by=operator_user,
                )
            if batch.status != ProductionBatchStatus.DONE:
                complete_batch(batch_id=batch.id)
            menu_item.refresh_from_db()
            if menu_item.available_qty != 20 or not menu_item.is_active:
                menu_item.available_qty = 20
                menu_item.is_active = True
                menu_item.save(update_fields=["available_qty", "is_active"])
            processed += 1
        return processed
