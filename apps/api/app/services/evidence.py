from typing import Literal

from pydantic import Field

from app.schemas.tools import DTO, KnowledgeResult, ProductSearchResult, QuoteDTO
from app.services.errors import DomainError


class Source(DTO):
    kind: Literal["product", "knowledge", "price_rule"]
    source_id: str
    title: str
    excerpt: str
    source: str


class EvidenceBundle(DTO):
    sources: list[Source] = Field(default_factory=list)

    @classmethod
    def from_results(cls, *results):
        sources = {}
        for result in results:
            if isinstance(result, ProductSearchResult):
                entries = [
                    Source(
                        kind="product",
                        source_id=p.product_id,
                        title=p.name_tr,
                        excerpt=f"{p.price_try:.2f} TRY; stok {p.stock_qty}",
                        source=p.sku,
                    )
                    for p in result.recommendations + result.unavailable_matches
                ]
            elif isinstance(result, KnowledgeResult):
                entries = [
                    Source(
                        kind="knowledge",
                        source_id=k.knowledge_id,
                        title=k.title,
                        excerpt=k.body,
                        source=k.source,
                    )
                    for k in result.entries
                ]
            elif isinstance(result, QuoteDTO):
                entries = [
                    Source(
                        kind="product",
                        source_id=p.product_id,
                        title=p.name_tr,
                        excerpt=f"{p.quantity} adet; snapshot {p.unit_price_try:.2f} TRY",
                        source=p.sku,
                    )
                    for p in result.items
                ]
                entries += [
                    Source(
                        kind="price_rule",
                        source_id=r,
                        title=r,
                        excerpt="Teklife uygulanan fiyat kuralı",
                        source=r,
                    )
                    for r in result.rule_ids
                ]
            else:
                raise TypeError("Unsupported evidence result")
            for source in entries:
                sources[(source.kind, source.source_id)] = source
        return cls(sources=list(sources.values()))

    def require(self, ids: list[tuple[str, str]]) -> list[Source]:
        by_id = {(s.kind, s.source_id): s for s in self.sources}
        if any(key not in by_id for key in ids):
            raise DomainError("SOURCE_NOT_GROUNDED", "Yanıt kaynağı doğrulanamadı.")
        return [by_id[key] for key in ids]
