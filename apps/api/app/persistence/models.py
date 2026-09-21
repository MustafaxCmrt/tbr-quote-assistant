"""SQLAlchemy 2 Core schema. Money stays NUMERIC/Decimal, never binary float."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

metadata = sa.MetaData(
    naming_convention={
        "ix": "ix_%(table_name)s_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)


def text(name, **kwargs):
    return sa.Column(name, sa.Text, nullable=False, **kwargs)


def integer(name, **kwargs):
    return sa.Column(name, sa.Integer, nullable=False, **kwargs)


def money(name):
    return sa.Column(name, sa.Numeric(14, 2), nullable=False)


def jsonb(name, default):
    return sa.Column(name, JSONB, nullable=False, server_default=sa.text(default))


def created_at():
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )


products = sa.Table(
    "products",
    metadata,
    text("product_id", primary_key=True),
    text("sku", unique=True),
    text("name_tr"),
    text("category"),
    text("brand"),
    money("price_try"),
    integer("stock_qty"),
    sa.Column("active", sa.Boolean, nullable=False),
    integer("min_order_qty"),
    integer("delivery_days"),
    integer("warranty_months"),
    jsonb("tags", "'[]'"),
    jsonb("aliases", "'{}'"),
    jsonb("substitute_product_ids", "'[]'"),
    text("notes"),
    sa.CheckConstraint("price_try >= 0", name="price_nonnegative"),
    sa.CheckConstraint("stock_qty >= 0", name="stock_nonnegative"),
    sa.CheckConstraint("min_order_qty > 0", name="min_order_positive"),
    sa.CheckConstraint("delivery_days >= 0 AND warranty_months >= 0", name="durations_nonnegative"),
)
knowledge_entries = sa.Table(
    "knowledge_entries",
    metadata,
    text("knowledge_id", primary_key=True),
    text("topic"),
    text("locale"),
    text("title"),
    text("body"),
    text("source"),
    jsonb("applies_to", "'[]'"),
    sa.Column("effective_from", sa.Date, nullable=False),
    sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
)
customers = sa.Table(
    "customers",
    metadata,
    text("customer_id", primary_key=True),
    text("name"),
    text("segment"),
    text("city"),
    text("price_tier"),
    money("credit_limit_try"),
    sa.Column("allow_backorder", sa.Boolean, nullable=False),
    text("default_locale"),
    text("notes"),
    sa.CheckConstraint("credit_limit_try >= 0", name="credit_nonnegative"),
)
price_rules = sa.Table(
    "price_rules",
    metadata,
    text("rule_id", primary_key=True),
    text("name"),
    text("condition"),
    money("discount_percent"),
    sa.CheckConstraint("discount_percent >= 0 AND discount_percent <= 100", name="discount_range"),
)
quotes = sa.Table(
    "quotes",
    metadata,
    text("quote_id", primary_key=True),
    sa.Column("customer_id", sa.Text, sa.ForeignKey("customers.customer_id"), nullable=False),
    text("status"),
    text("created_by_channel"),
    text("currency"),
    text("notes"),
    integer("version", server_default="1"),
    created_at(),
    sa.UniqueConstraint("quote_id", "customer_id"),
    sa.CheckConstraint("version > 0", name="version_positive"),
)
quote_items = sa.Table(
    "quote_items",
    metadata,
    text("quote_item_id", primary_key=True),
    sa.Column("quote_id", sa.Text, sa.ForeignKey("quotes.quote_id"), nullable=False),
    sa.Column("product_id", sa.Text, sa.ForeignKey("products.product_id"), nullable=False),
    integer("quantity"),
    money("unit_price_try"),
    text("status"),
    text("source_message_id"),
    text("idempotency_key"),
    text("fulfillment_status", server_default="in_stock"),
    sa.Column("replaced_by", sa.Text, sa.ForeignKey("quote_items.quote_item_id")),
    created_at(),
    sa.CheckConstraint("status IN ('active','removed','replaced')", name="status_valid"),
    sa.CheckConstraint(
        "quantity >= 0 AND (status != 'active' OR quantity > 0)", name="quantity_valid"
    ),
    sa.CheckConstraint("unit_price_try >= 0", name="price_nonnegative"),
    sa.CheckConstraint(
        "fulfillment_status IN ('in_stock','backorder','out_of_stock')", name="fulfillment_valid"
    ),
    sa.CheckConstraint(
        "replaced_by IS NULL OR replaced_by != quote_item_id", name="replacement_not_self"
    ),
)
sa.Index(
    "uq_quote_active_product",
    quote_items.c.quote_id,
    quote_items.c.product_id,
    unique=True,
    postgresql_where=quote_items.c.status == "active",
)
chat_sessions = sa.Table(
    "chat_sessions",
    metadata,
    text("session_id", primary_key=True),
    text("customer_id"),
    text("quote_id"),
    text("channel"),
    text("locale"),
    created_at(),
    sa.ForeignKeyConstraint(["quote_id", "customer_id"], ["quotes.quote_id", "quotes.customer_id"]),
)
chat_messages = sa.Table(
    "chat_messages",
    metadata,
    sa.Column("session_id", sa.Text, sa.ForeignKey("chat_sessions.session_id"), primary_key=True),
    text("message_id", primary_key=True),
    text("body"),
    text("payload_hash"),
    jsonb("trusted_constraints", "'{}'"),
    jsonb("persisted_plan", "'[]'"),
    text("status", server_default="pending"),
    sa.Column("final_response", JSONB),
    sa.Column("lease_until", sa.DateTime(timezone=True)),
    created_at(),
    sa.CheckConstraint(
        "status IN ('pending','processing','completed','failed')", name="status_valid"
    ),
)
TOOL_NAMES = (
    "search_products",
    "get_knowledge_entries",
    "get_quote",
    "add_to_quote",
    "update_quote_item",
    "replace_with_alternative",
)
tool_call_logs = sa.Table(
    "tool_call_logs",
    metadata,
    sa.Column("log_id", sa.BigInteger, primary_key=True, autoincrement=True),
    text("session_id"),
    text("message_id"),
    text("attempt_id"),
    integer("tool_sequence"),
    text("tool_name"),
    jsonb("input", "'{}'"),
    jsonb("output", "'{}'"),
    jsonb("sources", "'[]'"),
    sa.Column("success", sa.Boolean, nullable=False),
    sa.Column("replayed", sa.Boolean, nullable=False, server_default=sa.false()),
    sa.Column("mutation_applied", sa.Boolean, nullable=False, server_default=sa.false()),
    integer("duration_ms", server_default="0"),
    created_at(),
    sa.ForeignKeyConstraint(
        ["session_id", "message_id"], ["chat_messages.session_id", "chat_messages.message_id"]
    ),
    sa.UniqueConstraint("session_id", "message_id", "attempt_id", "tool_sequence"),
    sa.CheckConstraint("tool_sequence > 0 AND duration_ms >= 0", name="sequence_duration_valid"),
    sa.CheckConstraint("NOT (replayed AND mutation_applied)", name="replay_has_no_mutation"),
    sa.CheckConstraint("tool_name IN " + str(TOOL_NAMES), name="tool_valid"),
)
mutation_receipts = sa.Table(
    "mutation_receipts",
    metadata,
    sa.Column("quote_id", sa.Text, sa.ForeignKey("quotes.quote_id"), primary_key=True),
    text("idempotency_key", primary_key=True),
    text("session_id"),
    text("message_id"),
    integer("action_index"),
    text("operation"),
    text("payload_hash"),
    jsonb("before", "'{}'"),
    jsonb("after", "'{}'"),
    jsonb("result", "'{}'"),
    integer("committed_version"),
    created_at(),
    sa.ForeignKeyConstraint(
        ["session_id", "message_id"], ["chat_messages.session_id", "chat_messages.message_id"]
    ),
    sa.CheckConstraint("action_index >= 0 AND committed_version > 0", name="index_version_valid"),
    sa.CheckConstraint(
        "operation IN ('add_to_quote','update_quote_item','replace_with_alternative')",
        name="operation_valid",
    ),
)
# Operational marker: only written in the same transaction as a successful full seed.
bootstrap_state = sa.Table(
    "bootstrap_state",
    metadata,
    text("seed_id", primary_key=True),
    text("source_sha256"),
    created_at(),
)
SEED_TABLES = (products, knowledge_entries, customers, quotes, quote_items, price_rules)
