import { z } from "zod";

export const dhcpSchema = z.object({
  enabled: z.boolean().default(true),
  start: z.string().min(1).optional(),
  end: z.string().min(1).optional(),
});

export const deviceAccountSchema = z.object({
  username: z.string().min(1).max(64),
  password: z.string().min(1).max(64),
});

export const cloudAccountSchema = z.object({
  email: z.string().email().max(320),
  password: z.string().min(1).max(256),
});

export const lanSchema = z.object({
  name: z.string().min(1).optional(),
  purpose: z.enum(["corporate", "guest", "voice", "management"]).default("corporate"),
  vlanId: z.number().int().min(1).max(4094),
  gateway: z.string().min(1).optional(),
  subnetMask: z.string().min(1).optional(),
  dhcp: dhcpSchema.optional(),
});

export const ssidSchema = z.object({
  name: z.string().min(1),
  security: z.enum(["wpa2_psk", "wpa3_sae", "open"]).default("wpa2_psk"),
  password: z.string().min(8).optional(),
  vlanId: z.number().int().min(1).max(4094).optional(),
  hideSsid: z.boolean().default(false),
});

export const wlanGroupSchema = z.object({
  name: z.string().min(1),
  ssids: z.array(ssidSchema).default([]),
});

export const siteSchema = z.object({
  name: z.string().min(1),
  region: z.string().min(1).optional(),
  timezone: z.string().min(1).optional(),
  scenario: z.string().min(1).optional(),
  deviceAccount: deviceAccountSchema.optional(),
  lans: z.array(lanSchema).default([]),
  wlanGroups: z.array(wlanGroupSchema).default([]),
});

export const controllerSchema = z.object({
  organizationName: z.string().min(1),
  baseUrl: z.string().url().default("https://use1-omada-cloud.tplinkcloud.com/"),
  browserChannel: z.enum(["msedge", "chrome", "chromium"]).default("msedge"),
  headless: z.boolean().default(false),
  cloudAccount: cloudAccountSchema.optional(),
  deviceAccount: deviceAccountSchema.optional(),
});

export const executionSchema = z.object({
  stopOnError: z.boolean().default(true),
  screenshots: z.boolean().default(true),
  dryRun: z.boolean().default(false),
});

export const planSchema = z.object({
  version: z.literal(1).default(1),
  controller: controllerSchema,
  execution: executionSchema.default({
    stopOnError: true,
    screenshots: true,
    dryRun: false,
  }),
  sites: z.array(siteSchema).min(1),
});

export type OmadaPlan = z.infer<typeof planSchema>;
export type OmadaSite = z.infer<typeof siteSchema>;
export type OmadaLan = z.infer<typeof lanSchema>;
export type OmadaWlanGroup = z.infer<typeof wlanGroupSchema>;
export type OmadaSsid = z.infer<typeof ssidSchema>;

export function formatValidationError(error: unknown): string {
  if (!(error instanceof z.ZodError)) {
    return String(error);
  }

  return error.issues
    .map((issue) => {
      const path = issue.path.length > 0 ? issue.path.join(".") : "root";
      return `${path}: ${issue.message}`;
    })
    .join("\n");
}
