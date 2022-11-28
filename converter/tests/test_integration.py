from converter.constants import PATH_CSV_TEST_INPUT
from converter.constants import PATH_XML_TEST_EXPECTED_OUTPUT
from converter.convert import ConvertCsvToXml
from converter.tests.data.input.expected_df_with_errors import df_expected_with_errors
from pathlib import Path

import filecmp
import pandas as pd


def test_integration(tmp_path):
    data_converter = ConvertCsvToXml(orig_csv_path=PATH_CSV_TEST_INPUT)

    # test the validation output
    data_converter.validate_df()
    df_with_errors = data_converter.df
    df_expected_with_errors_dtypes = df_expected_with_errors.astype(df_with_errors.dtypes.to_dict())
    pd.testing.assert_frame_equal(left=df_with_errors, right=df_expected_with_errors_dtypes, check_index_type=False)

    # test the created .xml
    tmp_path = Path(f"{tmp_path.as_posix()}.xml")
    path_small, path_large = data_converter._create_xml(
        xml_path=tmp_path, create_small_xml=True, create_large_xml=False
    )
    assert PATH_XML_TEST_EXPECTED_OUTPUT.is_file()
    assert path_small and path_small.is_file()
    assert not path_large

    xml_equals_expected_xml = filecmp.cmp(
        f1=PATH_XML_TEST_EXPECTED_OUTPUT.as_posix(), f2=path_small.as_posix(), shallow=True
    )
    assert xml_equals_expected_xml
