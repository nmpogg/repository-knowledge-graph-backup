import importlib.util
from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect

from app.models import Base
from app.schemas.cart import CartAdd
from app.schemas.product import ProductPatch, VariantInput


def test_initial_migration_matches_models_and_downgrades():
    # Run the frozen migration on an in-memory DB, then compare physical schema.
    migration_path = Path("alembic/versions/0001_initial.py")
    spec = importlib.util.spec_from_file_location("soopi_initial_migration", migration_path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        context = MigrationContext.configure(connection)
        with Operations.context(context):
            migration.upgrade()
            assert set(inspect(connection).get_table_names()) == set(Base.metadata.tables)
            assert compare_metadata(context, Base.metadata) == []
            migration.downgrade()
            assert inspect(connection).get_table_names() == []
    engine.dispose()


@pytest.mark.parametrize("quantity", [0, -1, 1000, True, 1.5])
def test_invalid_cart_quantity_is_rejected(quantity):
    with pytest.raises(ValueError):
        CartAdd(variant_id="00000000-0000-0000-0000-000000000001", quantity=quantity)


@pytest.mark.parametrize("price", [-1, True, 1.5, "10000"])
def test_invalid_money_is_rejected(price):
    with pytest.raises(ValueError):
        VariantInput(sku="SKU", name="Variant", price=price, stock=1)


def test_patch_explicit_null_is_rejected():
    with pytest.raises(ValueError):
        ProductPatch(name=None)
    assert ProductPatch().model_dump(exclude_unset=True) == {}
