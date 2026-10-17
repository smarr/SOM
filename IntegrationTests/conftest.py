"""
Add custom reporting and test selection to pytest.
The test selection is done by using the "-m tester" option.
This way, we only run the tests of the test runner, when explicitly requested.
The standard case is, we want to run the SOM tests, and no the test runner tests.
"""

import os
import yaml


def generating_expectations():
    """Check whether to generate an expectations file."""
    return bool(
        "GENERATE_EXPECTATIONS_FILE" in os.environ
        and os.environ["GENERATE_EXPECTATIONS_FILE"]
    )


class TestVersioning:
    """The tests are versioned, and we run tests up to the configured version."""

    def __init__(self):
        self.expected_version = None
        self.test_versions = {}
        self.latest_version = 0

    def is_newer(self, test):
        """
        Tests added in a version newer than the one of the TEST_EXPECTATIONS file
        have not been categorized yet, and are thus not run.
        Without a TEST_EXPECTATIONS file, or when generating one, all tests are run.
        """
        if self.expected_version is None or generating_expectations():
            return False
        test_version = self.test_versions.get(test.name, 0)
        return test_version > self.expected_version

    def read_expected_version(self, yaml_file, filename):
        """Old expectation files may not have a version, those default to 0."""
        version = 0
        if yaml_file is not None:
            version = yaml_file.get("version", 0) or 0
        if not isinstance(version, int) or version < 0:
            raise ValueError(
                f"{filename}: version must be a non-negative integer, but was {version}"
            )
        self.expected_version = version

    def read_test_versions(self, filename):
        """
        Read the versions.yml file, which maps each version to the tests added in it.
        Tests not listed are part of version 0.
        """
        with open(filename, "r", encoding="utf-8") as file:
            yaml_file = yaml.safe_load(file) or {}

        path = os.path.relpath(os.path.dirname(__file__))
        if path == ".":
            path = ""

        test_versions = {}
        for version, tests in yaml_file.items():
            if not isinstance(version, int) or version < 1:
                raise ValueError(
                    f"{filename}: versions must be positive integers, but found {version}"
                )
            for test in tests or []:
                test_path = os.path.join(path, test)
                if test_path in test_versions:
                    raise ValueError(
                        f"{filename}: {test} is listed for version "
                        f"{test_versions[test_path]} and {version}"
                    )
                test_versions[test_path] = version

        self.test_versions = test_versions
        self.latest_version = max(test_versions.values(), default=0)


class ReportDetails:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """
    Holds info about passing and failing tests.
    """

    def __init__(self):
        self.tests_failed_unexpectedly = []
        self.tests_passed_unexpectedly = []
        self.tests_passed = 0
        self.tests_failed = 0
        self.total_tests = 0
        self.tests_skipped = 0

        self.known_failures = []
        self.failing_as_unspecified = []
        self.unsupported = []
        self.do_not_run = []
        self.version = TestVersioning()


REPORT_DETAILS = ReportDetails()


def pytest_configure(config):
    """
    Add a marker to pytest
    """
    config.addinivalue_line("markers", "tester: test the testing framework")


def pytest_collection_modifyitems(config, items):
    """
    Check if "-m tester" was specified
    """
    marker_expr = config.getoption("-m")
    run_tester_selected = False

    if marker_expr:
        # check if "tester" is anywhere in PyTest's -m expression
        run_tester_selected = "tester" in marker_expr.split(" or ")

    if not run_tester_selected:
        deselected = [item for item in items if "tester" in item.keywords]
        if deselected:
            for item in deselected:
                items.remove(item)
            config.hook.pytest_deselected(items=deselected)


def pytest_runtest_logreport(report):
    """
    Increment the counters for what action was performed
    """
    # Global required here to access counters
    # Not ideal but without the counters wouldn't work
    if report.when == "call":  # only count test function execution, not setup/teardown
        REPORT_DETAILS.total_tests += 1
        if report.passed:
            REPORT_DETAILS.tests_passed += 1
        elif report.failed:
            REPORT_DETAILS.tests_failed += 1
        elif report.skipped:
            REPORT_DETAILS.tests_skipped += 1


def pytest_sessionfinish(exitstatus):
    """
    Run after all tests completed. Generate a report of failing and passing tests.
    """
    if generating_expectations():
        # Add the tests which have failed--unexpectedly to known_failures.
        # Remove those that have passed from any of those lists.
        for test_path in REPORT_DETAILS.tests_passed_unexpectedly:
            test = str(test_path)
            if test in REPORT_DETAILS.known_failures:
                REPORT_DETAILS.known_failures.remove(test)
            if test in REPORT_DETAILS.unsupported:
                REPORT_DETAILS.unsupported.remove(test)
            if test in REPORT_DETAILS.failing_as_unspecified:
                REPORT_DETAILS.failing_as_unspecified.remove(test)

        if REPORT_DETAILS.tests_failed_unexpectedly:
            for test in REPORT_DETAILS.tests_failed_unexpectedly:
                # Remove the part of the path that is incompatible with multiple directory running
                REPORT_DETAILS.known_failures.append(
                    "Tests/" + str(test).rsplit("Tests/", maxsplit=1)[-1]
                )

        # Generate a report_message to save
        report_data = {
            "version": REPORT_DETAILS.version.latest_version,
            "summary": {
                "tests_total": REPORT_DETAILS.total_tests,
                "tests_passed": REPORT_DETAILS.tests_passed,
                "tests_failed": REPORT_DETAILS.tests_failed,
                "tests_skipped": REPORT_DETAILS.tests_skipped,
                "pytest_exitstatus": str(exitstatus),
                "note": "Totals include expected failures",
            },
            "unexpected": {
                "passed": [
                    "Tests/" + str(test).rsplit("Tests/", maxsplit=1)[-1]
                    for test in REPORT_DETAILS.tests_passed_unexpectedly
                ],
                "failed": [
                    "Tests/" + str(test).rsplit("Tests/", maxsplit=1)[-1]
                    for test in REPORT_DETAILS.tests_failed_unexpectedly
                ],
            },
            "environment": {
                "virtual machine": os.environ.get("VM", None),
                "classpath": os.environ.get("CLASSPATH", None),
                "test_expectations": os.environ.get("TEST_EXPECTATIONS", None),
                "expectations_file": os.environ["GENERATE_EXPECTATIONS_FILE"],
            },
            "known_failures": REPORT_DETAILS.known_failures,
            "failing_as_unspecified": REPORT_DETAILS.failing_as_unspecified,
            "unsupported": REPORT_DETAILS.unsupported,
            "do_not_run": REPORT_DETAILS.do_not_run,
        }
        with open(os.environ["GENERATE_EXPECTATIONS_FILE"], "w", encoding="utf-8") as f:
            yaml.dump(report_data, f, default_flow_style=False, sort_keys=False)
