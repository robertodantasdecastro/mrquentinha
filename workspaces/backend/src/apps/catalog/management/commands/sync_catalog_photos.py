from __future__ import annotations

import json
import mimetypes
from dataclasses import dataclass
from html import escape
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from apps.catalog.models import Dish, Ingredient

COMMONS_API_URL = "https://commons.wikimedia.org/w/api.php"
DEFAULT_TIMEOUT_SECONDS = 20
HTTP_USER_AGENT = "MrQuentinhaBot/1.0 (catalog-photo-sync)"
PLACEHOLDER_COLORS = {
    "dish": ("#FF6A00", "#111827"),
    "ingredient": ("#059669", "#0F172A"),
}

INGREDIENT_QUERY_HINTS = {
    "arroz branco": "white rice cooked food",
    "arroz integral": "brown rice cooked food",
    "feijao carioca": "pinto beans cooked",
    "peito de frango": "chicken breast cooked",
    "carne moida": "ground beef cooked",
    "tilapia": "tilapia fish cooked",
    "carne bovina": "beef meat cooked",
    "batata doce": "sweet potato food",
    "alface": "lettuce vegetable",
    "tomate": "tomato vegetable",
    "pepino": "cucumber vegetable",
    "ovo": "chicken egg food",
    "cenoura": "carrot vegetable",
    "abobrinha": "zucchini vegetable",
    "brocolis": "broccoli vegetable",
    "alho": "garlic ingredient",
    "cebola": "onion ingredient",
    "azeite": "olive oil bottle",
    "sal": "salt ingredient",
}

DISH_QUERY_HINTS = {
    "frango grelhado": "grilled chicken dish",
    "carne moida acebolada": "ground beef onion dish",
    "tilapia assada": "baked tilapia dish",
    "arroz soltinho": "cooked rice dish",
    "arroz integral": "brown rice dish",
    "feijao caseiro": "beans dish cooked",
    "legumes salteados": "sauteed vegetables dish",
    "pure de batata doce": "mashed sweet potato dish",
    "salada verde": "green salad dish",
    "omelete de legumes": "vegetable omelette dish",
    "carne de panela": "beef stew dish",
}

INGREDIENT_FALLBACK_IMAGE_URLS = {
    "arroz branco": "https://images.unsplash.com/photo-1603133872878-684f208fb84b",
    "arroz integral": "https://images.unsplash.com/photo-1515003197210-e0cd71810b5f",
    "feijao carioca": "https://images.unsplash.com/photo-1515543904379-3d757afe72e3",
    "peito de frango": "https://images.unsplash.com/photo-1604503468506-a8da13d82791",
    "carne moida": "https://images.unsplash.com/photo-1603360946369-dc9bb6258143",
    "tilapia": "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2",
    "carne bovina": "https://images.unsplash.com/photo-1544025162-d76694265947",
    "batata doce": "https://images.unsplash.com/photo-1596097635121-14b63b7a0c19",
    "alface": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd",
    "tomate": "https://images.unsplash.com/photo-1546470427-e5ac89cd0b8a",
    "pepino": "https://images.unsplash.com/photo-1604977042946-1eecc30f269e",
    "ovo": "https://images.unsplash.com/photo-1506976785307-8732e854ad03",
    "cenoura": "https://images.unsplash.com/photo-1447175008436-054170c2e979",
    "abobrinha": "https://images.unsplash.com/photo-1594282486552-05a79f66a9b8",
    "brocolis": "https://images.unsplash.com/photo-1459411621453-7b03977f4bfc",
    "alho": "https://images.unsplash.com/photo-1615478503562-ec2d8aa0e24e",
    "cebola": "https://images.unsplash.com/photo-1508747703725-719777637510",
    "azeite": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5",
    "sal": "https://images.unsplash.com/photo-1518110925495-5fe2fda0442f",
}

