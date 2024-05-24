"""The Unit Test for the SafeList Model."""

from notify_api.models.safe_list import SafeList


def test_safe_list():
    """Assert the test safe list model vaildation."""
    safelist = SafeList()
    safelist.add_email("hello@gogo.com")
    safelist.add_email("hello@gogo2.com")
    assert safelist.is_in_safe_list("hello@gogo.com")
    assert safelist.is_in_safe_list("hello@gogo2.com")
    # Test delete email
    safelist_to_delete = safelist.find_by_email("hello@gogo.com")
    safelist_to_delete.delete_email()
    assert not safelist.is_in_safe_list("hello@gogo.com")
    assert safelist.is_in_safe_list("hello@gogo2.com")
    # Test add email
    safelist.add_email("hello@gogo.com")
    assert safelist.is_in_safe_list("hello@gogo.com")
    assert safelist.is_in_safe_list("hello@gogo2.com")
