"""
Tests that will check if the test_runner is wokring ok
"""

import os
import pytest
from test_runner import (
    parse_test_file,
    read_directory,
    check_exp_given,
    read_test_exceptions,
)
import conftest as external_vars


@pytest.mark.tester
def test_parse_file():
    """
    Test that the test_runner can parse a file correctly.
    Expected output should be lower-case
    """

    # EXAMPLE TUPLE
    # 0. test_info_dict["name"],
    # 1. test_info_dict["stdout"],
    # 2. test_info_dict["stderr"],
    # 3. test_info_dict["custom_classpath"],
    # 4. test_info_dict["case_sensitive"],

    soms_for_testing_location = os.path.relpath(
        os.path.dirname(__file__) + "/test_runner_tests/soms_for_testing"
    )

    # Firstly assign what is expected from parsing som_test_1.som
    exp_stdout = ["1", "2", "3", "4", "5", "...", "10"]
    exp_stderr = ["this is an error", "...", "hello, world"]
    custom_classpath = None
    case_sensitive = False

    # Parse test and assert values are as above
    result_tuple = parse_test_file(soms_for_testing_location + "/som_test_1.som")
    assert result_tuple[1] == exp_stdout, "som_test_1.som stdout is not correct"
    assert result_tuple[2] == exp_stderr, "som_test_1.som stderr is not correct"
    assert (
        result_tuple[3] is custom_classpath
    ), "som_test_1.som custom_classpath should be None"
    assert (
        result_tuple[4] is case_sensitive
    ), "som_test_1.som case_sensitive shoudl be False"

    # Firstly assign what is expected from parsing som_test_2.som
    exp_stdout = ["I AM cAsE sensitiVe", "...", "Dots/inTest"]
    exp_stderr = ["CaSE sensitive ErrOr", "...", "TestCaseSensitivity"]
    custom_classpath = None
    case_sensitive = True

    # Parse test and assert values are as above
    result_tuple = parse_test_file(soms_for_testing_location + "/som_test_2.som")
    assert result_tuple[1] == exp_stdout, "som_test_2.som stdout is not correct"
    assert result_tuple[2] == exp_stderr, "som_test_2.som stderr is not correct"
    assert (
        result_tuple[3] is custom_classpath
    ), "som_test_2.som custom_classpath should be None"
    assert (
        result_tuple[4] is case_sensitive
    ), "som_test_2.som case_sensitive shoudl be True"

    # Firstly assign what is expected from parsing som_test_3.som
    exp_stdout = ["..."]
    exp_stderr = ["..."]
    custom_classpath = "core-lib/AreWeFastYet/Core"
    case_sensitive = False

    # Parse test and assert values are as above
    result_tuple = parse_test_file(soms_for_testing_location + "/som_test_3.som")
    assert result_tuple[1] == exp_stdout, "som_test_3.som stdout is not correct"
    assert result_tuple[2] == exp_stderr, "som_test_3.som stderr is not correct"
    assert (
        result_tuple[3] == custom_classpath
    ), f"som_test_3.som custom_classpath should be {custom_classpath}"
    assert (
        result_tuple[4] is case_sensitive
    ), "som_test_3.som case_sensitive shoudl be False"


@pytest.mark.tester
def test_test_discovery():
    """
    Test the som test discovery methods in the test_runner_tests directory
    Three tests should be located, Update this method if more tests are added
    """
    # Locate all SOM tests
    test_runner_tests_location = os.path.relpath(
        os.path.dirname(__file__) + "/test_runner_tests"
    )
    tests = []
    read_directory(test_runner_tests_location, tests)
    tests = sorted(tests)

    expected_tests = [
        f"{str(test_runner_tests_location)}/soms_for_testing/som_test_1.som",
        f"{str(test_runner_tests_location)}/soms_for_testing/som_test_2.som",
        f"{str(test_runner_tests_location)}/soms_for_testing/som_test_3.som",
    ]

    assert (
        tests == expected_tests
    ), "Some expected tests not found in tests_runner_tests, discovery could be incorrect"


