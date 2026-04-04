import { mkdir, writeFile } from "node:fs/promises";
import { basename, resolve } from "node:path";
import { stringify as stringifyYaml } from "yaml";

import { loadPlanFromPath, summarizePlan } from "../config/load-plan";
import type { OmadaMutationMode, OmadaPlan, OmadaSite, OmadaSsid, OmadaWlanGroup } from "../config/schema";
import { OmadaPortal } from "../omada/portal";
import { withAuthenticatedSession } from "../omada/session";
import { ensureRuntimeDirs } from "./paths";
import { RunReporter, type RunReport } from "./report";

export interface RunPlanResult {
  plan: OmadaPlan;
  report: RunReport;
}

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "site";
}

async function withStep<T>(
  reporter: RunReporter,
  targetType: "organization" | "site" | "lan" | "wlanGroup" | "ssid",
  targetName: string,
  action: string,
  work: () => Promise<T>,
  onFailure?: () => Promise<string | undefined>,
): Promise<T> {
  try {
    const result = await work();
    reporter.recordStep(action, targetType, targetName, "success");
    return result;
  } catch (error) {
    const screenshotPath = onFailure ? await onFailure() : undefined;
    reporter.recordStep(action, targetType, targetName, "failed", String(error), screenshotPath);
    throw error;
  }
}

async function applySsid(
  portal: OmadaPortal,
  reporter: RunReporter,
  plan: OmadaPlan,
  site: OmadaSite,
  group: OmadaWlanGroup,
  ssid: OmadaSsid,
): Promise<void> {
  try {
    await withStep(
      reporter,
      "ssid",
      `${site.name}/${group.name}/${ssid.name}`,
      "applySsid",
      async () => {
        await portal.ensureSsidWithMode(group, ssid, resolveMutationMode(plan));
      },
    );
  } catch (error) {
    if (plan.execution.stopOnError) {
      throw error;
    }
    reporter.log("warning", `Continuing after SSID failure: ${String(error)}`);
  }
}

function resolveMutationMode(plan: OmadaPlan): OmadaMutationMode {
  return plan.execution.mutationMode ?? "ensure";
}

function resolveSsidWithSequentialVlan(site: OmadaSite, ssid: OmadaSsid, sequentialIndex: number): OmadaSsid {
  if (typeof ssid.vlanId === "number") {
    return ssid;
  }

  if (site.lans.length === 0) {
    return ssid;
  }

  const mappedLan = site.lans[sequentialIndex];
  if (!mappedLan) {
    throw new Error(`SSID "${ssid.name}" needs a VLAN mapping, but site "${site.name}" only defines ${site.lans.length} LANs for ${sequentialIndex + 1} SSIDs.`);
  }

  return {
    ...ssid,
    vlanId: mappedLan.vlanId,
  };
}

async function applySite(
  portal: OmadaPortal,
  reporter: RunReporter,
  plan: OmadaPlan,
  site: OmadaSite,
): Promise<void> {
  const mutationMode = resolveMutationMode(plan);
  await withStep(
    reporter,
    "site",
    site.name,
    "applySite",
    async () => {
      await portal.ensureSiteWithMode(site, mutationMode);
    },
  );

  if (site.lans.length === 0 && site.wlanGroups.length === 0) {
    return;
  }

  await withStep(
    reporter,
    "site",
    site.name,
    "openSite",
    async () => {
      await portal.openSite(site.name);
    },
  );

  for (const lan of site.lans) {
    try {
      await withStep(
        reporter,
        "lan",
        `${site.name}/${lan.name ?? lan.vlanId}`,
        "applyLan",
        async () => {
          await portal.ensureLanWithMode(lan, mutationMode);
        },
      );
    } catch (error) {
      if (plan.execution.stopOnError) {
        throw error;
      }
      reporter.log("warning", `Continuing after LAN failure: ${String(error)}`);
    }
  }

  let ssidSequence = 0;
  for (const group of site.wlanGroups) {
    try {
      await withStep(
        reporter,
        "wlanGroup",
        `${site.name}/${group.name}`,
        "applyWlanGroup",
        async () => {
          await portal.ensureWlanGroupWithMode(group, mutationMode);
        },
      );
    } catch (error) {
      if (plan.execution.stopOnError) {
        throw error;
      }
      reporter.log("warning", `Continuing after WLAN group failure: ${String(error)}`);
      continue;
    }

    for (const ssid of group.ssids) {
      const effectiveSsid = resolveSsidWithSequentialVlan(site, ssid, ssidSequence);
      await applySsid(portal, reporter, plan, site, group, effectiveSsid);
      ssidSequence += 1;
    }
  }
}

async function writeLiveSiteArtifact(
  portal: OmadaPortal,
  reporter: RunReporter,
  siteName: string,
): Promise<void> {
  const snapshot = await portal.buildSiteSnapshot(siteName);
  const fileName = `live-site-${slugify(siteName)}.yaml`;
  const outputPath = resolve(reporter.outputDir, fileName);
  await writeFile(outputPath, stringifyYaml(snapshot), "utf8");
  reporter.addArtifact("live-site-yaml", fileName, outputPath);
  reporter.log("info", `Wrote live site snapshot "${fileName}".`);
}

export async function runPlanFromFile(planPath: string, forceDryRun = false): Promise<RunPlanResult> {
  ensureRuntimeDirs();

  const plan = await loadPlanFromPath(planPath);
  const dryRun = forceDryRun || plan.execution.dryRun;
  const reporter = new RunReporter(basename(planPath), dryRun);
  await mkdir(reporter.outputDir, { recursive: true });

  reporter.log("info", `Loaded plan ${basename(planPath)}.`);
  reporter.log("info", `Plan summary: ${JSON.stringify(summarizePlan(plan))}`);

  if (dryRun) {
    reporter.log("success", "Dry run complete. No browser actions were executed.");
    return {
      plan,
      report: await reporter.finalize("success"),
    };
  }

  try {
    await withAuthenticatedSession(plan.controller, async ({ page }) => {
      const portal = new OmadaPortal(page, reporter, plan.controller);

      await withStep(
        reporter,
        "organization",
        plan.controller.organizationName,
        "selectOrganization",
        async () => {
          await portal.ensureOrganizationSelected(plan.controller.organizationName);
        },
        plan.execution.screenshots ? async () => reporter.capture(page, "organization-selection-failure") : undefined,
      );

      for (const site of plan.sites) {
        try {
          await applySite(portal, reporter, plan, site);
          await writeLiveSiteArtifact(portal, reporter, site.name);
        } catch (error) {
          reporter.log("error", `Site ${site.name} failed: ${String(error)}`);
          if (plan.execution.stopOnError) {
            throw error;
          }
        }
      }
    });

    return {
      plan,
      report: await reporter.finalize("success"),
    };
  } catch (error) {
    reporter.log("error", `Run failed: ${String(error)}`);
    return {
      plan,
      report: await reporter.finalize("failed"),
    };
  }
}
