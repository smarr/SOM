import subprocess
from pathlib import Path
from defs import INSTRUCTIONS, CLASSPATH

location = "./core-lib/IntegrationTests/Tests" # This is a definite location of this file
locations = {"build": [], "run": "", "classpath": "", "inttesting-loc": "", "cleanup": ""}

def test_main():
    """
    Runs the main test function
    Locates SOM executable, loads classpaths and tests runs them and reports back
    """

    # First consider which SOM we are using
    repo = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
    name = repo.split("/")[-1]

    locations["classpath"] = CLASSPATH
    locations["build"] = INSTRUCTIONS[name]["build"]
    locations["run"] = INSTRUCTIONS[name]["run"]
    locations["executable"] = INSTRUCTIONS[name]["run"]
    locations["inttesting-loc"] = INSTRUCTIONS[name]["inttesting-loc"]
    locations["cleanup"] = INSTRUCTIONS[name]["cleanup"]

    # First open any tests to be ignored
    with open(f"{locations["inttesting-loc"]}/ignored_tests.txt", "r") as f:
        ignoredTests = [Path(line.strip()) for line in f.readlines()]

    testFiles = []
    readDirectory(location, testFiles, ignoredTests) # locate tests
    testsToBeRun = assembleTestDictionary(testFiles) # parse tests
    
    # Run the tests
    failed = runTests(testsToBeRun)

    print("\n\nIgnored Tests:\n")
    for ignoredTest in ignoredTests:
        print(f"Test {ignoredTest} was ignored")

    print("\n\nFailed Tests:\n")
    for test in failed:
        print(f"Test {test} failed")

    print("\n\nSummary of tests:")
    print(f"Total tests passed: {len(testFiles)-len(failed)}")
    print(f"Total tests ignored: {len(ignoredTests)}")
    print(f"Total tests failed: {len(failed)}")
    print("\nCheck above for a full list of ignored/ran/failed tests")

    for test in failed:
        print(test)

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
    testDict = {"name": testFile, "stdout": [], "stderr": []}
    with open(testFile, 'r') as f:
        contents = f.read()
        if "IGNORE" in contents:
            return None
        comment = contents.split("\"")[1]
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

    return testDict

    

def runTests(testsToBeRun):
    """
    Take an array of dictionaries with test file names and expected output
    Build the SOM executable if required
    Run all of the tests and check the output
    Cleanup the build directory if required
    """

    failedTests = []

    # check if we are using a compiled language or a interpreted language
    if locations["build"] != "NaN":
        print("Building the SOM executable")
        subprocess.run(locations["build"], shell=True)

    print("\n\nRunning tests\n")

    count = 0
    for x in testsToBeRun:
        count += 1
        print(f"Running test {count}/{len(testsToBeRun)}: {x['name']}")
        result = subprocess.run(
            [str(locations["run"]), "-cp", locations["classpath"], x["name"]],
            capture_output=True,
            text=True 
        )

        # SOM level errors will be raised in stdout only SOM++ errors are in stderr (Most tests are for SOM level errors) STILL NEEDS MORE WORK
        if all(element in result.stdout for element in x["stdout"]) and all(element in result.stderr for element in x["stderr"]) or all(element in result.stderr for element in x["stdout"]) and all (element in result.stdout for element in x["stderr"]):
            continue
        else:
            print(f"Test {x['name']} failed")
            print(f"Expected stdout: \n{x['stdout']}")
            print(f"Expected stderr: \n{x['stderr']}")
            print(f"Actual stdout: \n{result.stdout}")
            print(f"Actual stderr: \n{result.stderr}\n")
            failedTests.append(x["name"])

    if locations["cleanup"] != "NaN":
        subprocess.run(locations["cleanup"], shell=True)

    return failedTests