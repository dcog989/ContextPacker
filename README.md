# ![ContextPacker logo](https://github.com/dcog989/ContextPacker/blob/main/assets/icons/ContextPacker-x64.png) ContextPacker

A desktop app to scrape websites, Git repositories, or package local files into a single file, optimized for consumption by LLMs.

![ContextPacker screenshot](https://github.com/user-attachments/assets/955e7a42-45c7-44e4-a37e-43003e49f06a)

## Features

* **Web Crawling**: Scrape a website, convert pages to Markdown, and package them into one file.
* **Git Repository Cloning**: Enter a Git URL to automatically clone the repository and switch to local packaging mode.
* **Local Packaging**: Package a local directory (e.g., a code repository) into a single file.
* **Multiple Output Formats**: Package files as `.md`, `.txt`, or `.xml`.
* **Smart Filtering**: Automatically respects `.gitignore` rules and provides an option to hide common binary and image files from the list.
* **Customizable**: Scraping options (depth, paths, speed) and file exclusions can be configured.
* **External Configuration**: Key settings can be modified in a `config.json` file.
* **Cross-Platform**: Light and Dark theme support (detects system theme on Windows, macOS, and Linux).

## Installation

1. **Install a Web Browser**: The web crawling feature requires one of the following browsers to be installed:
    * Microsoft Edge
    * Google Chrome
    * Mozilla Firefox

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

## Usage

The application has two main modes, selectable via radio buttons.

### 1. Web Crawl Mode

This mode is for scraping online content or cloning Git repositories.

1. Select the **"Web Crawl"** radio button.
2. Enter the **Start URL**.
    * For a website, enter the full URL to begin scraping.
    * For a Git repository, enter the repository's clone URL (e.g., `https://github.com/user/repo.git`). The app will detect it, clone the repo, and switch to Local Directory mode.
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

* `user_agents`: The list of user-agents available in the dropdown.
* `default_local_excludes`: The default patterns that appear in the "Excludes" text box.
* `binary_file_patterns`: The list of file patterns to hide when "Hide Images + Binaries" is checked.

## Building from Source

You can create a standalone executable using the included PowerShell build script.

1. Ensure you have followed the installation steps and installed dependencies with `poetry install`.
2. The repository includes a pre-configured `ContextPacker.spec` file and a runtime hook (`pyi_rth_selenium.py`) to correctly handle Selenium's dependencies.
3. Run the interactive builder from a PowerShell terminal:

    ```powershell
    # Navigate to the .build-tools directory
    cd .build-tools
    
    # Run the builder script
    ./Builder.ps1
    ```

4. Select an option from the menu, such as "Build Executable (Production)".
5. The final executable will be located in the `dist` folder.

## Technology Stack

* **UI**: Python with [wxPython](https://wxpython.org/)
* **Web Scraping**: [Selenium](https://www.selenium.dev/) + [Beautiful Soup](https://pypi.org/project/beautifulsoup4/)
* **HTML to Markdown**: [markdownify](https://pypi.org/project/markdownify/)
* **File Packaging**: [repomix](https://pypi.org/project/repomix/)
