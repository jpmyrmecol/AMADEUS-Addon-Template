# AMADEUS Add-on Template

An independent Python application that can be installed and launched from AMADEUS Home. The template does not import AMADEUS, Ultralytics, or any AMADEUS implementation code. It reads result CSV files and `config.yaml` through file paths.

This repository is distributed under **0BSD**. Its visibility is controlled by the repository owner. The template does not require a public repository or an authenticated connection to AMADEUS.

## Try the template

Use Python 3.12 or newer. Build the package without installing dependencies:

```sh
python build_addon.py
```

The installable ZIP and its SHA-256 file appear in `dist/`. In a version of AMADEUS that includes add-on support, select **Add-ons** above **Update** on Home. Drop the ZIP into the installer or select it with **Browse**. Review the confirmation and approve installation. AMADEUS creates a separate Python environment and installs the declared dependencies.

Click **Result Viewer (template)** on the right of Home. Select a results CSV, a configuration file, or both. **Read files** previews their contents. Input files are never overwritten by this example. Selected paths are saved in the persistent data directory provided by the host.

The viewer does not perform behavioral analysis. It deliberately does not infer CSV frame counts, animal counts, coordinates, units or angle conventions. `records_after_first_row` counts CSV records after the first record. All CSV cell values are retained as strings.

## Develop independently

Create a virtual environment and install the example's direct dependency:

```sh
python -m venv .venv
```

On Windows:

```powershell
.venv\Scripts\python -m pip install PyYAML==6.0.2
.venv\Scripts\python app.py
```

On macOS or Linux:

```sh
.venv/bin/python -m pip install PyYAML==6.0.2
.venv/bin/python app.py
```

The application also accepts `--config PATH` and `--results PATH`. `--check` reads files and prints JSON without opening a GUI. `--data-dir PATH` selects a settings directory for standalone use. When launched by AMADEUS, `AMADEUS_ADDON_DATA_DIR` provides the persistent location automatically.

This template opts in to dropping `.csv`, `.yaml`, and `.yml` files onto its Home panel through the `drop_extensions` field in `addon.json`. A dropped file is passed to the independent process as `--dropped-file PATH`. The viewer uses CSV files as results and YAML files as configuration. Ordinary clicks still launch without a file. To allow video drops in your own application, declare its video suffixes (such as `.mp4` or `.avi`) and implement the `--dropped-file` argument yourself. Omit `drop_extensions` or set it to `[]` to disable Home file drops.

## Make your own add-on

Change `id`, `name`, `author`, `description`, `license`, `platforms`, `dependencies` and optional `drop_extensions` in `addon.json`. Use your own immutable qualified ID so your application does not replace this sample. Set `entry_point` to your independent Python entry script. Add your application files to `PAYLOAD` in `build_addon.py` and replace the sample GUI/reader with your implementation. Include the appropriate `LICENSE` and dependency notices.

Keep program resources relative to `__file__`. Save settings and outputs outside the program directory. The host sets the working directory to the application's persistent data directory. Do not assume that the working directory contains the application source.

Increment `version` using `MAJOR.MINOR.PATCH` for each update. Build and distribute the ZIP. The host's **Update** menu can install a newer ZIP with the same ID. **Uninstall** permanently removes the complete add-on folder, including its virtual environments, settings, data and logs. **Update** preserves settings, data and logs.

The sample declares intended support for Windows x64, macOS Apple Silicon/Intel, and Linux x64/ARM64. This declaration is not a claim that every OS/architecture has been tested. Test the actual packaged application on each platform you declare. AMADEUS itself may support a narrower set of host platforms.

## Network updates

Local ZIP updates are the default because `update_url` is `null`. They work with private repositories. The installed application does not inherit a developer's or ChatGPT's GitHub credentials.

For public updates, set `update_url` in `addon.json` to a stable HTTPS URL for your update descriptor. Build the release with its final ZIP URL:

```sh
python build_addon.py --download-url https://example.org/releases/my-addon-1.0.0.zip
```

Upload the ZIP and then the generated `dist/update.json` to your server or release hosting. The descriptor contains the ID, version, ZIP URL and SHA-256. The host downloads a newer release only when the user selects **Update**, verifies the package, and asks for installation consent. URLs must not contain credentials.

## Tests

After installing PyYAML in the selected Python environment:

```sh
python -m unittest discover -s tests -v
```

Tests cover read-only file handling, unsafe YAML rejection, standalone invocation, deterministic ZIP creation and update checksums. Also test the ZIP using the real AMADEUS Home on each intended OS. Native D&D and uv runtime downloads require separate integration checks.

## Specification and licensing

The authoritative format and security notes are in [AMADEUS's add-on guide](https://github.com/jpmyrmecol/AMADEUS/blob/main/tools/ADDONS.md). Format 1 supports independent Python entry scripts, exact direct dependency pins, compatible binary wheels from PyPI, and optional HTTPS update descriptors. It does not support arbitrary executable installers, private package indexes, or source builds.

The template code is [0BSD](LICENSE). Developers may use it when creating applications under other licenses, subject to the licenses of their own additions and dependencies. PyYAML has its own license. AMADEUS remains AGPL-3.0-only. This template does not grant exceptions to AMADEUS's or Ultralytics's licensing terms. Do not copy AGPL implementation code into an add-on and assume that a separate process changes its license.

Add-ons are not sandboxed. They run with the user's permissions. Include clear information about your developer identity, data access, dependencies and licensing.
