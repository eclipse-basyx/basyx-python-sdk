# Copyright (c) 2026 the Eclipse BaSyx Authors
#
# This program and the accompanying materials are made available under the terms of the MIT License, available in
# the LICENSE file of this project.
#
# SPDX-License-Identifier: MIT

"""
Endpoint test for the ``/description`` route of :class:`~app.interfaces.repository.WSGIApp`.
"""

from .helpers import RepositoryEndpointTestBase


class RepositoryServiceDescriptionTest(RepositoryEndpointTestBase):

    def test_description(self) -> None:
        response = self.client.get("/description")
        self.assertEqual(200, response.status_code)
        body = response.get_data(as_text=True)
        self.assertIn("AssetAdministrationShellRepositoryServiceSpecification/SSP-001", body)
        self.assertIn("SubmodelRepositoryServiceSpecification/SSP-001", body)