@pytest.mark.tester
def test_check_output():
    """
    Test that the check_output function complies with the expected output.
    """

    stdout = "Hello World\nSome other output in the Middle\nThis is a test\n"

    expected_stdout = ["hello world", "...", "this is a test"]

    # For checking case sensitivity all are converted to lower at differnt parts of the program
    # This just simulates that. It is very difficult to actually run this

    # Check case sensitive
    assert (
        check_exp_given(stdout.split("\n"), expected_stdout) == 0
    ), "Output here should evaluate to False, currently case_sensitive"
    # Check case insensitive
    assert (
        check_exp_given(stdout.lower().split("\n"), expected_stdout) == 1
    ), "Output here should evaluate to True, currently case_insensitive"

    # Check large output file with ... used inline at beginning and at end
    stdout = """This is SOM++
Hello Rhys this is some sample output
1\n2\n3\n4\n4\n56\n6\n7\n7\n8\n9\n9
1010101\n10101\n1010101
1010101010101010100101010101010010101
Rhys Walker
Moving on
Extra text
more Numbers
NUMBER NUMBER NUMBER NUMBER
"""
    expected_stdout = [
        "Hello ... this is ... sample output",
        "Rhys Walker",
        "... on",
        "more ...",
        "... NUMBER ... NUMBER",
    ]

    assert (
        check_exp_given(stdout.split("\n"), expected_stdout) == 1
    ), "Evaluation should have been successfull"

    stdout = """This is SOM++
Hello, this is some sample output
There is some more on this line
And a little more here
"""
    expected_stdout = [
        "Hello, ... sample ...",
        "... is ... this line",
        "... little ...",
    ]

    assert (
        check_exp_given(stdout.split("\n"), expected_stdout) == 1
    ), "Evaluation should have been successfull"

    # Now check some outputs with ***
    # A couple of assertions are run on this expacted
    expected = ["...", "Really***LongWord"]

    stdout = "Some output, as an example\nExtra Line\nReallyLongWord"
    assert check_exp_given(
        stdout.split("\n"), expected
    ), "Evaluation should've been successfull"
    stdout = "Some output, as an example\nExtra Line\nReally"
    assert check_exp_given(
        stdout.split("\n"), expected
    ), "Evaluation should've been successfull"
    stdout = "Some output, as an example\nExtra Line\nReallyLong"
    assert check_exp_given(
        stdout.split("\n"), expected
    ), "Evaluation should've been successfull"
    stdout = "Some output, as an example\nExtra Line\nReallyLo"
    assert check_exp_given(
        stdout.split("\n"), expected
    ), "Evaluation should've been successfull"

    # Now assert some failures to test when it should fail
    stdout = "Some output, as an example\nExtra Line\nReallyLongTestFunction"
    assert not check_exp_given(
        stdout.split("\n"), expected
    ), "Evaluation should've been successfull"

    # This one should fail as there is still more word than expected
    stdout = "Some output, as an example\nExtra Line\nReallyLongWordExtra"
    assert not check_exp_given(
        stdout.split("\n"), expected
    ), "Evaluation should've been successfull"


@pytest.mark.tester
def test_different_yaml():
    """
    Test different yaml files which may be missing some information
    Or be malformed
    """

    # First, save the variables that will change in external_vars
    temp_known = external_vars.known_failures
    temp_unspecified = external_vars.failing_as_unspecified
    temp_unsupported = external_vars.unsupported
    temp_do_not_run = external_vars.do_not_run

    yaml_for_testing_location = os.path.relpath(
        os.path.dirname(__file__) + "/test_runner_tests/yaml_for_testing"
    )

    # Read a yaml file with nothing after tag (Should all be empty lists)
    read_test_exceptions(yaml_for_testing_location + "/missing_known_declaration.yaml")
    assert (
        external_vars.known_failures == []
    ), "known_failures was not [] in missing_known_declaration.yaml"
    assert (
        external_vars.failing_as_unspecified == []
    ), "failing_as_unspecified was not [] in missing_known_declaration.yaml"
    assert (
        external_vars.unsupported == []
    ), "unsupported was not [] in missing_known_declaration.yaml"
    assert (
        external_vars.do_not_run == []
    ), "do_not_run was not [] in missing_known_declaration.yaml"

    # Read a yaml file with null after each tag (Should all be [])
    read_test_exceptions(yaml_for_testing_location + "/set_to_be_null.yaml")
    assert external_vars.known_failures == [
        None
    ], "known_failures was not [] in set_to_be_null.yaml"
    assert external_vars.failing_as_unspecified == [
        None
    ], "failing_as_unspecified was not [] in set_to_be_null.yaml"
    assert external_vars.unsupported == [
        None
    ], "unsupported was not [] in set_to_be_null.yaml"
    assert external_vars.do_not_run == [
        None
    ], "do_not_run was not [] in set_to_be_null.yaml"

    # Read a yaml file where the yamlFile object will evaluate to None type (Should be all [])
    read_test_exceptions(yaml_for_testing_location + "/missing_all_tags.yaml")
    assert (
        external_vars.known_failures == []
    ), "known_failures was not [] in missing_all_tags.yaml"
    assert (
        external_vars.failing_as_unspecified == []
    ), "failing_as_unspecified was not [] in missing_all_tags.yaml"
    assert (
        external_vars.unsupported == []
    ), "unsupported was not [] in missing_all_tags.yaml"
    assert (
        external_vars.do_not_run == []
    ), "do_not_run was not [] in missing_all_tags.yaml"

    # Read a yaml file where each tag has one test included
    # [core-lib/IntegrationTests/Tests/mutate_superclass_method/test.som]
    read_test_exceptions(yaml_for_testing_location + "/tests_in_each.yaml")
    test_list = ["core-lib/IntegrationTests/Tests/mutate_superclass_method/test.som"]
    assert (
        external_vars.known_failures == test_list
    ), f"known_failures was not {test_list} in missing_all_tags.yaml"
    assert (
        external_vars.failing_as_unspecified == test_list
    ), f"failing_as_unspecified was not {test_list} in missing_all_tags.yaml"
    assert (
        external_vars.unsupported == test_list
    ), f"unsupported was not {test_list} in missing_all_tags.yaml"
    assert (
        external_vars.do_not_run == test_list
    ), f"do_not_run was not {test_list} in missing_all_tags.yaml"

    # Reset external vars after test
    external_vars.known_failures = temp_known
    external_vars.failing_as_unspecified = temp_unspecified
    external_vars.unsupported = temp_unsupported
    external_vars.do_not_run = temp_do_not_run
