# TO DO

- the UI locks up while scraping web content - the user should be able to resize it

- https://pypi.org/project/playwright/ instead of Selenium?

---

## PENDING


---

## FUTURE WORK


Of course. If I were to build this application from scratch today with a focus on modern development practices, performance, and maintainability, here is the stack I would choose:

### Summary of the Recommended Stack

| Component                | Recommended Technology                                   | Reason for Choice                                        |
| ------------------------ | -------------------------------------------------------- | -------------------------------------------------------- |
| **Language**             | Python 3.12+                                             | High-level, excellent ecosystem for this task.          |
| **GUI Framework**        | **PyQt6** / **PySide6**                                  | Modern, powerful, native look, excellent styling (QSS).  |
| **Web Scraping**         | **Playwright** + **BeautifulSoup4**                      | Faster, more reliable, better API than Selenium.         |
| **File System Logic**    | Python's built-in **`pathlib`** module                   | Object-oriented, clean, and robust for file operations.  |
| **App Distribution**     | **PyInstaller**                                          | The industry standard for creating standalone executables. |

---

### Detailed Breakdown

#### 1. Language: Python
The original choice of Python is still the best. It excels at the "glue" tasks required here: file I/O, web requests, and text processing. The vast library ecosystem is a major advantage.

#### 2. GUI Framework: PyQt6 / PySide6
This would be the most significant change. While `wxPython` is functional, **PyQt** (or its more liberally licensed sibling, PySide) offers a more modern and powerful development experience.

*   **Why it's better:**
    *   **Modern Widgets & Styling:** PyQt's widgets feel more contemporary, and you can style the entire application using **QSS**, which is analogous to CSS for web pages. This makes creating a beautiful, custom theme (like the dark mode in the current app) far easier and more powerful.
    *   **Professional Tooling:** It comes with **Qt Designer**, a drag-and-drop tool for building UIs, which dramatically speeds up layout work.
    *   **Excellent Documentation & Community:** It is one of the most widely used GUI libraries for Python, with extensive documentation and community support.

#### 3. Web Scraping: Playwright + BeautifulSoup4
Selenium is a classic, but **Playwright** is its modern successor, developed by Microsoft. It is designed for the modern web and is generally faster and more reliable.

*   **Why it's better:**
    *   **Performance and Reliability:** Playwright's architecture often leads to faster and less flaky automation. It has more intelligent "auto-wait" mechanisms, which reduces the need for manual `sleep` or `wait` commands.
    *   **Modern API:** It has a cleaner, async-first API that is a pleasure to work with.
    *   **Browser Management:** It handles its own browser installations, which can simplify setup and avoid the driver-mismatch issues that sometimes plague Selenium.

I would still use **BeautifulSoup4** with the `lxml` parser on the page content fetched by Playwright. Its ability to parse messy HTML is second to none.

#### 4. File System & Packaging Logic: `pathlib`
The core logic of walking through directories, reading `.gitignore`, filtering files, and concatenating them into a single output file can be written cleanly using Python's standard library.

*   **Why it's better:**
    *   The `pathlib` module provides an object-oriented interface for file system paths (e.g., `path.read_text()`, `path.iterdir()`, `path.glob('*.py')`). This results in code that is more readable and less error-prone than using older string-based methods from the `os` module.
    *   This removes the dependency on `repomix` and gives full control over the packaging logic, which at its core is not overly complex for this application's needs.

#### 5. Application Distribution: PyInstaller
This choice would remain the same. **PyInstaller** is the gold standard for packaging Python applications into single-file executables for Windows, macOS, and Linux. It is mature, well-supported, and handles complex dependencies effectively.