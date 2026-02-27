from jsonschema import validate
import pytest
import schemas
import api_helpers
from hamcrest import assert_that, equal_to, is_

'''
TODO: Finish this test by...
1) Troubleshooting and fixing the test failure
The purpose of this test is to validate the response matches the expected schema defined in schemas.py
Fixed: schemas.py had 'name' type as 'integer' instead of 'string'
'''
def test_pet_schema():
    test_endpoint = "/pets/1"

    response = api_helpers.get_api_data(test_endpoint)

    assert response.status_code == 200

    # Validate the response schema against the defined schema in schemas.py
    validate(instance=response.json(), schema=schemas.pet)

'''
TODO: Finish this test by...
1) Extending the parameterization to include all available statuses
2) Validate the appropriate response code
3) Validate the 'status' property in the response is equal to the expected status
4) Validate the schema for each object in the response
'''
@pytest.mark.parametrize("status", ["available", "pending", "sold"])
def test_find_by_status_200(status):
    test_endpoint = "/pets/findByStatus"
    params = {
        "status": status
    }

    response = api_helpers.get_api_data(test_endpoint, params)

    # Validate the response code
    assert_that(response.status_code, is_(equal_to(200)))

    pets = response.json()

    for pet in pets:
        # Validate the status property matches the requested status
        assert_that(pet["status"], is_(equal_to(status)))

        # Validate the schema for each pet object in the response
        validate(instance=pet, schema=schemas.pet)

'''
TODO: Finish this test by...
1) Testing and validating the appropriate 404 response for /pets/{pet_id}
2) Parameterizing the test for any edge cases
'''
@pytest.mark.parametrize("pet_id", [9999, -1])
def test_get_by_id_404(pet_id):
    test_endpoint = f"/pets/{pet_id}"

    response = api_helpers.get_api_data(test_endpoint)

    # Validate a 404 is returned for non-existent pet IDs
    assert_that(response.status_code, is_(equal_to(404)))