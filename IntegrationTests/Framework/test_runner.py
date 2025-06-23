import subprocess
from pathlib import Path

location = "./core-lib/IntegrationTests/Tests"
locations = {"build": "", "executable": "", "classpath": "", "inttesting-loc": "", "cleanup": ""}

def test_main():
    """
    Runs the main test function
    Locates SOM executable, loads classpaths and tests runs them and reports back
    """

    # First locate the classpaths file
    classpaths_file = Path("./classpaths")
    if not classpaths_file.exists():
        raise FileNotFoundError("classpaths file not found. Please ensure it exists in the root directory.")
    with open(classpaths_file, 'r') as f:
        classpaths = f.read()
        lines = classpaths.split("\n")
        for line in lines:
            if line.startswith("build:"):
                locations["build"] = line.split(":", 1)[1].strip()
            elif line.startswith("executable:"):
                locations["executable"] = line.split(":", 1)[1].strip()
            elif line.startswith("classpath:"):
                locations["classpath"] = line.split(":", 1)[1].strip()
            elif line.startswith("inttesting-loc:"):
                locations["inttesting-loc"] = line.split(":", 1)[1].strip()
            elif line.startswith("cleanup:"):
                locations["cleanup"] = line.split(":", 1)[1].strip()


    # First open any tests to be ignored
    with open(f"{locations["inttesting-loc"]}ignored_tests.txt", "r") as f:
        ignoredTests = [Path(line.strip()) for line in f.readlines()]

    testFiles = []
    readDirectory(location, testFiles, ignoredTests) # locate tests
    testsToBeRun = assembleTestDictionary(testFiles) # parse tests
    
    # Run the tests
    runTests(testsToBeRun)

    print("\n\nIgnored Tests:\n")
    for ignoredTest in ignoredTests:
        print(f"Test {ignoredTest} was ignored")

    print("\n\nSummary of tests:")
    print(f"Total tests passed: {len(testFiles)}")
    print(f"Total tests ignored: {len(ignoredTests)}")
    print("\nCheck above for a full list of ignored tests and ran tests")

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

    # check if we are using a compiled language or a interpreted language
    if locations["build"] != "NaN":
        subprocess.run(locations["build"], shell=True)

    print("\n\nRunning tests\n")

    count = 0
    for x in testsToBeRun:
        count += 1
        print(f"Running test {count}/{len(testsToBeRun)}: {x['name']}")
        result = subprocess.run(
            [str(locations["executable"]), "-cp", locations["classpath"], x["name"]],
            capture_output=True,
            text=True 
        )

        # SOM level errors will be raised in stdout only SOM++ errors are in stderr (Most tests are for SOM level errors) STILL NEEDS MORE WORK
        assert all(element in result.stdout for element in x['stdout']) or all(element in result.stderr for element in x['stdout']), f"Expected output ({x['stdout']}) not found in stdout for test {x['name']}"

    if locations["cleanup"] != "NaN":
        subprocess.run(locations["cleanup"], shell=True)