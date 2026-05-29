# Ha-opower

Custom Home Assistant `opower` integration based on Home Assistant Core, updated to support utility MFA login flows (including Portland General Electric) while preserving the same device and sensor model as the core integration.

## Installation

1. Copy `custom_components/opower` into your Home Assistant config directory.
2. Restart Home Assistant.
3. Add **Opower** from **Settings → Devices & Services → Add Integration**.
4. Select your utility (for example, **Portland General Electric**), enter credentials, and complete MFA when prompted.

## What this integration provides

- The same `opower` config flow pattern used by Home Assistant Core.
- MFA challenge handling (`mfa_options` + `mfa_code`) for utilities that require it.
- The same `opower` sensor/statistics behavior expected from the Home Assistant Core integration.