DISH_FALLBACK_IMAGE_URLS = {
    "frango grelhado": "https://images.unsplash.com/photo-1532550907401-a500c9a57435",
    "carne moida acebolada": "https://images.unsplash.com/photo-1559847844-5315695dadae",
    "tilapia assada": "https://images.unsplash.com/photo-1485963631004-f2f00b1d6606",
    "arroz soltinho": "https://images.unsplash.com/photo-1515003197210-e0cd71810b5f",
    "arroz integral": "https://images.unsplash.com/photo-1603133872878-684f208fb84b",
    "feijao caseiro": "https://images.unsplash.com/photo-1515543904379-3d757afe72e3",
    "legumes salteados": "https://images.unsplash.com/photo-1547592166-23ac45744acd",
    "pure de batata doce": "https://images.unsplash.com/photo-1608755727748-dfa2e44f4f4e",
    "salada verde": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd",
    "omelete de legumes": "https://images.unsplash.com/photo-1525351484163-7529414344d8",
    "carne de panela": "https://images.unsplash.com/photo-1544025162-d76694265947",
}

GENERIC_INGREDIENT_FALLBACK_URL = (
    "https://images.unsplash.com/photo-1547592166-23ac45744acd"
)
GENERIC_DISH_FALLBACK_URL = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c"


@dataclass
class ImageCandidate:
    url: str
    mime: str


