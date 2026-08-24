# Cisco Secure Access Connector — Preparation (Фаза 2.5, до кода)

**Дата:** 2026-08-24. Задача Vikunja #2533 ("максимальный функционал, полный
максимум" — заявленный объём релиза, повторный вопрос не требуется).

## 1. WHY BYOK

Cisco Secure Access/Umbrella и Meraki живут в облаке клиента (его собственная
организация) — Imperal не брокерит доступ централизованно, тот же принцип, что
Zscaler/MuleSoft/CircleCI Connector.

## 2. WHY две раздельные авторизации внутри одного коннектора

Cisco консолидирует Umbrella + Duo + Meraki под бренд "Cisco Secure Access", но
на уровне API это по-прежнему РАЗНЫЕ поверхности с разными механизмами:

- **Umbrella / Secure Access Reporting & Management API** — OAuth2
  client_credentials (`api.umbrella.com` / `api.sse.cisco.com`), управляет DNS/
  SIG-политиками, destination lists, ZTNA-доступом к приложениям.
- **Meraki Dashboard API** — статичный `X-Cisco-Meraki-API-Key` header
  (`api.meraki.com/api/v1`), управляет SD-WAN стороной (organizations,
  networks, uplinks, VPN topology, appliance).

Это ДВЕ независимые формы подключения внутри одного коннектора (как ZIA/ZPA
внутри Zscaler Connector) — общий продукт для клиента, разные учётные данные и
разные API-клиенты технически.

## 3. Scope (Ярус 1+2, максимум по заявленному объёму)

**Umbrella / Secure Access (SIG + ZTNA):**
- Destination Lists (list/create/update/delete) — блок/аллов-листы доменов.
- Policies (list/read) — привязка destination lists + identities.
- Identities: Networks, Roaming Computers, Virtual Appliances (list/read).
- ZTNA Private Resources (list/create/update/delete) — аналог ZPA App Segments.
- Reporting: Activity/DNS/Firewall/IPS logs (list, ограниченное окно), Top
  destinations/categories/identities summary.
- Deployments: Roaming Client status (list/read).

**Meraki (SD-WAN):**
- Organizations (list/read).
- Networks (list/create/update/delete).
- SD-WAN / Uplink status per network (list/read).
- Site-to-site VPN topology (list/read).
- Appliance (MX) health/status (list/read).
- Alerts/webhooks (list/create).

**Общее (Ярус 3, наши доп. функции):**
- `audit_secure_access` — health report: destination lists без назначенной
  policy, roaming computers offline, MX appliances с VPN down, alerts за
  последние 24ч.
- Bulk actions: `bulk_update_destination_lists`, `bulk_reboot_appliances`
  (Meraki поддерживает reboot по serial).

## 4. Данные аутентификации (форма connect)

Два раздельных Form-блока в одном connect-экране (как секции, не табы —
клиент может подключить только одну из двух сторон):

- **Umbrella / Secure Access:** `api_key` (client_id, Input) + `api_secret`
  (client_secret, Password) — OAuth2 client_credentials.
- **Meraki:** `meraki_api_key` (Password — Meraki сам называет это API key, но
  оно секретное) + опционально `organization_id` (Input, если известен
  заранее; иначе резолвится через `/organizations` после подключения).

## 5. Ограничения / что явно НЕ входит в этот заход

Duo (MFA/verified push) — отдельный продукт с отдельным API и моделью данных
(users/phones/factors, не сетевые политики) — не входит в этот заход. Cisco
Umbrella's DNS-layer resolver сам по себе (raw DNS query logs без Secure
Access framing) — уже покрыт через "Reporting" выше, отдельного раздела не
требует.

## 6. UI/Onboarding

См. `IDEAL_ONBOARDING.md` и `UI_COMPONENT_PLAN.md` — оба написаны ДО
`panels.py` по правилу APP_PREPARATION_STANDARD.md §9.
