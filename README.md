# 🚀 DevCLI  

This project provides a CLI tool to manage and streamline development workflows. The tool allows adding, removing, and listing aliases while supporting custom directory navigation and execution of commands for easy boot up projects.

---

## 🌟 Features
- 🛠️ Manage aliases (`add`, `remove`, `list`) stored in a JSON file.
- ✨ Open projects in Visual Studio Code.
- 🔥 Automatically run `npm run dev`.
    - 📂 Looks after `package.json` in selected folder.

> [!NOTE]
> _Other commands coming as the need is there_ 



## ⚙️ Setup

### Prerequisites
- **Python**: Ensure Python 3.7+ is installed.
- **Node.js**: Install Node.js and ensure `npm` is in your PATH.
- **pip**: Ensure you have `pip` installed for Python package management.

---

### 1. Install Required Dependencies
Run the following command to install dependencies:

```bash
pip install click python-dotenv
```



### 2. Create a `.env` File
Create a `.env` file in the project root with the following structure:

```env
# Path to the JSON file storing aliases
ALIAS_PATH=<full/path/alias.json>

# Path to the npm executable
NODE_PATH=</full/path/nodejs/npm.cmd>

# Path to the Visual Studio Code executable
VSCODE_PATH=</full/path/Code.exe>

# Base path for project directories
BASE_PATH=</full/path>
```

- **Windows**: Update paths for `NODE_PATH` and `VSCODE_PATH` as per your installation.
- **Mac/Linux**: Use `/usr/local/bin/npm` for `NODE_PATH` and `/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code` for `VSCODE_PATH`.

---

### 3. Set Up the CLI for Your Shell

#### **Windows (PowerShell Profile)** 🖥️
1. Open your PowerShell profile:
   ```powershell
   notepad $PROFILE
   ```
2. Add the following line:
   ```powershell
   function dev { python path\\to\\your\\script.py @args }
   ```
3. Save the file and reload the profile:
   ```powershell
   . $PROFILE
   ```

#### **MacOS/Linux** 🐧
1. Open your shell configuration file (`.bashrc`, `.zshrc`, or `.bash_profile`):
   ```bash
   nano ~/.bashrc  # Or ~/.zshrc for Zsh users
   ```
2. Add the following line:
   ```bash
   alias dev="python /path/to/your/script.py"
   ```
3. Save the file and reload the shell:
   ```bash
   source ~/.bashrc  # Or source ~/.zshrc
   ```



## 📜 Usage

### Adding an Alias
```bash
dev alias add <alias_name> <alias_for>
```
Example:
```bash
dev alias add myproject "MyProject\\subFolder"
```

### Removing an Alias
```bash
dev alias remove <alias_name>
```
Example:
```bash
dev alias remove myproject
```

### Listing Aliases
```bash
dev alias list
```

### Running the CLI
To navigate to a folder and run `npm run dev`:
```bash
dev run <folder_name>
```



## 📝 Important!
- Ensure your `.env` file is configured correctly to avoid path-related issues.
- Use the appropriate shell setup instructions for your OS to enable the `dev` command globally.
