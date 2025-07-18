"""
Add custom reporting and test selection to pytest.
The test selection is done by using the "-m tester" option.
This way, we only run the tests of the test runner, when explicitly requested.
The standard case is, we want to run the SOM tests, and no the test runner tests.
"""

import os
import yaml


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
    if (
        "GENERATE_EXPECTATIONS_FILE" in os.environ
        and os.environ["GENERATE_EXPECTATIONS_FILE"]
    ):
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
                "virtual machine": os.environ["VM"],
                "classpath": os.environ["CLASSPATH"],
                "test_expectations": os.environ["TEST_EXPECTATIONS"],
                "expectations_file": os.environ["GENERATE_EXPECTATIONS_FILE"],
            },
            "known_failures": REPORT_DETAILS.known_failures,
            "failing_as_unspecified": REPORT_DETAILS.failing_as_unspecified,
            "unsupported": REPORT_DETAILS.unsupported,
            "do_not_run": REPORT_DETAILS.do_not_run,
        }
        with open(
            f"{os.environ["GENERATE_EXPECTATIONS_FILE"]}", "w", encoding="utf-8"
        ) as f:
            yaml.dump(report_data, f, default_flow_style=False, sort_keys=False)
