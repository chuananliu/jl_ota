"""Regenerate and validate the SwiftPM simulator placeholder frameworks on macOS."""

import plistlib
import subprocess
import tempfile
from pathlib import Path

FRAMEWORKS = (
    "DFUnits",
    "JLLogHelper",
    "JL_AdvParse",
    "JL_BLEKit",
    "JL_HashPair",
    "JL_OTALib",
)
SOURCE = Path(__file__).resolve().with_name("placeholder.c")
ROOT = SOURCE.parents[2]


def main():
    with tempfile.TemporaryDirectory(prefix="jl_ota_simulator_") as temporary:
        scratch = Path(temporary)
        for name in FRAMEWORKS:
            xcframework = ROOT / "ios" / "jl_ota" / "Frameworks" / f"{name}.xcframework"
            metadata_path = xcframework / "Info.plist"
            metadata = plistlib.loads(metadata_path.read_bytes())
            device = next(
                library
                for library in metadata["AvailableLibraries"]
                if library.get("SupportedPlatformVariant") is None
            )
            framework = xcframework / "ios-arm64-simulator" / f"{name}.framework"
            headers = framework / "Headers"
            modules = framework / "Modules"
            headers.mkdir(parents=True, exist_ok=True)
            modules.mkdir(parents=True, exist_ok=True)
            (headers / f"{name}.h").write_text(
                "// Placeholder only. Use a physical iOS device for the Jieli SDK.\n"
                '#error "The Jieli SDK is unavailable on iOS Simulator."\n'
            )
            (modules / "module.modulemap").write_text(
                f"framework module {name} {{\n"
                f'    umbrella header "{name}.h"\n'
                "    export *\n"
                "}\n"
            )
            (framework / "Info.plist").write_bytes(
                plistlib.dumps(
                    {
                        "CFBundleExecutable": name,
                        "CFBundleIdentifier": f"com.jieli.jl-ota.simulator.{name.replace('_', '-')}",
                        "CFBundleName": name,
                        "CFBundlePackageType": "FMWK",
                        "CFBundleShortVersionString": "1.0",
                        "CFBundleSupportedPlatforms": ["iPhoneSimulator"],
                        "CFBundleVersion": "1",
                        "MinimumOSVersion": "14.0",
                    }
                )
            )
            object_file = scratch / f"{name}-arm64.o"
            subprocess.run(
                [
                    "xcrun",
                    "--sdk",
                    "iphonesimulator",
                    "clang",
                    "-target",
                    "arm64-apple-ios14.0-simulator",
                    f"-DJL_OTA_SIMULATOR_SYMBOL=jl_ota_simulator_{name}",
                    "-c",
                    str(SOURCE),
                    "-o",
                    str(object_file),
                ],
                check=True,
            )
            destination = framework / name
            # Match the vendor's linkage: DFUnits is static; the other five are dynamic.
            if name == "DFUnits":
                link_command = ["xcrun", "libtool", "-static", "-D"]
            else:
                link_command = [
                    "xcrun",
                    "--sdk",
                    "iphonesimulator",
                    "clang",
                    "-target",
                    "arm64-apple-ios14.0-simulator",
                    "-dynamiclib",
                    "-install_name",
                    f"@rpath/{name}.framework/{name}",
                ]
            subprocess.run(
                [*link_command, "-o", str(destination), str(object_file)],
                check=True,
            )
            # Use Xcode's parser to validate the device/simulator pair and generate
            # the correct framework metadata, instead of hand-authoring a .a entry.
            validated = scratch / f"{name}.xcframework"
            subprocess.run(
                [
                    "xcodebuild",
                    "-create-xcframework",
                    "-framework",
                    str(
                        xcframework
                        / device["LibraryIdentifier"]
                        / device["LibraryPath"]
                    ),
                    "-framework",
                    str(framework),
                    "-output",
                    str(validated),
                ],
                check=True,
            )
            validated_metadata = plistlib.loads((validated / "Info.plist").read_bytes())
            simulator = next(
                library
                for library in validated_metadata["AvailableLibraries"]
                if library.get("SupportedPlatformVariant") == "simulator"
            )
            metadata["AvailableLibraries"] = [device, simulator]
            metadata_path.write_bytes(plistlib.dumps(metadata, sort_keys=False))
            print(f"Generated and validated {destination.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
