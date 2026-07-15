"""
End-to-End (E2E) Step Library — TAF Step Library seed (TFK-03).

Organized by domain; all steps use Playwright (``context.page``).
Selectors use ``page.get_by_test_id()`` per SAO.md §15.

Modules and steps:

**navigation_steps**
  - Given the user is on the "{page_name}" page
  - When the user navigates to the "{page_name}" page
  - Then the user should see the "{page_name}" page

**form_steps**
  - When the user enters "{value}" into "{field}"
  - When the user selects "{option}" from "{dropdown}"
  - When the user clicks "{button}"
  - When the user submits the form

**table_steps**
  - Then the user sees table "{table_name}" with {n:d} rows
  - Then the table "{table_name}" should contain "{text}"
  - When the user sorts table "{table_name}" by "{column}"

**auth_steps**
  - Given the user is logged in as "{role}" (stub — NotImplementedError)
  - Given the user is not authenticated

**assertion_steps**
  - Then the user should see "{text}"
  - Then the user should not see "{text}"
  - Then the element "{test_id}" should be visible

**dialog_steps**
  - When the user confirms the dialog
  - When the user cancels the dialog
  - Then the dialog "{dialog_name}" should be visible

**common_steps**
  - When the user waits {seconds:d} seconds
"""
