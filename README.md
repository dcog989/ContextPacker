# ![ContextPacker logo](https://github.com/dcog989/ContextPacker/blob/main/assets/icons/ContextPacker-x64.png) ContextPacker

A desktop app to scrape websites, Git repositories, or package local files into a single file, optimized for consumption by LLMs.

![ContextPacker screenshot](https://github.com/user-attachments/assets/955e7a42-45c7-44e4-a37e-43003e49f06a)

## Features

- **Web Crawling**: Scrape a website, convert pages to Markdown, and package them into one file.
- **Git Repository Cloning**: Enter a Git URL to automatically clone the repository and switch to local packaging mode.
- **Local Packaging**: Package a local directory (e.g., a code repository) into a single file.
- **Multiple Output Formats**: Package files as `.md`, `.txt`, or `.xml`.
- **Smart Filtering**: Automatically respects `.gitignore` rules and provides an option to hide common binary and image files from the list.
- **Customizable**: Scraping options (depth, paths, speed) and file exclusions can be configured.
- **External Configuration**: Key settings can be modified in a `config.json` file.
- **Cross-Platform**: Light and Dark theme support (detects system theme on Windows, macOS, and Linux).

## Installation

1. **Install a Web Browser**: The web crawling feature requires one of the following browsers to be installed:
    - Microsoft Edge
    - Google Chrome
    - Mozilla Firefox

2. **Install Git**: The Git repository cloning feature requires `git` to be installed and accessible in your system's PATH.

3. **Install Python and Poetry**: This project uses [Poetry](https://python-poetry.org/) for dependency management. Please install a modern version of Python (3.10+) and follow the [official instructions](https://python-poetry.org/docs/#installation) to install Poetry.

4. Clone the repository or download the source code.

5. Install the required dependencies using Poetry. This command will create a virtual environment and install all necessary packages.

    ```sh
    poetry install
    ```

6. Run the application using Poetry:

    ```sh
    poetry run python app.py
    ```

## Developer Troubleshooting

### Selenium Drivers

The web crawler needs a matching browser driver. You can either:

1. **Use the helper script** (requires network access):

    ```pwsh
    poetry run python scripts/get_driver.py --browser edge   # for Edge
    poetry run python scripts/get_driver.py --browser chrome # for Chrome
    poetry run python scripts/get_driver.py --browser firefox # for Firefox
    ```

2. **Download manually** if the script fails (DNS/network issues):

    ```pwsh
    # For Edge: First, get your Edge version
    $ver = (Get-Item "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe").VersionInfo.FileVersion
    Write-Host "Edge version: $ver"
    $major = $ver.Split('.')
    Write-Host "Major version: $major"
    
    # Download and extract Edge driver for your version
    $zip = "edgedriver_win64.zip"
    $url = "https://msedgedriver.microsoft.com/${major}/edgedriver_win64.zip"
    Write-Host "Downloading from: $url"
    Invoke-WebRequest $url -OutFile $zip -UseBasicParsing
    
    New-Item -ItemType Directory -Force -Path ".drivers/edge/$major" | Out-Null
    Expand-Archive $zip -DestinationPath ".drivers/edge/$major" -Force
    Remove-Item $zip
    
    # The driver is now in .drivers/edge/<version>/msedgedriver.exe
    # Test it works:
    & "./.drivers/edge/$major/msedgedriver.exe" --version
    ```

3. **Check environment** to validate browser/driver setup:

    ```pwsh
    poetry run python scripts/check_env.py
    ```

### Running from Source

## Usage

The application has two main modes, selectable via radio buttons.

### 1. Web Crawl Mode

This mode is for scraping online content or cloning Git repositories.

1. Select the **"Web Crawl"** radio button.
2. Enter the **Start URL**.
    - For a website, enter the full URL to begin scraping.
    - For a Git repository, enter the repository's clone URL (e.g., `https://github.com/user/repo.git`). The app will detect it, clone the repo, and switch to Local Directory mode.
3. Adjust the crawling options as needed (these are ignored for Git URLs).
4. Click **"Download & Convert"**.

### 2. Local Directory Mode

This mode is for packaging local files.

1. Select the **"Local Directory"** radio button.
2. Choose the **Input Directory** you want to package.
3. Use the **Excludes** text area to list any files or directories you wish to exclude. These patterns are combined with the rules in your `.gitignore` file.
4. Use the checkboxes to include subdirectories or hide common binary and image files from the list.
5. Click **"Package"**. The application will package all visible files into a single file in your Downloads folder, using the format selected in the output dropdown.

## Configuration

On first run, the application creates a `config.json` file in the same directory. You can edit this file to customize:

- `user_agents`: The list of user-agents available in the dropdown.
- `default_local_excludes`: The default patterns that appear in the "Excludes" text box.
- `binary_file_patterns`: The list of file patterns to hide when "Hide Images + Binaries" is checked.

## Building from Source

This project uses [Nox](https://nox.thea.codes/) for task automation. Ensure you have run `poetry install` to install Nox into the development environment.

### Available Build Commands

Run these commands from the project root in your terminal.

- **Build for Production:**
    Creates a compressed archive (`.7z` or `.zip`) in the `dist` folder.

    ```sh
    poetry run nox -s build
    ```

- **Build and Run for Debugging:**
    Builds a version with the console enabled, then launches it immediately.

    ```sh
    poetry run nox -s build-run
    ```

- **Clean Build Artifacts:**
    Removes the `dist`, `build`, and `__pycache__` directories.

    ```sh
    poetry run nox -s clean
    ```
