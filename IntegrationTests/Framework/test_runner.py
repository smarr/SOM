import subprocess
from pathlib import Path
from defs import INSTRUCTIONS
import os
import sys
import pytest

global CLASSPATH
global EXECUTABLE
global TESTS_LIST

def locateTests(path, testFiles, ignoredTests):
    """
    Locate all test files that exist in the given directory
    Ignore any tests which are in the ignoredTests directory
    Return a list of paths to the test files
    """

    # To ID a file will be opened and at the top there should be a comment which starts with VM:
    for file in Path(path).glob("*.som"):
        # Check if the file is in the ignored tests (Check via path, multiple tests named test.som)
        if (file in ignoredTests):
            continue
        else:
            with open(file, 'r') as f:
                contents = f.read()
                if "VM" in contents:
                    testFiles.append(file)

    return testFiles

def readDirectory(path, testFiles, ignoredTests):
    """
    Recursively read all sub directories
    Path is the directory we are currently in
    testFiles is the list of test files we are building up
    ignoredTests is the list of test files that should be ignored
    """
    for directory in Path(path).iterdir():
        if directory.is_dir():
            readDirectory(directory, testFiles, ignoredTests)
        else:
            continue

    locateTests(path, testFiles, ignoredTests)

def assembleTestDictionary(testFiles):
    """
    Assemble a dictionary of
    name: the name of the test file
    stdout/stderr: the expected output of the test
    """
    tests = []
    for file in testFiles:
        testDict = parseTestFile(file)
        if (testDict is None):
            continue
        tests.append(testDict)
        
    return tests

def parseTestFile(testFile):
    """
    parse the test file to extract the important information
    """
    testDict = {"name": testFile, "stdout": [], "stderr": [], "customCP": "NaN"}
    with open(testFile, 'r') as f:
        contents = f.read()
        comment = contents.split("\"")[1]

        # Make sure if using a custom test classpath that it is above
        # Stdout and Stderr
        if "customCP" in comment:
            commentLines = comment.split("\n")
            for line in commentLines:
                if "customCP" in line:
                    testDict["customCP"] = line.split("customCP:")[1].strip()
                    continue

        if "stdout" in comment:
            stdOut = comment.split("stdout:")[1]
            if "stderr" in stdOut:
                stdErrInx = stdOut.index("stderr:")
                stdOut = stdOut[:stdErrInx]
            stdOut = stdOut.replace("...", "")
            stdOutL = stdOut.split("\n")
            stdOutL = [line.strip() for line in stdOutL if line.strip()]
            testDict["stdout"] = stdOutL

        if "stderr" in comment:
            stdErr = comment.split("stderr:")[1]
            if "stdout" in stdErr:
                stdOutInx = stdErr.index("stdout:")
                stdErr = stdErr[:stdOutInx]
            stdErr = stdErr.replace("...", "")
            stdErrL = stdErr.split("\n")
            stdErrL = [line.strip() for line in stdErrL if line.strip()]
            testDict["stderr"] = stdErrL

        testTuple = (testDict["name"], testDict["stdout"], testDict["stderr"], testDict["customCP"])

    return testTuple

def idfn(name):
    """
    Generate a unique ID for each test based on the test name
    Tests that are in IntegrationTests/Tests are just their filename
    Tests that are in subdirectories will have their relative path preserved
    """
    finalName = str(name).replace("core-lib/IntegrationTests/Tests/", "")
    return finalName


location = "./core-lib/IntegrationTests/Tests" # This is a definite location of this file

if "CLASSPATH" not in os.environ:
    sys.exit("Please set the CLASSPATH environment variable")

if "EXECUTABLE" not in os.environ:
    sys.exit("Please set the EXECUTABLE environment variable")

CLASSPATH = os.environ["CLASSPATH"]
EXECUTABLE = os.environ["EXECUTABLE"]

# First open any tests to be ignored
with open(f"./core-lib/IntegrationTests/ignored_tests.txt", "r") as f:
    ignoredTests = [Path(line.strip()) for line in f.readlines()]

# Now check if we have any supplementary implementation specific tests to ignore
if (Path(f"./pignore").exists()):
    with open("./pignore", "r") as f:
        for line in f.readlines():
            if line not in ignoredTests:
                ignoredTests.append(Path(line.strip()))
            else:
                continue

testFiles = []
readDirectory(location, testFiles, ignoredTests)
TESTS_LIST = assembleTestDictionary(testFiles)



@pytest.mark.parametrize("name,stdout,stderr,customCP", TESTS_LIST, ids=idfn)
def tests_runner(name, stdout, stderr, customCP):
    """
    Take an array of dictionaries with test file names and expected output
    Run all of the tests and check the output
    Cleanup the build directory if required
    """
    global EXECUTABLE, CLASSPATH

    failedTests = []


    if (customCP != "NaN"):
        command = f"{EXECUTABLE} -cp {customCP} {name}"
    else:
        command = f"{EXECUTABLE} -cp {CLASSPATH} {name}"

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        shell=True
    )

    # SOM level errors will be raised in stdout only SOM++ errors are in stderr (Most tests are for SOM level errors) STILL NEEDS MORE WORK
    assert all(element in result.stdout for element in stdout) and all(element in result.stderr for element in stderr) or all(element in result.stderr for element in stdout) and all (element in result.stdout for element in stderr), "Test failed for: " + name