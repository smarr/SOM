use std::{env, fs::read_to_string, path::PathBuf, process::Command};

use lang_tester::LangTester;
use lazy_static::lazy_static;
use regex::{Regex, RegexBuilder};

const SOM_LIBS_PATH: &'static str = "SOM/Smalltalk";

lazy_static! {
    static ref EXPECTED: Regex = RegexBuilder::new(r#"^"(.*?)^"[ \t]*$"#)
        .multi_line(true)
        .dot_matches_new_line(true)
        .build()
        .unwrap();
}

fn main() {
    LangTester::new()
        .test_dir("lang_tests")
        .test_path_filter(|p| {
            if p.is_file()
                && p.parent().unwrap().file_name().unwrap().to_str() == Some("lang_tests")
            {
                p.extension().unwrap().to_str().unwrap() == "som"
            } else {
                p.is_file() && p.file_name().unwrap() == "test.som"
            }
        })
        .test_extract(|p| {
            EXPECTED
                .captures(&read_to_string(p).unwrap())
                .map(|x| x.get(1).unwrap().as_str().trim().to_owned())
                .unwrap()
        })
        .test_cmds(|p| {
            // We call target/[debug|release]/yksom directly, because it's noticeably faster than
            // calling `cargo run`.
            let mut yksom_bin = PathBuf::new();
            yksom_bin.push(env::var("CARGO_MANIFEST_DIR").unwrap());
            yksom_bin.push("target");
            #[cfg(debug_assertions)]
            yksom_bin.push("debug");
            #[cfg(not(debug_assertions))]
            yksom_bin.push("release");
            yksom_bin.push("yksom");
            let mut vm = Command::new(yksom_bin);
            vm.args(&["--cp", SOM_LIBS_PATH, p.to_str().unwrap()]);
            vec![("VM", vm)]
        })
        .run();
}
