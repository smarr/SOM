"""
This is the SOM integration test runner file. Pytest automatically discovers
this file and will find all .som test files in the below directories.
"""

import subprocess
from pathlib import Path
from difflib import ndiff
import os
import pytest
import yaml
import conftest as external_vars


def locate_tests(path, test_files):
    """
    Locate all tests which are in the current directory.
    Add them to the list test_files and return
    A check if made on if the file has VM: in it's content
    """
    # To ID a file will be opened and at the top there should be a comment which starts with VM:
    for file_path in Path(path).glob("*.som"):
        with open(file_path, "r", encoding="utf-8") as f:
            contents = f.read()
            if "VM:" in contents:
                test_files.append(str(file_path))

    return test_files


def read_directory(path, test_files):
    """
    Recursively read all sub directories
    Path is the directory we are currently in
    test_files is the list of test files we are building up
    """
    for directory in Path(path).iterdir():
        if directory.is_dir():
            read_directory(directory, test_files)
        else:
            continue

    locate_tests(path, test_files)


def collect_tests(test_files):
    """
    Assemble a dictionary of
    name: the name of the test file
    stdout/stderr: the expected output of the test
    """
    tests = []
    for file_path in test_files:
        test_dict = parse_test_file(file_path)
        if test_dict is None:
            continue
        tests.append(test_dict)

    return tests


def parse_test_file(test_file):
    """
    parse the test file to extract the important information
    """
    test_info_dict = {
        "name": test_file,
        "stdout": [],
        "stderr": [],
        "custom_classpath": None,
        "case_sensitive": False,
    }
    with open(test_file, "r", encoding="utf-8") as open_file:
        contents = open_file.read()
        comment = contents.split('"')[1]

        # Make sure if using a custom test classpath that it is above
        # Stdout and Stderr
        if "custom_classpath" in comment:
            comment_lines = comment.split("\n")
            for line in comment_lines:
                if "custom_classpath" in line:
                    test_info_dict["custom_classpath"] = line.split(
                        "custom_classpath:"
                    )[1].strip()
                    continue

        # Check if we are case sensitive (has to be toggled on)
        if "case_sensitive" in comment:
            comment_lines = comment.split("\n")
            for line in comment_lines:
                if "case_sensitive" in line:
                    test_info_dict["case_sensitive"] = bool(
                        line.split("case_sensitive:")[1].strip().lower() == "true"
                    )

        if "stdout" in comment:
            std_out = comment.split("stdout:")[1]
            if "stderr" in std_out:
                std_err_inx = std_out.index("stderr:")
                std_out = std_out[:std_err_inx]
            std_err_l = std_out.split("\n")
            std_err_l = [line.strip() for line in std_err_l if line.strip()]
            test_info_dict["stdout"] = std_err_l

        if "stderr" in comment:
            std_err = comment.split("stderr:")[1]
            if "stdout" in std_err:
                std_out_inx = std_err.index("stdout:")
                std_err = std_err[:std_out_inx]
            std_err_l = std_err.split("\n")
            std_err_l = [line.strip() for line in std_err_l if line.strip()]
            test_info_dict["stderr"] = std_err_l

        if test_info_dict["case_sensitive"]:
            test_tuple = (
                test_info_dict["name"],
                test_info_dict["stdout"],
                test_info_dict["stderr"],
                test_info_dict["custom_classpath"],
                test_info_dict["case_sensitive"],
            )
            return test_tuple

        test_tuple = (
            test_info_dict["name"],
            [s.lower() for s in test_info_dict["stdout"]],
            [s.lower() for s in test_info_dict["stderr"]],
            test_info_dict["custom_classpath"],
            test_info_dict["case_sensitive"],
        )

    return test_tuple


def make_a_diff(expected, given):
    """
    Creates a string that represents the difference between two
    lists of Strings.
    """
    diff_string = ""
    for diff in ndiff(expected, given):
        diff_string += f"\n{str(diff)}"

    return diff_string


# pylint: disable=too-many-positional-arguments
# pylint: disable=too-many-arguments
def build_error_message(
    stdout, stderr, exp_stdout, exp_stderr, command, case_sensitive
):
    """
    Build an error message for the test runner
    """

    error_message = f"""\n
Command: {command}
Case Sensitive: {case_sensitive}
    """

    if stdout.strip() != "":
        error_message += "\nstdout diff with stdout expected\n"
        error_message += make_a_diff(exp_stdout, stdout.strip().split("\n"))

    if stderr.strip() != "":
        error_message += "\nstderr diff with stderr expected\n"
        error_message += make_a_diff(exp_stderr, stderr.strip().split("\n"))

    return error_message


