# pylint: disable=missing-function-docstring, missing-class-docstring, too-many-arguments, too-many-positional-arguments, too-few-public-methods
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
from conftest import REPORT_DETAILS


class Definition:
    def __init__(
        self,
        name: str,
        status: str | int | None,
        stdout: list[str],
        stderr: list[str],
        custom_classpath: str | None,
        case_sensitive: bool,
        definition_fail_msg: str | None,
    ):
        self.name = name
        if status is None:
            status = "success"
        assert status == "success" or status == "error" or isinstance(status, int)

        self.status = status
        self.stdout = stdout
        self.stderr = stderr
        self.custom_classpath = custom_classpath
        self.case_sensitive = case_sensitive
        self.definition_fail_msg = definition_fail_msg

    def __repr__(self):
        return (
            f"Definition(name={self.name}, status={self.status}, "
            f"stdout={self.stdout}, stderr={self.stderr}, "
            f"custom_classpath={self.custom_classpath}, "
            f"case_sensitive={self.case_sensitive}, "
            f"definition_fail_msg={self.definition_fail_msg})"
        )


class ParseError(Exception):
    """
    Exception raised when a test file cannot be parsed correctly.
    This is used to fail the test in the test runner.
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message


def discover_test_files_candidates(path, test_files):
    """
    Recursively read the directory tree and add all .som test files to `test_files`.
    """
    for element in Path(path).iterdir():
        if element.is_dir():
            discover_test_files_candidates(element, test_files)
        elif element.is_file() and element.suffix == ".som":
            test_files.append(str(element))


def collect_tests(test_files) -> list[Definition]:
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


def process_classpath(classpath) -> str | None:
    """
    Process variables in classpath.
    $var is expecting a `var` to be defined as an environment variable
    to use in the classpath.
    """
    if "$" not in classpath:
        return classpath

    parts = classpath.split(":")

    for i, part in enumerate(parts):
        if part[0] == "$":
            # If the part contains an '$', it is expected to be an environment variable
            var_name = part.replace("$", "")
            if var_name in os.environ:
                parts[i] = os.environ[var_name]
            else:
                raise ParseError(f"Environment variable {var_name} not set")

    return ":".join(parts)


# pylint: disable=too-many-locals, too-many-return-statements, too-many-branches, too-many-statements
def parse_test(content, name) -> Definition | None:
    status = None
    stdout = []
    stderr = []
    custom_classpath = None
    case_sensitive = False

    test_definition = content.split('"')[1]

    # the test definition is similar to a YAML format.
    # it starts with an executable command name followed by a colon
    # after it, there are at the same indentation level, properties defined.
    # possible properties are:
    # - stdout: the expected standard output of the test
    # - stderr: the expected standard error output of the test
    # - custom_classpath: the custom classpath for the test
    # - case_sensitive: whether the test is case sensitive or not
    # but these properties can have multiline values, or just one the same line.
    lines = test_definition.split("\n")

    while lines[0].strip() == "":
        lines.pop(0)  # remove leading empty lines

    exec_command = lines[0].strip()
    if exec_command != "VM:":
        return Definition(
            name,
            None,
            [],
            [],
            None,
            False,
            "Test definition is expected to start with 'VM:'",
        )

    lines.pop(0)

    first_line = lines[0]
    indentation_level = len(first_line) - len(first_line.lstrip())
    multiline_val_indentation = indentation_level * 2

    finding_next_property = True
    current_part_name = None
    record_value = False

    for line in lines:
        if not finding_next_property:
            if (
                not line[:multiline_val_indentation].isspace()
                and not line[indentation_level:].isspace()
                and ":" in line
            ):
                # reached the end of a multiline value
                finding_next_property = True

        if finding_next_property:
            if not line.strip():
                continue  # skip empty lines

            prefix = line[:indentation_level]
            if not prefix.isspace():
                return Definition(
                    name,
                    None,
                    [],
                    [],
                    None,
                    False,
                    "Test definition has inconsistent indentation",
                )

            rest = line[indentation_level:]
            if rest[0].isspace():
                return Definition(
                    name,
                    None,
                    [],
                    [],
                    None,
                    False,
                    "Test definition has inconsistent indentation",
                )

            parts = rest.split(":", 1)
            if len(parts) != 2:
                return Definition(
                    name,
                    None,
                    [],
                    [],
                    None,
                    False,
                    "Test definition line does not contain a property: " + line,
                )

            current_part_name = parts[0]
            current_part_value = parts[1].strip()
            if current_part_value:
                record_value = True
            else:
                finding_next_property = False
        else:
            prefix = line[:multiline_val_indentation]
            if line and not prefix.isspace():
                return Definition(
                    name,
                    None,
                    [],
                    [],
                    None,
                    False,
                    "Test definition has inconsistent indentation",
                )

            current_part_value = line[multiline_val_indentation:]
            assert current_part_name
            record_value = True

        if record_value:
            if current_part_name == "status":
                status = current_part_value.strip()
                if status.isnumeric():
                    status = int(status)
            elif current_part_name == "stdout":
                stdout.append(current_part_value)
            elif current_part_name == "stderr":
                stderr.append(current_part_value)
            elif current_part_name == "custom_classpath":
                custom_classpath = current_part_value
            elif current_part_name == "case_sensitive":
                case_sensitive = current_part_value.lower() == "true"
            else:
                return Definition(
                    name,
                    None,
                    [],
                    [],
                    None,
                    False,
                    f"Unknown property in test definition: {current_part_name}",
                )
            record_value = False

    if custom_classpath:
        custom_classpath = process_classpath(custom_classpath)

    if stdout and stdout[-1] == "":
        stdout.pop()  # remove the last empty line if it exists

    if stderr and stderr[-1] == "":
        stderr.pop()  # remove the last empty line if it exists

    return Definition(
        name, status, stdout, stderr, custom_classpath, case_sensitive, None
    )


def parse_test_file(test_file) -> Definition | None:
    try:
        contents = None
        with open(test_file, "r", encoding="utf-8") as open_file:
            contents = open_file.read()

        if contents is None or '"' not in contents:
            return None

        return parse_test(contents, test_file)
    except ParseError as e:
        return Definition(test_file, None, [], [], None, False, e.message)


def make_a_diff(expected, given):
    """
    Creates a string that represents the difference between two
    lists of Strings.
    """
    diff_string = ""
    for diff in ndiff(expected, given):
        diff_string += f"\n{str(diff)}"

    return diff_string


def build_error_message(result, test, command):
    error_message = f"""\n
