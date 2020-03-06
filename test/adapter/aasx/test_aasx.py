# Copyright 2019 PyI40AAS Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

import unittest
from aas import model
from aas.adapter import aasx


class TestAASXUtils(unittest.TestCase):
    def test_name_friendlyfier(self) -> None:
        friendlyfier = aasx.NameFriendlyfier()
        name1 = friendlyfier.get_friendly_name(model.Identifier("http://example.com/AAS-a", model.IdentifierType.IRI))
        self.assertEqual("http___example_com_AAS_a", name1)
        name2 = friendlyfier.get_friendly_name(model.Identifier("http://example.com/AAS+a", model.IdentifierType.IRI))
        self.assertEqual("http___example_com_AAS_a_1", name2)
