Here's a comprehensive guide to Claude Code hooks based on my research.

---

### Quick Reference: Claude Code Hooks

| Your Question | Short Answer |
| :--- | :--- |
| **1. Shell/Environment** | Hooks execute as shell commands using your system's default shell (`/bin/bash`, `zsh`, or PowerShell on Windows), with access to your full user environment and permissions. |
| **2. Trigger Order** | Hooks fire based on lifecycle events: `PreToolUse` (before any tool) -> Tool Execution -> `PostToolUse` (after success). They run in the order defined in your `settings.json`, and `PreToolUse` can block execution. |
| **3. Command Execution** | Executed as standard shell commands. They can be simple one-liners or calls to scripts. The command is defined as a string and executed directly by Claude Code. |
| **4. Environment Variables** | Yes, several. These include `CLAUDE_BASH_NO_LOGIN`, `CLAUDE_TOOL_NAME`, `CLAUDE_FILE_PATHS`, and custom ones you can set in your settings files. |
| **5. Debugging** | Use the `/hooks` command to verify configuration, run `claude --debug` for verbose logs, and test your hook commands manually in a terminal. |

---

### 1. How Claude Code Executes Hooks (Shell/Environment)

Claude Code executes hooks by running the `command` string you provide directly in a shell environment. The specifics are as follows:

- **Shell**: On macOS and Linux, it uses your default shell (e.g., `/bin/bash` or `zsh`). On Windows, it uses PowerShell. The shell has access to your full user environment, including your `PATH`, so any command-line tool you have installed (like `jq`, `git`, `npm`, `python`) is available.
- **Environment**: The shell inherits the environment variables from the Claude Code process. You can influence this with the `env` field in your settings file or by using environment variables to modify Claude Code's own behavior.

**Key Environment Variable for Shell Behavior:**
- `CLAUDE_BASH_NO_LOGIN`: By default, the `Bash` tool uses a login shell, which can be slow as it sources profile files. Setting `CLAUDE_BASH_NO_LOGIN=1` tells Claude Code to use a non-login, interactive shell for faster command execution. This is useful for short, frequent commands.

### 2. When Hooks are Triggered and In What Order

Hooks are triggered by specific lifecycle events. The order of execution is determined by the event type and the configuration.

**Hook Events (in approximate order of a typical tool use):**

1.  **`PreToolUse`**: This is the first opportunity to intervene. It fires *before* a specific tool (like `Bash`, `Edit`, or `Write`) is executed. This hook can be used to block the action by exiting with code `2`.
2.  **Tool Execution**: The tool itself runs (e.g., the `Bash` command is executed, the file is edited).
3.  **`PostToolUse`**: This fires *after* a tool has successfully run. It cannot block the action that just happened, but it's ideal for follow-up tasks like auto-formatting, linting, or running tests.
4.  **`Notification`**: This hook fires when Claude Code sends a notification to the user (e.g., when waiting for input). It's informational and cannot block execution.
5.  **`Stop`**: This hook runs when the main Claude Code agent finishes responding. It can be configured to prevent the agent from stopping.
6.  **`SubagentStop`**: Similar to `Stop`, but for when a sub-agent completes its task.

**Order of Execution:**
- For a single event (like `PreToolUse`), hooks run in the order they are defined in the `hooks` array within your `settings.json`.
- If you have multiple `matcher` sections for the same event, they are processed in the order they appear in the configuration file.
- The `PermissionRequest` event is a fallback, firing when a tool would normally show the user a permission dialog, and after any `PreToolUse` hooks have run.

### 3. How the Command is Executed

The command is executed as a standard shell command. The `command` field in your `settings.json` is a string that is passed directly to the shell.

