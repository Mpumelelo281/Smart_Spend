import pytest
from django.core.exceptions import ImproperlyConfigured

from smartspend.secret_key import INSECURE_DEFAULT, require_real_secret_key


def test_placeholder_key_is_refused_when_debug_is_off():
    with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY"):
        require_real_secret_key(INSECURE_DEFAULT, debug=False)


def test_placeholder_key_is_allowed_locally_with_debug_on():
    assert require_real_secret_key(INSECURE_DEFAULT, debug=True) == INSECURE_DEFAULT


def test_a_real_key_is_accepted_in_production():
    key = "x" * .  m,l]
    

    assert require_real_secret_key(key, debug=False) == key

