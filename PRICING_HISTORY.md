# Pricing History — Cisco Secure Access Connector

Обязательный журнал: каждое выставление или изменение цен на функции этого
приложения фиксируется здесь — что изменилось, почему, и на основании чего.
Не переписывать прошлые записи — только дописывать новые сверху.

---

## 2026-08-24 — первый прайсинг (per_action, по образцу MuleSoft/Zscaler Connector)

`developer.update_pricing` вызван ДО `submit_for_review` (канонический
`PRICING_POLICY.md` §1). Первая попытка вернула тот же класс ошибки, что и
на Zscaler/MuleSoft/GitLab CI/CD/PandaDoc: `model stored as 'free', expected
'per_action'` плюс список всех `tool_prices`, ни один из которых не
сохранился. Немедленный повтор с ТЕМ ЖЕ payload прошёл без ошибки.

**Модель:** `per_action`, `currency=tokens`, `monthly_price=0`,
`revenue_split_dev=95`.

**Fixed platform scale {0, 8, 16, 20, 40, 60}** — идентична шкале
Zscaler/MuleSoft Connector:
- `0` — connect_umbrella/connect_meraki/disconnect_cisco/list_connections
  (бесплатные, per policy)
- `8` — простые read-функции (list_*, get_*)
- `16` — write-операции (create/update/delete/reboot_appliance/create_alert_webhook)
- `40` — audit_secure_access (агрегированный отчёт Umbrella+Meraki)
- `60` — bulk_update_destination_lists / bulk_reboot_appliances (пакетные операции)

Задокументировано как продолжение того же класса системной ошибки первого
прохода `update_pricing`, отслеживаемой в task #2230 (BBW Imperal Apps).
