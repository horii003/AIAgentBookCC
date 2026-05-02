import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import (
    EXPENSE_TEMPLATE_PATH,
    FIXED_FARES_PATH,
    OUTPUT_DIR,
    SESSION_DIR,
    TRAIN_ROUTES_PATH,
    TRANSPORT_TEMPLATE_PATH,
)


def test_all_constants_are_strings():
    for val in [
        TRAIN_ROUTES_PATH,
        FIXED_FARES_PATH,
        TRANSPORT_TEMPLATE_PATH,
        EXPENSE_TEMPLATE_PATH,
        OUTPUT_DIR,
        SESSION_DIR,
    ]:
        assert isinstance(val, str)


def test_train_routes_path():
    assert TRAIN_ROUTES_PATH == "data/train_routes.json"


def test_fixed_fares_path():
    assert FIXED_FARES_PATH == "data/fixed_fares.json"


def test_transport_template_path():
    assert "交通費" in TRANSPORT_TEMPLATE_PATH
    assert TRANSPORT_TEMPLATE_PATH.endswith(".xlsx")


def test_expense_template_path():
    assert "経費" in EXPENSE_TEMPLATE_PATH
    assert EXPENSE_TEMPLATE_PATH.endswith(".xlsx")
