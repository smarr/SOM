"""
Instructions for running the integration tests for different SOM implementations
"""
INSTRUCTIONS = {
    "SOMpp" : {
        "build": ["mkdir inttesting && cd inttesting && cmake .. -DUSE_TAGGING=false -DCACHE_INTEGER=true -DGC_TYPE=COPYING -DCMAKE_BUILD_TYPE=Debug -DUSE_VECTOR_PRIMITIVES=true && make"],
        "run": "./inttesting/SOM++",
        "inttesting-loc": "./core-lib/IntegrationTests",
        "cleanup": "rm -rf inttesting"
    },
    "JsSOM" : {
        "build": ["make"],
        "run": "./som.sh",
        "inttesting-loc": "./core-lib/IntegrationTests",
        "cleanup": "NaN"
    },
    "PySOM" : {
        "build": ["NaN"],
        "run": "SOM_INTERP=AST ./som.sh",
        "inttesting-loc": "./core-lib/IntegrationTests",
        "cleanup": "NaN"
    },
    "som-java": {
        "build": ["ant jar"],
        "run": "./som.sh",
        "inttesting-loc": "./core-lib/IntegrationTests",
        "cleanup": "NaN"
    }
}

# depends on whether symlinks have been preserved
CLASSPATH = "core-lib/Smalltalk"
CLASSPATH_LINUX = "Smalltalk"