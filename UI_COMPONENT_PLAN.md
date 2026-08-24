# Cisco Secure Access Connector — UI component plan

Источники: `Docs/session-notes/UI_COMPONENT_VOCABULARY.md`, `UI_INTERFACE_STANDARD.md`,
`concepts/panels.md`. Основано на функционале `cisco-secure-access-connector`
(см. `PREPARATION.md`).

**ВАЖНО (усвоено на Zscaler Connector — реальные ошибки DUI-валидатора при
деплое, не повторять):** `ui.Stack` НЕ принимает `width=` (только align/
children/className/direction/gap/justify/sticky/wrap). `ui.Stats` принимает
`children=[ui.Stat(...)]`, НЕ `stats=[...]` и НЕ `items=[dict]`. `ui.Alert`
принимает `type=`, НЕ `variant=`. `ui.Input`/`ui.Password`/`ui.Select` НЕ
принимают `label=` — использовать соседний `ui.Text(..., variant="caption")`
как визуальный лейбл внутри `ui.Stack(direction="v", gap=1, children=[Text, Input])`.

## 0. Разница с реализацией сейчас

Реализация начинается с нуля вместе с этим документом (первый заход) — план
строится ПЕРЕД `panels.py`, а не после, по правилу APP_PREPARATION_STANDARD.md
§9. Начальный `panels.py` реализует ровно §1 ниже, без отклонений, и уже
использует только валидированные kwargs (см. блок выше).

## 1. Компоненты

| Экран | Примитивы | Почему именно эти |
|---|---|---|
| Sidebar (left) | `ui.Stack`(direction="v") + `ui.Text`(org/network summary) + `ui.Divider` + navigation `ui.ListItem`(Umbrella / Meraki / Health) + `ui.Button`("App settings") | Без карточек по стандарту, как Zscaler/CircleCI/MuleSoft. |
| Connect: Umbrella section | `ui.Stack`(direction="v", gap=1, children=[`ui.Text`("Api Key", variant="caption"), `ui.Input`(param_name="api_key", placeholder="Umbrella API key from Admin > API Keys")]) + аналогично Password для api_secret + submit `ui.Button` | Каждый инпут с явным текстовым лейблом-соседом, контекстный placeholder. |
| Connect: Meraki section | `ui.Stack`(...) с `ui.Password`(param_name="meraki_api_key") + `ui.Input`(param_name="organization_id", placeholder="Опционально — авто-резолв первой организации") + submit `ui.Button` | Раздельная секция — Meraki и Umbrella не одна форма. |
| Empty (ни одна сторона не подключена) | `ui.Empty`(message="Подключите Umbrella/Secure Access или Meraki", icon="shield") | Стандартный первый экран. |
| Umbrella Overview (center, `center_overlay=True`) | `ui.Stack`(children=[`ui.Text`(heading), `ui.Stats`(children=[ui.Stat(...)x3]), `ui.Tabs`(Destination Lists / Policies / Identities / ZTNA Resources / Reporting)]) | `Stats` даёт мгновенный статус объёма конфигурации. |
| Destination Lists Table | `ui.DataTable`(columns=[name, type allow/block Badge, entry count]; sortable) + row actions Edit/Delete | Табличный список, привязанный к policies. |
| ZTNA Private Resources Table | `ui.DataTable`(columns=[name, address, protocol, policy assigned Badge]) | Аналог ZPA App Segments в Zscaler Connector — параллельная структура для консистентности портфеля. |
| Reporting | `ui.DataTable`(columns=[timestamp, identity, destination, action Badge]) + `ui.Stats`(top categories/identities counts) | Логи активности за ограниченное окно. |
| Meraki Overview (center, `center_overlay=True`) | `ui.Stack`(children=[`ui.Text`(heading), `ui.Stats`(children=[Networks/MX online/VPN tunnels]), `ui.Tabs`(Networks / Appliances / VPN Topology / Alerts)]) | Параллельная структура Umbrella-вкладке. |
| Networks Table | `ui.DataTable`(columns=[name, product types, tags]) + row actions | Список сетей в организации. |
| Appliance Health Table | `ui.DataTable`(columns=[serial/name, model, status Badge online/offline/alerting, uplink status]) | Здоровье MX-устройств. |
| Tenant Health (Ярус 3) | `ui.Stack`(children=[`ui.Stats`(unassigned lists/offline appliances/24h alerts), `ui.List`(находки с severity Badge)]) | Единый health-репорт по обеим сторонам. |
| App Settings | `ui.Stack`(children=[секция Umbrella disconnect, секция Meraki disconnect, About]) | Единая точка disconnect на каждую сторону отдельно, без дублирования в сайдбаре. |

## 2. Комбинаторные правила

- `ui.Tabs` переключает контент внутри одной center-панели без перезагрузки
  sidebar — избегает дублирования навигации.
- Umbrella и Meraki — раздельные top-level секции навигации (не табы одной
  вкладки), т.к. это независимые подключения с независимым состоянием
  "подключено/не подключено".
- `ui.Dialog` для редактирования отдельного объекта (Destination List/Network)
  — не отдельная навигационная страница, чтобы не терять контекст таблицы.
- Обе connect-формы — контейнер растянут на всю ширину сайдбара, поля
  растянуты внутри контейнера (аналогично Zscaler Connector's addendum).
- Инструкция "как получить API key" — только в help-модалке при кнопке рядом
  с каждой формой, не дублируется статическим текстом в сайдбаре.