def check_partial_word(word, exp_word):
    """
    Check a partial expected String against a line

    returns True if the line matches
    """

    # Creates a list of words that are expected
    exp_word_needed = exp_word.split("***")[0]
    exp_word_optional = exp_word.split("***")[1]

    if exp_word_needed in word:
        where = word.find(exp_word_needed) + len(exp_word_needed)
        counter = 0
        for character in exp_word_optional:

            if counter + where > len(word) - 1:
                return True

            if word[counter + where] == character:
                counter += 1
                continue
            return False
    else:
        return False

    if counter + where < len(word):
        return False

    return True


def check_exp_given(given, expected):
    """
    Check if the expected output is contained in the given output

    given: list of strings representing some kind of SOM output
    expected: list of strings representing the expected output

    return: 1 if success 0 if failure
    """
    # Check if the stdout matches the expected stdout
    exp_std_inx = 0
    for g_out in given:
        # Check that checks don't pass before out of outputs
        if exp_std_inx >= len(expected):
            return 1

        if expected[exp_std_inx] == "...":
            # If the expected output is '...' then we skip this line
            exp_std_inx += 1
            continue

        # This is incompaptible with ... for line skipping
        if "***" in expected[exp_std_inx]:
            # Now do some partial checking
            partial_output = check_partial_word(g_out, expected[exp_std_inx])
            if partial_output is True:
                exp_std_inx += 1
            continue

        if g_out.strip() != expected[exp_std_inx].strip():
            # Check if expected has ...
            if "..." in expected[exp_std_inx]:
                # If it does then we need to remove it and check for that line containing string
                without_gap = expected[exp_std_inx].split("...")
                if all(without_gap in g_out for without_gap in without_gap):
                    exp_std_inx += 1
                    continue

            # If the output does not match, continue without incrementing
            continue

        exp_std_inx += 1

    if exp_std_inx != len(expected):
        # It is not all contained in the output
        return 0

    return 1


def check_output(test_outputs, expected_std_out, expected_std_err):
    """
    check if the output of the test matches the expected output
    test_outputs: The object returned by subprocess.run
    expected_std_out: The expected standard output
    expected_std_err: The expected standard error output
    Returns: Boolean indicating if result matches expected output

    note: This method does not directly error, just checks conditions

    stdout and stderr do not match in all SOMs
    stderr checked against stdout and stderr
    stdout checked against stdout and stderr

    This is relatively robust for most test cases
    """
    given_std_out = test_outputs.stdout.split("\n")
    given_std_err = test_outputs.stderr.split("\n")

    passing = 0

    passing += check_exp_given(given_std_out, expected_std_out)
    passing += check_exp_given(given_std_err, expected_std_err)

    if passing == 2:
        # If we have two passing then we know we have what we expect
        return True

    return False


# Read the test exceptions file and set the variables correctly
# pylint: disable=too-many-branches
def read_test_exceptions(filename):
    """
    Read a TEST_EXCEPTIONS file and extract the core information
    Filename should be either a relative path from CWD to file
    or an absolute path.
    """
    if filename:
        path = os.path.relpath(os.path.dirname(__file__))

        with open(f"{filename}", "r", encoding="utf-8") as file:
            yaml_file = yaml.safe_load(file)

            if yaml_file is not None:
                if "known_failures" in yaml_file:
                    external_vars.known_failures = yaml_file["known_failures"]
                    if external_vars.known_failures is None:
                        external_vars.known_failures = []

                else:
                    external_vars.known_failures = []

                if "failing_as_unspecified" in yaml_file:
                    external_vars.failing_as_unspecified = yaml_file[
                        "failing_as_unspecified"
                    ]
                    if external_vars.failing_as_unspecified is None:
                        external_vars.failing_as_unspecified = []

                else:
                    external_vars.failing_as_unspecified = []

                if "unsupported" in yaml_file:
                    external_vars.unsupported = yaml_file["unsupported"]
                    if external_vars.unsupported is None:
                        external_vars.unsupported = []

                else:
                    external_vars.unsupported = []

                if "do_not_run" in yaml_file:
                    external_vars.do_not_run = yaml_file["do_not_run"]
                    if external_vars.do_not_run is None:
                        external_vars.do_not_run = []

                else:
                    external_vars.do_not_run = []
            else:
                external_vars.known_failures = []
                external_vars.failing_as_unspecified = []
                external_vars.unsupported = []
                external_vars.do_not_run = []

        if (
            external_vars.known_failures is not None
            and external_vars.known_failures != [None]
        ):
            external_vars.known_failures = [
                os.path.join(path, test) for test in external_vars.known_failures
            ]
        if (
            external_vars.failing_as_unspecified is not None
            and external_vars.failing_as_unspecified != [None]
        ):
            external_vars.failing_as_unspecified = [
                os.path.join(path, test)
                for test in external_vars.failing_as_unspecified
            ]
        if external_vars.unsupported is not None and external_vars.unsupported != [
            None
        ]:
            external_vars.unsupported = [
                os.path.join(path, test) for test in external_vars.unsupported
            ]
        if external_vars.do_not_run is not None and external_vars.do_not_run != [None]:
            external_vars.do_not_run = [
                os.path.join(path, test) for test in external_vars.do_not_run
            ]