class Command(BaseCommand):
    help = (
        "Sincroniza fotos de pratos e insumos no banco, buscando imagens no "
        "Wikimedia Commons e salvando em MEDIA_ROOT."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--only",
            choices=["all", "ingredients", "dishes"],
            default="all",
            help="Define se sincroniza apenas ingredientes, apenas pratos ou ambos.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help=(
                "Limita a quantidade de registros processados por grupo "
                "(0 = sem limite)."
            ),
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Sobrescreve fotos existentes.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Executa a busca sem gravar arquivos no banco.",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=DEFAULT_TIMEOUT_SECONDS,
            help="Timeout de rede em segundos para busca/download das imagens.",
        )

    def handle(self, *args, **options):
        only = str(options["only"])
        limit = int(options["limit"])
        force = bool(options["force"])
        dry_run = bool(options["dry_run"])
        timeout = int(options["timeout"])

        if limit < 0:
            raise CommandError("--limit nao pode ser negativo.")
        if timeout <= 0:
            raise CommandError("--timeout precisa ser maior que zero.")

        self.stdout.write(
            self.style.NOTICE(
                "Iniciando sincronizacao de fotos do catalogo "
                f"(only={only}, limit={limit or 'sem limite'}, "
                f"force={force}, dry_run={dry_run})..."
            )
        )

        if only in {"all", "ingredients"}:
            ingredient_stats = self._sync_ingredients(
                force=force,
                dry_run=dry_run,
                timeout=timeout,
                limit=limit,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "Ingredientes -> "
                    f"atualizados={ingredient_stats['updated']} "
                    f"ignorados={ingredient_stats['skipped']} "
                    f"falhas={ingredient_stats['failed']}"
                )
            )

        if only in {"all", "dishes"}:
            dish_stats = self._sync_dishes(
                force=force,
                dry_run=dry_run,
                timeout=timeout,
                limit=limit,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "Pratos -> "
                    f"atualizados={dish_stats['updated']} "
                    f"ignorados={dish_stats['skipped']} "
                    f"falhas={dish_stats['failed']}"
                )
            )

        self.stdout.write(self.style.SUCCESS("Sincronizacao de fotos finalizada."))

    def _sync_ingredients(
        self,
        *,
        force: bool,
        dry_run: bool,
        timeout: int,
        limit: int,
    ) -> dict[str, int]:
        queryset = Ingredient.objects.all().order_by("name")
        if limit > 0:
            queryset = queryset[:limit]

        stats = {"updated": 0, "skipped": 0, "failed": 0}
        for ingredient in queryset:
            updated = self._sync_entity_image(
                entity=ingredient,
                kind="ingredient",
                query_hints=INGREDIENT_QUERY_HINTS,
                force=force,
                dry_run=dry_run,
                timeout=timeout,
            )
            if updated is True:
                stats["updated"] += 1
            elif updated is None:
                stats["skipped"] += 1
            else:
                stats["failed"] += 1
        return stats

    def _sync_dishes(
        self,
        *,
        force: bool,
        dry_run: bool,
        timeout: int,
        limit: int,
    ) -> dict[str, int]:
        queryset = Dish.objects.all().order_by("name")
        if limit > 0:
            queryset = queryset[:limit]

        stats = {"updated": 0, "skipped": 0, "failed": 0}
        for dish in queryset:
            updated = self._sync_entity_image(
                entity=dish,
                kind="dish",
                query_hints=DISH_QUERY_HINTS,
                force=force,
                dry_run=dry_run,
                timeout=timeout,
            )
            if updated is True:
                stats["updated"] += 1
            elif updated is None:
                stats["skipped"] += 1
            else:
                stats["failed"] += 1
        return stats

    def _sync_entity_image(
        self,
        *,
        entity: Ingredient | Dish,
        kind: str,
        query_hints: dict[str, str],
        force: bool,
        dry_run: bool,
        timeout: int,
    ) -> bool | None:
        if entity.image and not force:
            self.stdout.write(
                f"[skip] {kind}#{entity.id} {entity.name}: imagem ja existe."
            )
            return None

        search_query = self._build_search_query(entity.name, query_hints, kind=kind)
        try:
            candidates = self._search_commons_candidates(
                query=search_query,
                timeout=timeout,
            )
        except CommandError as exc:
            self.stdout.write(
                self.style.ERROR(
                    f"[fail] {kind}#{entity.id} {entity.name}: erro de busca ({exc})."
                )
            )
            candidates = []

        fallback_url = self._resolve_fallback_image_url(name=entity.name, kind=kind)
        if fallback_url:
            candidates.append(ImageCandidate(url=fallback_url, mime="image/jpeg"))

        if not candidates:
            self.stdout.write(
                self.style.WARNING(
                    f"[warn] {kind}#{entity.id} {entity.name}: sem candidatos de busca."
                )
            )

        for candidate in candidates:
            try:
                image_bytes, extension = self._download_image(
                    image_url=candidate.url,
                    mime=candidate.mime,
                    timeout=timeout,
                )
            except CommandError:
                continue

            if dry_run:
                self.stdout.write(
                    self.style.NOTICE(
                        f"[dry-run] {kind}#{entity.id} "
                        f"{entity.name}: imagem encontrada."
                    )
                )
                return True

            base_slug = slugify(entity.name) or f"{kind}-{entity.id}"
            filename = f"catalog/{kind}s/sync/{base_slug}-{entity.id}.{extension}"
            entity.image.save(filename, ContentFile(image_bytes), save=False)
            entity.save(update_fields=["image", "updated_at"])
            self.stdout.write(
                self.style.SUCCESS(
                    f"[ok] {kind}#{entity.id} {entity.name}: imagem sincronizada."
                )
            )
            return True

        if dry_run:
            self.stdout.write(
                self.style.NOTICE(
                    f"[dry-run] {kind}#{entity.id} "
                    f"{entity.name}: usaria placeholder local."
                )
            )
            return True

        placeholder_bytes = self._build_placeholder_svg(name=entity.name, kind=kind)
        base_slug = slugify(entity.name) or f"{kind}-{entity.id}"
        filename = f"catalog/{kind}s/sync/{base_slug}-{entity.id}.svg"
        entity.image.save(filename, ContentFile(placeholder_bytes), save=False)
        entity.save(update_fields=["image", "updated_at"])
        self.stdout.write(
            self.style.SUCCESS(
                f"[ok] {kind}#{entity.id} {entity.name}: " "placeholder local aplicado."
            )
        )
        return True

    def _resolve_fallback_image_url(self, *, name: str, kind: str) -> str:
        key = name.strip().lower()
        if kind == "dish":
            return DISH_FALLBACK_IMAGE_URLS.get(key, GENERIC_DISH_FALLBACK_URL)
        return INGREDIENT_FALLBACK_IMAGE_URLS.get(key, GENERIC_INGREDIENT_FALLBACK_URL)

    def _build_search_query(
        self,
        name: str,
        query_hints: dict[str, str],
        *,
        kind: str,
    ) -> str:
        key = name.strip().lower()
        if key in query_hints:
            return query_hints[key]

        if kind == "dish":
            return f"{name} food dish"

        return f"{name} ingredient food"

    def _search_commons_candidates(
        self,
        *,
        query: str,
        timeout: int,
    ) -> list[ImageCandidate]:
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,
            "gsrlimit": 8,
            "prop": "imageinfo",
            "iiprop": "url|mime",
        }
        api_url = f"{COMMONS_API_URL}?{urlencode(params)}"
        payload = self._load_json(url=api_url, timeout=timeout)

        pages = payload.get("query", {}).get("pages", {})
        candidates: list[ImageCandidate] = []
        for page in pages.values():
            image_info = page.get("imageinfo", [])
            if not image_info:
                continue

            first_info = image_info[0]
            image_url = str(first_info.get("url", "")).strip()
            mime = str(first_info.get("mime", "")).strip().lower()
            if not image_url or not mime.startswith("image/"):
                continue

            candidates.append(ImageCandidate(url=image_url, mime=mime))

        return candidates

    def _download_image(
        self,
        *,
        image_url: str,
        mime: str,
        timeout: int,
    ) -> tuple[bytes, str]:
        request = Request(
            image_url,
            headers={
                "User-Agent": HTTP_USER_AGENT,
            },
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                image_bytes = response.read()
                content_type = str(response.headers.get("Content-Type", "")).lower()
        except (HTTPError, URLError, TimeoutError) as exc:
            raise CommandError(f"falha ao baixar imagem: {exc}") from exc

        if not image_bytes:
            raise CommandError("imagem vazia.")

        resolved_extension = self._resolve_extension(
            content_type=content_type,
            image_url=image_url,
            fallback_mime=mime,
        )
        return image_bytes, resolved_extension

    def _resolve_extension(
        self,
        *,
        content_type: str,
        image_url: str,
        fallback_mime: str,
    ) -> str:
        mime_value = content_type.split(";")[0].strip() or fallback_mime
        guessed_extension = mimetypes.guess_extension(mime_value) or ""
        if guessed_extension:
            return guessed_extension.lstrip(".")

        for extension in ("jpg", "jpeg", "png", "webp"):
            if image_url.lower().endswith(f".{extension}"):
                return extension

        return "jpg"

    def _load_json(self, *, url: str, timeout: int) -> dict[str, Any]:
        request = Request(
            url,
            headers={
                "User-Agent": HTTP_USER_AGENT,
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError) as exc:
            raise CommandError(f"falha ao consultar API externa: {exc}") from exc

        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise CommandError("resposta JSON invalida da API externa.") from exc

    def _build_placeholder_svg(self, *, name: str, kind: str) -> bytes:
        primary_color, text_color = PLACEHOLDER_COLORS.get(
            kind,
            ("#FF6A00", "#111827"),
        )
        safe_kind = "Prato" if kind == "dish" else "Ingrediente"
        safe_name = escape(name.strip() or "Item")
        svg = (
            "<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='800' "
            "viewBox='0 0 1200 800'>"
            "<defs>"
            f"<linearGradient id='bg' x1='0' y1='0' x2='1' y2='1'>"
            f"<stop offset='0%' stop-color='{primary_color}' stop-opacity='0.20'/>"
            "<stop offset='100%' stop-color='#FFFFFF' stop-opacity='1'/>"
            "</linearGradient>"
            "</defs>"
            "<rect width='1200' height='800' fill='url(#bg)'/>"
            f"<text x='64' y='160' font-size='52' fill='{text_color}' "
            "font-family='Arial, Helvetica, sans-serif' font-weight='700'>"
            f"{safe_kind}</text>"
            f"<text x='64' y='260' font-size='72' fill='{text_color}' "
            "font-family='Arial, Helvetica, sans-serif' font-weight='700'>"
            f"{safe_name}</text>"
            f"<text x='64' y='730' font-size='28' fill='{text_color}' "
            "font-family='Arial, Helvetica, sans-serif' opacity='0.75'>"
            "Mr Quentinha - imagem de fallback</text>"
            "</svg>"
        )
        return svg.encode("utf-8")
