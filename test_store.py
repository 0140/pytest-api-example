from jsonschema import validate
import pytest
import schemas
import api_helpers
from hamcrest import assert_that, equal_to, is_, has_entry

# Optional: pytest fixture to create a unique order before each test run
@pytest.fixture
def created_order():
    # Pet ID 2 (flippy) is 'available' and can be ordered
    order_data = {"pet_id": 2}
    response = api_helpers.post_api_data("/store/order", order_data)
    assert response.status_code == 201
    order = response.json()
    yield order
    # Teardown: reset pet status back to 'available' for the next test
    api_helpers.patch_api_data(f"/store/order/{order['id']}", {"status": "available"})

'''
TODO: Finish this test by...
1) Creating a function to test the PATCH request /store/order/{order_id}
2) *Optional* Consider using @pytest.fixture to create unique test data for each run
2) *Optional* Consider creating an 'Order' model in schemas.py and validating it in the test
3) Validate the response codes and values
4) Validate the response message "Order and pet status updated successfully"
'''
@pytest.mark.parametrize("new_status", ["sold", "available", "pending"])
def test_patch_order_by_id(created_order, new_status):
    order_id = created_order["id"]
    test_endpoint = f"/store/order/{order_id}"

    # Validate the created order schema
    validate(instance=created_order, schema=schemas.order)

    # Send PATCH request to update the order status
    patch_data = {"status": new_status}
    response = api_helpers.patch_api_data(test_endpoint, patch_data)

    # Validate the response code
    assert_that(response.status_code, is_(equal_to(200)))

    # Validate the response message
    assert_that(response.json(), has_entry("message", "Order and pet status updated successfully"))