# START, ENTRY, BEGIN, MAIN
# Code below here runs before pytest finds it's methods
location = os.path.relpath(os.path.dirname(__file__))
if not os.path.exists(location + "/Tests"):
    pytest.exit(
        "/Tests directory not found. Please make sure the lang_tests are installed"
    )

# Work out settings for the application (They are labelled REQUIRED or OPTIONAL)
if "CLASSPATH" not in os.environ:  # REQUIRED
    sys.exit("Please set the CLASSPATH environment variable")

if "VM" not in os.environ:  # REQUIRED
    sys.exit("Please set the VM environment variable")

if "TEST_EXCEPTIONS" in os.environ:  # OPTIONAL
    external_vars.TEST_EXCEPTIONS = location + "/" + os.environ["TEST_EXCEPTIONS"]

if "GENERATE_REPORT" in os.environ:  # OPTIONAL
    # Value is the location
    # Its prescense in env variables signifies intent to save
    external_vars.GENERATE_REPORT = os.environ["GENERATE_REPORT"]

external_vars.CLASSPATH = os.environ["CLASSPATH"]
external_vars.VM = os.environ["VM"]

read_test_exceptions(external_vars.TEST_EXCEPTIONS)


def prepare_tests():
    """
    Prepare all of the tests and their relevent information into a dictionary
    so that the test runner understands each test
    """
    test_files = []
    read_directory(location + "/Tests", test_files)
    test_files = sorted(test_files)
    return collect_tests(test_files)


@pytest.mark.parametrize(
    "name,stdout,stderr,custom_classpath,case_sensitive",
    prepare_tests(),
    ids=[str(test_args[0]) for test_args in prepare_tests()],
)
# pylint: disable=too-many-branches
def tests_runner(name, stdout, stderr, custom_classpath, case_sensitive):
    """
    Take an array of dictionaries with test file names and expected output
    Run all of the tests and check the output
    Cleanup the build directory if required
    """

    # Check if a test shoudld not be ran
    if str(name) in external_vars.do_not_run:
        pytest.skip("Test included in do_not_run")

    if custom_classpath is not None:
        command = f"{external_vars.VM} -cp {custom_classpath} {name}"
    else:
        command = f"{external_vars.VM} -cp {external_vars.CLASSPATH} {name}"

    try:
        result = subprocess.run(
            command, capture_output=True, text=True, shell=True, check=False
        )
    except UnicodeDecodeError:
        pytest.skip(
            "Test output could not be decoded SOM may not support "
            "full Unicode. Result object not generated."
        )

    # lower-case comparisons unless specified otherwise
    if case_sensitive is False:
        result.stdout = str(result.stdout).lower()
        result.stderr = str(result.stderr).lower()

    # Produce potential error messages now and then run assertion
    error_message = build_error_message(
        result.stdout, result.stderr, stdout, stderr, command, case_sensitive
    )

    # Related to above line (Rather than change how stdout and stderr are
    # represented just joining and then splitting again)

    if result.returncode != 0:
        error_message += f"Command failed with return code: {result.returncode}\n"

    test_pass_bool = check_output(result, stdout, stderr)

    # Check if we have any unexpectedly passing tests
    if (
        name in external_vars.known_failures and test_pass_bool
    ):  # Test passed when it is not expected to
        external_vars.tests_passed_unexpectedly.append(name)
        assert False, f"Test {name} is in known_failures but passed"

    if (
        str(name) in external_vars.failing_as_unspecified and test_pass_bool
    ):  # Test passed when it is not expected tp
        external_vars.tests_passed_unexpectedly.append(name)
        assert False, f"Test {name} is in failing_as_unspecified but passed"

    if (
        name in external_vars.unsupported and test_pass_bool
    ):  # Test passed when it is not expected tp
        external_vars.tests_passed_unexpectedly.append(name)
        assert False, f"Test {name} is in unsupported but passed"

    if (
        name not in external_vars.unsupported
        and name not in external_vars.known_failures
        and name not in external_vars.failing_as_unspecified
    ):
        if not test_pass_bool:
            external_vars.tests_failed_unexpectedly.append(name)
        assert (
            test_pass_bool
        ), f"Error on test, {name} expected to pass: {error_message}"