Command: {command}
Status: {test.status}
Case Sensitive: {test.case_sensitive}
    """

    if result.stdout.strip() != "":
        error_message += "\nstdout diff with stdout expected\n"
        error_message += make_a_diff(test.stdout, result.stdout.strip().split("\n"))
        error_message += "\n"

    if result.stderr.strip() != "":
        error_message += "\nstderr diff with stderr expected\n"
        error_message += make_a_diff(test.stderr, result.stderr.strip().split("\n"))
        error_message += "\n"

    if result.returncode != 0:
        error_message += f"Command failed with return code: {result.returncode}\n"
    else:
        error_message += "Command exit code: 0\n"

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


def check_output_matches(given: list[str], expected: list[str]):
    """
    Check if the expected output is contained in the given output

    given: list of strings representing the actual output
    expected: list of strings representing the expected output
    """
    # Check if the stdout matches the expected stdout
    exp_std_inx = 0
    for g_out in given:
        # Check that checks don't pass before out of outputs
        if exp_std_inx >= len(expected):
            return True

        if expected[exp_std_inx] == "...":
            # If the expected output is '...' then we skip this line
            exp_std_inx += 1
            continue

        # This is incompatible with ... for line skipping
        if "***" in expected[exp_std_inx]:
            # Now do some partial checking
            partial_output = check_partial_word(g_out, expected[exp_std_inx])
            if partial_output:
                exp_std_inx += 1
            continue

        if g_out.strip() != expected[exp_std_inx].strip():
            # Check if expected has ...
            if "..." in expected[exp_std_inx]:
                # If it does, then we need to remove it and check for that line containing string
                without_gap = expected[exp_std_inx].split("...")
                if all(without_gap in g_out for without_gap in without_gap):
                    exp_std_inx += 1
                    continue

            # If the output does not match, continue without incrementing
            continue

        exp_std_inx += 1

    if exp_std_inx != len(expected):
        # It is not all contained in the output
        return False

    return True


def check_exit_code(test_outputs, test):
    if test.status == "success":
        return test_outputs.returncode == 0
    if test.status == "error":
        return test_outputs.returncode != 0
    if isinstance(test.status, int):
        return test_outputs.returncode == test.status
    return False


def check_result(test_outputs, test):
    if not check_exit_code(test_outputs, test):
        return False

    given_std_out = test_outputs.stdout.split("\n")
    given_std_err = test_outputs.stderr.split("\n")
    expected_std_out = test.stdout
    expected_std_err = test.stderr

    if not test.case_sensitive:
        given_std_out = [line.lower() for line in given_std_out]
        given_std_err = [line.lower() for line in given_std_err]
        expected_std_out = [line.lower() for line in expected_std_out]
        expected_std_err = [line.lower() for line in expected_std_err]

    return check_output_matches(
        given_std_out, expected_std_out
    ) and check_output_matches(given_std_err, expected_std_err)


# Read the test exceptions file and set the variables correctly
# pylint: disable=too-many-branches
def read_test_expectations(filename):
    """
    Read a TEST_EXPECTATIONS file and extract the core information
    Filename should be either a relative path from CWD to file
    or an absolute path.
    """
    if not filename:
        return

    with open(f"{filename}", "r", encoding="utf-8") as file:
        yaml_file = yaml.safe_load(file)

        if yaml_file is not None:
            REPORT_DETAILS.known_failures = yaml_file.get("known_failures", []) or []
            REPORT_DETAILS.failing_as_unspecified = (
                yaml_file.get("failing_as_unspecified", []) or []
            )
            REPORT_DETAILS.unsupported = yaml_file.get("unsupported", []) or []
            REPORT_DETAILS.do_not_run = yaml_file.get("do_not_run", []) or []

            path = os.path.relpath(os.path.dirname(__file__))
            if path == ".":
                path = ""

            REPORT_DETAILS.known_failures = [
                os.path.join(path, test)
                for test in REPORT_DETAILS.known_failures
                if test is not None
            ]
            REPORT_DETAILS.failing_as_unspecified = [
                os.path.join(path, test)
                for test in REPORT_DETAILS.failing_as_unspecified
                if test is not None
            ]
            REPORT_DETAILS.unsupported = [
                os.path.join(path, test)
                for test in REPORT_DETAILS.unsupported
                if test is not None
            ]
            REPORT_DETAILS.do_not_run = [
                os.path.join(path, test)
                for test in REPORT_DETAILS.do_not_run
                if test is not None
            ]


def prepare_tests():
    location = os.path.relpath(os.path.dirname(__file__))
    if not os.path.exists(location + "/Tests"):
        return [
            Definition(
                "test-setup",
                None,
                [],
                [],
                None,
                False,
                "`Tests` directory not found. Please make sure the lang_tests are installed",
            )
        ]

    # Work out settings for the application (They are labelled REQUIRED or OPTIONAL)
    if "CLASSPATH" not in os.environ:  # REQUIRED
        return [
            Definition(
                "test-setup",
                None,
                [],
                [],
                None,
                False,
                "Please set the CLASSPATH environment variable",
            )
        ]

    if "VM" not in os.environ:  # REQUIRED
        return [
            Definition(
                "test-setup",
                None,
                [],
                [],
                None,
                False,
                "Please set the VM environment variable",
            )
        ]

    if "TEST_EXPECTATIONS" in os.environ:
        read_test_expectations(os.environ["TEST_EXPECTATIONS"])

    test_files = []
    discover_test_files_candidates(location + "/Tests", test_files)
    test_files = sorted(test_files)
    return collect_tests(test_files)


def get_test_id(test):
    print(test)
    return "Tests/" + test.name.split("Tests/")[-1]


def run_test(test):
    if test.name in REPORT_DETAILS.do_not_run:
        pytest.skip("Test included in do_not_run")

    if test.definition_fail_msg:
        pytest.fail(test.definition_fail_msg)

    if test.custom_classpath is not None:
        command = f"{os.environ["VM"]} -cp {test.custom_classpath} {test.name}"
    else:
        command = f"{os.environ["VM"]} -cp {os.environ["CLASSPATH"]} {test.name}"

    try:
        result = subprocess.run(
            command, capture_output=True, text=True, shell=True, check=False
        )
    except UnicodeDecodeError:
        pytest.skip(
            "Test output could not be decoded SOM may not support "
            "full Unicode. Result object not generated."
        )
    return command, result


@pytest.mark.parametrize(
    "test",
    prepare_tests(),
    ids=get_test_id,
)
# pylint: disable=too-many-branches
def tests_runner(test):
    command, result = run_test(test)

    # lower-case comparisons unless specified otherwise
    if not test.case_sensitive:
        result.stdout = str(result.stdout).lower()
        result.stderr = str(result.stderr).lower()

    error_message = build_error_message(result, test, command)
    test_pass_bool = check_result(result, test)

    if test.name in REPORT_DETAILS.known_failures and test_pass_bool:
        REPORT_DETAILS.tests_passed_unexpectedly.append(test.name)
        assert False, f"Test {test.name} is in known_failures but passed"

    if test.name in REPORT_DETAILS.failing_as_unspecified and test_pass_bool:
        REPORT_DETAILS.tests_passed_unexpectedly.append(test.name)
        assert False, f"Test {test.name} is in failing_as_unspecified but passed"

    if test.name in REPORT_DETAILS.unsupported and test_pass_bool:
        REPORT_DETAILS.tests_passed_unexpectedly.append(test.name)
        assert False, f"Test {test.name} is in unsupported but passed"

    if (
        test.name not in REPORT_DETAILS.unsupported
        and test.name not in REPORT_DETAILS.known_failures
        and test.name not in REPORT_DETAILS.failing_as_unspecified
    ):
        if not test_pass_bool:
            REPORT_DETAILS.tests_failed_unexpectedly.append(test.name)
        assert (
            test_pass_bool
        ), f"Error on test, {test.name} expected to pass: {error_message}"
