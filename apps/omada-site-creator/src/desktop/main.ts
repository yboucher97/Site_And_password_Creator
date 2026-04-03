import { app, BrowserWindow, shell } from "electron";
import type { Server } from "node:http";
import { resolve } from "node:path";

import type { StartedServer } from "../server/app";

let mainWindow: BrowserWindow | null = null;
let startedServer: StartedServer | null = null;
let closingServer = false;

async function ensureServer(): Promise<StartedServer> {
  if (startedServer) {
    return startedServer;
  }

  process.env.OMADA_SITE_CREATOR_APP_ROOT = app.getAppPath();
  process.env.OMADA_SITE_CREATOR_DATA_DIR = resolve(app.getPath("userData"), "data");
  process.env.PORT = process.env.OMADA_SITE_CREATOR_PORT ?? process.env.PORT ?? "3210";

  const { startServer } = await import("../server/app.js");
  const server = await startServer({ port: Number(process.env.PORT), host: "127.0.0.1" });
  startedServer = server;
  return server;
}

async function createMainWindow(): Promise<void> {
  const server = await ensureServer();

  mainWindow = new BrowserWindow({
    width: 1240,
    height: 900,
    minWidth: 980,
    minHeight: 720,
    autoHideMenuBar: true,
    backgroundColor: "#f6f3eb",
    title: "Omada Site Creator",
    webPreferences: {
      contextIsolation: true,
      sandbox: false,
    },
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    void shell.openExternal(url);
    return { action: "deny" };
  });

  await mainWindow.loadURL(server.url);

  mainWindow.on("closed", () => {
    mainWindow = null;
  });

  const autoQuitMs = Number(process.env.OMADA_SITE_CREATOR_AUTO_QUIT_MS ?? 0);
  if (autoQuitMs > 0) {
    setTimeout(() => {
      app.quit();
    }, autoQuitMs);
  }
}

async function closeServer(server: Server): Promise<void> {
  await new Promise<void>((resolveClose, rejectClose) => {
    server.close((error) => {
      if (error) {
        rejectClose(error);
        return;
      }
      resolveClose();
    });
  });
}

app.whenReady().then(async () => {
  await createMainWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      void createMainWindow();
    }
  });
}).catch((error) => {
  console.error("Failed to start desktop app.", error);
  app.exit(1);
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", (event) => {
  if (!startedServer || closingServer) {
    return;
  }

  closingServer = true;
  event.preventDefault();

  void closeServer(startedServer.server)
    .catch((error) => {
      console.error("Failed to close local server cleanly.", error);
    })
    .finally(() => {
      startedServer = null;
      app.quit();
    });
});
