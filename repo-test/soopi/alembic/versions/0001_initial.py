"""Initial standalone Soopi schema; CMP-SOOPI-BACKEND revision 1.

This migration freezes the physical schema and never imports live ORM metadata.
"""

import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def common():
    return [
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    ]


def upgrade():
    op.create_table(
        "users",
        *common(),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("phone", sa.String(20)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_table(
        "addresses",
        *common(),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("recipient", sa.String(120), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("line1", sa.String(255), nullable=False),
        sa.Column("ward", sa.String(120), nullable=False),
        sa.Column("district", sa.String(120), nullable=False),
        sa.Column("province", sa.String(120), nullable=False),
    )
    op.create_table(
        "refresh_sessions",
        *common(),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("token_hash", name=op.f("uq_refresh_sessions_token_hash")),
    )
    op.create_table(
        "categories",
        *common(),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(160), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("slug", name=op.f("uq_categories_slug")),
    )
    op.create_table(
        "products",
        *common(),
        sa.Column("category_id", sa.Uuid(), sa.ForeignKey("categories.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(220), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("slug", name=op.f("uq_products_slug")),
    )
    op.create_table(
        "product_variants",
        *common(),
        sa.Column("product_id", sa.Uuid(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("sku", sa.String(80), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("price", sa.Numeric(14, 0), nullable=False),
        sa.Column("stock", sa.BigInteger(), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.CheckConstraint("price >= 0", name=op.f("ck_product_variants_nonnegative_price")),
        sa.CheckConstraint("stock >= 0", name=op.f("ck_product_variants_nonnegative_stock")),
        sa.UniqueConstraint("sku", name=op.f("uq_product_variants_sku")),
    )
    op.create_table(
        "carts",
        *common(),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id")),
        sa.Column("guest_token_hash", sa.String(64)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "(user_id IS NOT NULL AND guest_token_hash IS NULL) OR "
            "(user_id IS NULL AND guest_token_hash IS NOT NULL AND expires_at IS NOT NULL)",
            name=op.f("ck_carts_single_owner"),
        ),
        sa.UniqueConstraint("user_id", name=op.f("uq_carts_user_id")),
        sa.UniqueConstraint("guest_token_hash", name=op.f("uq_carts_guest_token_hash")),
    )
    op.create_table(
        "cart_items",
        *common(),
        sa.Column(
            "cart_id", sa.Uuid(), sa.ForeignKey("carts.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("variant_id", sa.Uuid(), sa.ForeignKey("product_variants.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.UniqueConstraint("cart_id", "variant_id", name=op.f("uq_cart_items_cart_id")),
        sa.CheckConstraint(
            "quantity > 0 AND quantity <= 999", name=op.f("ck_cart_items_valid_quantity")
        ),
    )
    payment_method = sa.Enum(
        "cod", "momo", "vnpay", name="paymentmethod", native_enum=False, create_constraint=True
    )
    op.create_table(
        "orders",
        *common(),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("idempotency_key", sa.String(100), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "confirmed",
                "shipped",
                "delivered",
                "cancelled",
                "expired",
                name="orderstatus",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("payment_method", payment_method, nullable=False),
        sa.Column(
            "payment_status",
            sa.Enum(
                "unpaid",
                "paid",
                "refund_required",
                name="paymentstatus",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("subtotal", sa.Numeric(14, 0), nullable=False),
        sa.Column("shipping_fee", sa.Numeric(14, 0), nullable=False),
        sa.Column("total", sa.Numeric(14, 0), nullable=False),
        sa.Column("shipping_address", sa.JSON(), nullable=False),
        sa.Column("note", sa.String(500), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("stock_released_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("user_id", "idempotency_key", name=op.f("uq_orders_user_id")),
        sa.CheckConstraint(
            "subtotal >= 0 AND shipping_fee >= 0", name=op.f("ck_orders_nonnegative_amounts")
        ),
        sa.CheckConstraint("total = subtotal + shipping_fee", name=op.f("ck_orders_correct_total")),
    )
    op.create_table(
        "order_items",
        *common(),
        sa.Column("order_id", sa.Uuid(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("variant_id", sa.Uuid(), sa.ForeignKey("product_variants.id"), nullable=False),
        sa.Column("product_name", sa.String(200), nullable=False),
        sa.Column("variant_name", sa.String(120), nullable=False),
        sa.Column("sku", sa.String(80), nullable=False),
        sa.Column("unit_price", sa.Numeric(14, 0), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("line_total", sa.Numeric(14, 0), nullable=False),
        sa.CheckConstraint("quantity > 0", name=op.f("ck_order_items_positive_quantity")),
        sa.CheckConstraint("unit_price >= 0", name=op.f("ck_order_items_nonnegative_price")),
        sa.CheckConstraint(
            "line_total = unit_price * quantity", name=op.f("ck_order_items_correct_total")
        ),
    )
    op.create_table(
        "payment_attempts",
        *common(),
        sa.Column("order_id", sa.Uuid(), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column(
            "provider",
            sa.Enum(
                "cod",
                "momo",
                "vnpay",
                name="paymentmethod",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("request_id", sa.String(50), nullable=False),
        sa.Column("amount", sa.Numeric(14, 0), nullable=False),
        sa.Column("payment_url", sa.String(4096)),
        sa.Column("transaction_id", sa.String(100)),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("order_id", name=op.f("uq_payment_attempts_order_id")),
        sa.UniqueConstraint("request_id", name=op.f("uq_payment_attempts_request_id")),
        sa.UniqueConstraint(
            "provider", "transaction_id", name=op.f("uq_payment_attempts_provider")
        ),
    )
    for table, column in (
        ("addresses", "user_id"),
        ("refresh_sessions", "user_id"),
        ("products", "category_id"),
        ("product_variants", "product_id"),
        ("cart_items", "cart_id"),
        ("orders", "user_id"),
        ("orders", "expires_at"),
        ("order_items", "order_id"),
    ):
        op.create_index(op.f(f"ix_{table}_{column}"), table, [column])


def downgrade():
    for table in (
        "payment_attempts",
        "order_items",
        "orders",
        "cart_items",
        "carts",
        "product_variants",
        "products",
        "categories",
        "refresh_sessions",
        "addresses",
        "users",
    ):
        op.drop_table(table)
