//! Windows only: embed the app icon and version info into `elecraft.exe`. Elsewhere a no-op.

fn main() {
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed=../../assets/app-icon/elecraft.ico");
    println!("cargo:rerun-if-env-changed=CADCRAFT_REQUIRE_WINRES");
    println!("cargo:rerun-if-env-changed=CADCRAFT_BUILD_SHA");
    if std::env::var("CARGO_CFG_TARGET_OS").as_deref() != Ok("windows") {
        return;
    }
    let mut res = winresource::WindowsResource::new();
    if std::path::Path::new("../../assets/app-icon/elecraft.ico").exists() {
        res.set_icon("../../assets/app-icon/elecraft.ico");
    }
    res.set("ProductName", "Elecraft")
        .set("FileDescription", "Elecraft computer-aided design")
        .set("LegalCopyright", "Copyright (c) 2026 ArtCraft Team and the CADCraft contributors. MIT OR Apache-2.0.")
        .set("OriginalFilename", "elecraft.exe")
        .set("InternalName", "elecraft");
    if let Err(e) = res.compile() {
        if std::env::var_os("CADCRAFT_REQUIRE_WINRES").is_some() {
            eprintln!("embedding Windows resources failed: {e}");
            std::process::exit(1);
        }
        println!("cargo:warning=elecraft.exe built without icon/version resources: {e}");
    }
}
