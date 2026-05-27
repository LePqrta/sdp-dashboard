const { execFileSync } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const rootDir = path.resolve(__dirname, "..");
const pidDir = path.join(rootDir, ".dashboard-pids");
const ports = [3000, 8000];

function log(message) {
  console.log(message);
}

function commandOutput(command, args) {
  try {
    return execFileSync(command, args, {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
    });
  } catch {
    return "";
  }
}

function windowsProcesses() {
  if (process.platform !== "win32") {
    return [];
  }

  const output = commandOutput("powershell.exe", [
    "-NoProfile",
    "-Command",
    "Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,CommandLine | ConvertTo-Json -Compress",
  ]);
  if (!output.trim()) {
    return [];
  }

  try {
    const parsed = JSON.parse(output);
    return Array.isArray(parsed) ? parsed : [parsed];
  } catch {
    return [];
  }
}

function windowsRelatedPids(pid) {
  return windowsProcesses()
    .filter((item) => {
      const commandLine = String(item.CommandLine || "");
      return (
        Number(item.ParentProcessId) === pid ||
        commandLine.includes(`parent_pid=${pid}`) ||
        commandLine.includes(`parent_pid=${pid},`)
      );
    })
    .map((item) => Number(item.ProcessId))
    .filter((processId) => Number.isInteger(processId) && processId > 0);
}

function isRunning(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

function stopPid(pid, reason) {
  if (!Number.isInteger(pid) || pid <= 0) {
    return false;
  }
  if (process.platform === "win32") {
    log(`Stopping PID ${pid} (${reason})`);
    commandOutput("taskkill", ["/PID", String(pid), "/T", "/F"]);
    return true;
  }

  if (!isRunning(pid)) {
    log(`Already stopped: PID ${pid} (${reason})`);
    return false;
  }

  log(`Stopping PID ${pid} (${reason})`);
  try {
    process.kill(pid, "SIGTERM");
  } catch {}
  return true;
}

function readTrackedPids() {
  if (!fs.existsSync(pidDir)) {
    return [];
  }

  return fs
    .readdirSync(pidDir)
    .filter((name) => name.endsWith(".pid"))
    .flatMap((name) => {
      const raw = fs.readFileSync(path.join(pidDir, name), "utf8").trim();
      const pid = Number(raw);
      return Number.isInteger(pid) ? [{ pid, name }] : [];
    });
}

function pidsForPort(port) {
  if (process.platform === "win32") {
    const output = commandOutput("netstat", ["-ano", "-p", "tcp"]);
    const pids = new Set();
    for (const line of output.split(/\r?\n/)) {
      const parts = line.trim().split(/\s+/);
      if (parts.length < 5 || !/^TCP$/i.test(parts[0]) || !/\bLISTENING\b/i.test(line)) {
        continue;
      }
      const localAddress = parts[1];
      if (!localAddress.endsWith(`:${port}`)) {
        continue;
      }
      const pid = Number(parts[parts.length - 1]);
      if (Number.isInteger(pid)) {
        pids.add(pid);
        for (const relatedPid of windowsRelatedPids(pid)) {
          pids.add(relatedPid);
        }
      }
    }
    return [...pids];
  }

  const output = commandOutput("lsof", ["-ti", `tcp:${port}`]);
  return output
    .split(/\r?\n/)
    .map((line) => Number(line.trim()))
    .filter((pid) => Number.isInteger(pid));
}

function cleanupPidFiles() {
  if (fs.existsSync(pidDir)) {
    fs.rmSync(pidDir, { recursive: true, force: true });
  }
}

log("Stopping local churn dashboard services...");

for (const { pid, name } of readTrackedPids()) {
  stopPid(pid, `tracked ${name}`);
}

for (const port of ports) {
  const pids = pidsForPort(port);
  if (!pids.length) {
    log(`No process is listening on port ${port}.`);
    continue;
  }

  for (const pid of pids) {
    stopPid(pid, `port ${port}`);
  }
}

cleanupPidFiles();
log("Stop complete.");
