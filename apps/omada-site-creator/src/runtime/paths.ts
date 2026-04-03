import { mkdirSync } from "node:fs";
import { resolve } from "node:path";

const envProjectRoot = process.env.OMADA_SITE_CREATOR_APP_ROOT;
const envDataDir = process.env.OMADA_SITE_CREATOR_DATA_DIR;

export const projectRoot = envProjectRoot ? resolve(envProjectRoot) : resolve(__dirname, "..", "..");
export const dataDir = envDataDir ? resolve(envDataDir) : resolve(projectRoot, "data");
export const uploadsDir = resolve(dataDir, "uploads");
export const reportsDir = resolve(dataDir, "reports");
export const browserProfileDir = resolve(dataDir, "browser-profile");
export const publicDir = resolve(projectRoot, "public");
export const examplesDir = resolve(projectRoot, "examples");

export function ensureRuntimeDirs(): void {
  for (const dir of [dataDir, uploadsDir, reportsDir, browserProfileDir]) {
    mkdirSync(dir, { recursive: true });
  }
}
