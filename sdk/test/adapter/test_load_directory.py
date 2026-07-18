import tempfile
import unittest
from pathlib import Path

from basyx.aas import adapter, model


class LoadDirectoryTest(unittest.TestCase):
    def test_reading_all_files(self):
        # ----- Arange ----
        # Create an AAS per file type
        json_aas = model.AssetAdministrationShell(
            id_="http://example.org/JSON_AAS",
            asset_information=model.AssetInformation(
                global_asset_id="http://example.org/JSON_Asset"
            ),
        )

        xml_aas = model.AssetAdministrationShell(
            id_="http://example.org/XML_AAS",
            asset_information=model.AssetInformation(
                global_asset_id="http://example.org/XML_Asset"
            ),
        )

        aasx_aas = model.AssetAdministrationShell(
            id_="http://example.org/aasx_AAS",
            asset_information=model.AssetInformation(
                global_asset_id="http://example.org/aasx_Asset"
            ),
        )

        # load TestFile.pdf to save into aasx
        file_container = adapter.aasx.DictSupplementaryFileContainer()
        with open(Path(__file__).parent / "aasx" / "TestFile.pdf", "rb") as pdf:
            resulting_file_name = file_container.add_file(
                "/aasx/suppl/file.pdf", pdf, "application/json"
            )

        # create submodel for aasx_aas that refers to pdf
        sm_with_file = model.Submodel(
            id_="http://example.org/tmp_Submodel",
            submodel_element={
                model.File(
                    id_short="SampleFile",
                    content_type="application/json",
                    value=resulting_file_name,
                )
            },
        )
        aasx_aas.submodel.add(model.ModelReference.from_referable(sm_with_file))

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            # save to json file
            adapter.json.write_aas_json_file(
                temp_dir_path / "testAAS.json", model.DictIdentifiableStore([json_aas])
            )
            # save to xml file
            adapter.xml.write_aas_xml_file(
                temp_dir_path / "testAAS.xml", model.DictIdentifiableStore([xml_aas])
            )
            # save to aasx file
            with adapter.aasx.AASXWriter(temp_dir_path / "testAAS.aasx") as writer:
                writer.write_aas(
                    aas_ids=["http://example.org/aasx_AAS"],
                    object_store=model.DictIdentifiableStore([aasx_aas, sm_with_file]),
                    file_store=file_container,
                )

            # ---- Act ----
            new_object_store, new_file_store = adapter.load_directory(temp_dir_path)

            # ---- Assert -----
            # check for all three AAS
            self.assertIn("http://example.org/JSON_AAS", new_object_store)
            self.assertIn("http://example.org/XML_AAS", new_object_store)
            self.assertIn("http://example.org/aasx_AAS", new_object_store)

            # check pdf is loaded
            self.assertIn(resulting_file_name, new_file_store)

    def test_skipping_other_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            # ---- Arange ----
            tmp_dir_path = Path(tmp_dir)

            # create empty file
            open(tmp_dir_path / "test.txt", "a").close()

            # create directory
            (tmp_dir_path / "empty").mkdir()

            # ---- Act ----
            # assert no exception is occurring
            object_store, file_store = adapter.load_directory(tmp_dir_path)

            # ---- Assert ----
            # check stores are empty
            self.assertEqual(len(object_store), 0)
            self.assertEqual(len(file_store), 0)
