import { chmod, mkdir, writeFile } from "node:fs/promises";
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

interface LiveSiteSnapshot {
  version: number;
  operation: string;
  source: string;
  passwordsAvailable: boolean;
  site: { id: string; name: string };
  lans: Array<{ id: string; name: string; vlan: number }>;
  wlanGroups: Array<{
    id: string;
    name: string;
    ssids: Array<{ id: string; name: string; password: string | null }>;
  }>;
}

function normalizeKey(value: string): string {
  return value.trim().toLowerCase();
}

function enrichSnapshotWithPlanPasswords(snapshot: LiveSiteSnapshot, site: OmadaSite): LiveSiteSnapshot {
  const passwordByGroupAndSsid = new Map<string, string>();
  const passwordBySsid = new Map<string, string>();

  for (const group of site.wlanGroups) {
    for (const ssid of group.ssids) {
      if (!ssid.password) {
        continue;
      }

      const groupKey = normalizeKey(group.name);
      const ssidKey = normalizeKey(ssid.name);
      passwordByGroupAndSsid.set(`${groupKey}::${ssidKey}`, ssid.password);
      if (!passwordBySsid.has(ssidKey)) {
        passwordBySsid.set(ssidKey, ssid.password);
      }
    }
  }

  let matchedPasswords = 0;
  const wlanGroups = snapshot.wlanGroups.map((group) => {
    const groupKey = normalizeKey(group.name);
    const ssids = group.ssids.map((ssid) => {
      const ssidKey = normalizeKey(ssid.name);
      const password = passwordByGroupAndSsid.get(`${groupKey}::${ssidKey}`) ?? passwordBySsid.get(ssidKey) ?? null;
      if (password) {
        matchedPasswords += 1;
      }
      return {
        ...ssid,
        password,
      };
    });

    return {
      ...group,
      ssids,
    };
  });

  return {
    ...snapshot,
    source: matchedPasswords > 0 ? "live_omada_plus_applied_plan" : snapshot.source,
    passwordsAvailable: matchedPasswords > 0,
    wlanGroups,
  };
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
  site: OmadaSite,
): Promise<void> {
  const snapshot = enrichSnapshotWithPlanPasswords(await portal.buildSiteSnapshot(site.name), site);
  const fileName = "live-site.yaml";
  const outputPath = resolve(reporter.outputDir, fileName);
  const yamlContent = stringifyYaml(snapshot);
  await writeFile(outputPath, yamlContent, "utf8");
  await chmod(outputPath, 0o644).catch(() => undefined);
  reporter.addArtifact("live-site-yaml", fileName, outputPath, {
    content: yamlContent,
    contentEncoding: "utf-8",
  });
  reporter.log("info", `Wrote live site snapshot "${fileName}".`);
}

export async function runPlanFromFile(planPath: string, forceDryRun = false): Promise<RunPlanResult> {
  ensureRuntimeDirs();

  const plan = await loadPlanFromPath(planPath);
  const dryRun = forceDryRun || plan.execution.dryRun;
  const reporter = new RunReporter(basename(planPath), dryRun);
  await mkdir(reporter.outputDir, { recursive: true });
  await chmod(reporter.outputDir, 0o755).catch(() => undefined);

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
          await writeLiveSiteArtifact(portal, reporter, site);
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
