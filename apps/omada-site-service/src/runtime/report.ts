import { writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import type { Page } from "playwright";

import { reportsDir } from "./paths";

export type StepStatus = "success" | "failed" | "skipped";
export type LogLevel = "info" | "warning" | "error" | "success";

export interface RunLogEntry {
  time: string;
  level: LogLevel;
  message: string;
}

export interface RunStep {
  time: string;
  action: string;
  targetType: "organization" | "site" | "lan" | "wlanGroup" | "ssid";
  targetName: string;
  status: StepStatus;
  detail?: string;
  screenshotPath?: string;
}

export interface RunArtifact {
  type: string;
  name: string;
  path: string;
}

export interface RunReport {
  runId: string;
  planFileName: string;
  startedAt: string;
  finishedAt?: string;
  overallStatus: "running" | "success" | "failed";
  dryRun: boolean;
  logs: RunLogEntry[];
  steps: RunStep[];
  artifacts: RunArtifact[];
  summary: {
    success: number;
    failed: number;
    skipped: number;
  };
}

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "artifact";
}

export class RunReporter {
  public readonly report: RunReport;
  public readonly outputDir: string;

  public constructor(planFileName: string, dryRun: boolean) {
    const runId = `${new Date().toISOString().replace(/[:.]/g, "-")}-${Math.random().toString(36).slice(2, 8)}`;

    this.outputDir = resolve(reportsDir, runId);
    this.report = {
      runId,
      planFileName,
      startedAt: new Date().toISOString(),
      overallStatus: "running",
      dryRun,
      logs: [],
      steps: [],
      artifacts: [],
      summary: {
        success: 0,
        failed: 0,
        skipped: 0,
      },
    };
  }

  public log(level: LogLevel, message: string): void {
    this.report.logs.push({
      time: new Date().toISOString(),
      level,
      message,
    });
  }

  public recordStep(
    action: string,
    targetType: RunStep["targetType"],
    targetName: string,
    status: StepStatus,
    detail?: string,
    screenshotPath?: string,
  ): void {
    const step: RunStep = {
      time: new Date().toISOString(),
      action,
      targetType,
      targetName,
      status,
    };

    if (detail !== undefined) {
      step.detail = detail;
    }

    if (screenshotPath !== undefined) {
      step.screenshotPath = screenshotPath;
    }

    this.report.steps.push(step);
    this.report.summary[status] += 1;
  }

  public async capture(page: Page, label: string): Promise<string> {
    const path = resolve(this.outputDir, `${slugify(label)}.png`);
    await page.screenshot({ path, fullPage: true });
    return path;
  }

  public addArtifact(type: string, name: string, path: string): void {
    this.report.artifacts.push({ type, name, path });
  }

  public async finalize(status: "success" | "failed"): Promise<RunReport> {
    this.report.overallStatus = status;
    this.report.finishedAt = new Date().toISOString();
    await writeFile(resolve(this.outputDir, "report.json"), JSON.stringify(this.report, null, 2), "utf8");
    return this.report;
  }
}