**Configuration Format (JSON):**
The hooks are configured in a JSON object under the `hooks` key, with the event name as the key.
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/pre-bash-firewall.sh"
          }
        ]
      }
    ]
  }
}
```
- **`type`**: For now, the only documented type is `"command"`.
- **`command`**: The shell command to run. This can be a one-liner or a path to an executable script (e.g., `python my_hook.py`).
- **`matcher`**: An optional field to filter which tool calls the hook applies to. For `PreToolUse` and `PostToolUse`, it often matches the tool name (like `"Bash"` or `"Edit"`). For `Notification` events, it can match the notification type.

**Input and Output:**
- **Input (stdin)**: The hook script receives a JSON object via standard input. This object contains all the context about the event, such as `session_id`, `tool_name`, and `tool_input` (which includes the command to be run or the file to be edited).
- **Output (stdout/stderr)**: The hook communicates back to Claude Code primarily through its **exit code**.
    - **Exit Code 0**: Success. Any output to `stdout` is shown to the user, but not to the Claude model.
    - **Exit Code 2**: **Blocking Error**. This is only effective for `PreToolUse` hooks. It tells Claude Code to halt the action. The text sent to `stderr` is fed back to the model, which will see the error and adjust its plan.
    - **Other Non-Zero Exit Codes**: Non-blocking error. The action continues, but the error message (from `stderr`) is displayed to the user.

### 4. What Environment Variables are Available

Hooks have access to the full system environment, plus specific variables set by Claude Code.

**Key Claude Code-Specific Variables:**
- **`CLAUDE_BASH_NO_LOGIN`**: Controls whether the `Bash` tool uses a login shell (`0` or `1`).
- **`CLAUDE_TOOL_NAME`**: The name of the tool being used (e.g., `Bash`, `Edit`).
- **`CLAUDE_TOOL_INPUT`**: The raw JSON input for the tool.
- **`CLAUDE_FILE_PATHS`**: A space-separated list of file paths affected by the tool (useful for `Edit` or `Write`).
- **`CLAUDE_EVENT_TYPE`**: The type of event that triggered the hook (e.g., `PreToolUse`).
- **`CLAUDE_NOTIFICATION`**: The notification message (for `Notification` hooks).

**Setting Custom Environment Variables:**
You can also set custom environment variables for all tool executions directly in your `settings.json` file using the `env` key.
```json
{
  "env": {
    "MY_PROJECT_ROOT": "/path/to/my/project",
    "LOG_LEVEL": "DEBUG"
  }
}
```
These variables will be available to your hook scripts.

### 5. How to Debug Hook Execution Issues

Debugging hooks requires a systematic approach. Here are the most effective methods:

- **Use the `/hooks` Command**: In an active Claude Code session, type `/hooks`. This will display a list of all loaded hooks from your configuration files, confirming that your `settings.json` is being parsed correctly and your hooks are registered.
- **Test Your Hook Command in Isolation**: Before trusting the hook to work within Claude Code, run the exact command string from your configuration in a terminal. If it's a script, make sure it has execute permissions (`chmod +x my-script.sh`).
- **Enable Debug Logging**: Start Claude Code with the `--debug` flag: `claude --debug`. This produces verbose output, including details about hook execution, input JSON, and any errors encountered. You can then inspect the log file, often located at `~/.claude/debug/latest`.
- **Add Logging to Your Hooks**: Temporarily modify your hook scripts to write debug information to a file. For example, you can redirect the stdin JSON to a file to see exactly what data Claude Code is sending to your hook.
    ```bash
    #!/usr/bin/env bash
    # At the top of your hook script
    cat > /tmp/hook_input.json
    # ... rest of your script
    ```
- **Verify File Structure and Permissions**:
    - **Settings Location**: Ensure your `settings.json` is in the correct location: `~/.claude/settings.json` for user-level, or `./.claude/settings.json` for project-level. Settings also have a precedence: `settings.local.json` (project) > `settings.json` (project) > `settings.json` (user).
    - **Script Permissions**: If your hook calls an external script, that script must be executable. Run `chmod +x .claude/hooks/my-hook.sh`.

By combining these techniques, you can effectively trace any hook issues from configuration loading to the final execution of your custom scripts.