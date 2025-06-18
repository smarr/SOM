import subprocess
from pathlib import Path

# testsToBeRun = ["./VecTest.som", "./Supplement.som"]
testsToBeRun = [{"test": "./VecTest.som", "expected": "I AM VECTOR"}, {"test": "./Supplement.som", "expected": "I AM SUPPLEMENT"}]

def test_sompp_program_runs():
    """
    Take an array of dictionaries with test file names and expected output
    Run all of the tests and report back on the results
    """

    # Define the command
    sompp_path = Path("./cmake-build/SOM++")  # Adjust if it's elsewhere or not executable
    classpath = "./core-lib/Smalltalk"

    print("\n\nRunning tests")

    for x in testsToBeRun:
        # Run the process
        result = subprocess.run(
            [str(sompp_path), "-cp", classpath, x["test"]],
            capture_output=True,
            text=True  # Decode output as string (Python 3.7+)
        )

        # Assert that it executed successfully
        # assert "I love Keira" in result.stdout, "'I love Keira' not found in output"
        assert x['expected'] in result.stdout, "ERROR message not containsed in stderr"
        print(f"Test {x['test']} executed successfully")
