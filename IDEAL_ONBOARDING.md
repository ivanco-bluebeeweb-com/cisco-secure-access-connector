# Cisco Secure Access Connector — идеальный первый запуск

Источник: `ONBOARDING_FIRST_LAUNCH_STANDARD.md`. Целевой пользователь: network/
security admin, управляющий Cisco Umbrella/Secure Access (DNS/SIG/ZTNA
политиками) и/или Meraki SD-WAN инфраструктурой.

## 1. Credential type

Две независимые пары credentials, ни одна не обязательна для другой:

- **Umbrella / Secure Access:** `api_key` + `api_secret` (OAuth2
  client_credentials, из Umbrella dashboard → Admin → API Keys → Umbrella
  Reporting/Management).
- **Meraki:** `meraki_api_key` (из Meraki Dashboard → My profile → API access)
  + опциональный `organization_id`.

## 2. Идеальный флоу

1. **Первое открытие** — `Empty` с двумя равнозначными путями: "Подключить
   Umbrella / Secure Access" и "Подключить Meraki" — не последовательный
   визард, а два независимых входа, т.к. клиент может использовать только
   одну из сторон Cisco Secure Access.
2. **Форма Umbrella** — `api_key` + `api_secret` (password). Подсказка (в
   help-модалке, не в сайдбаре): где именно в Umbrella dashboard создаётся
   API key с нужным скоупом (Reporting vs Management — Cisco разделяет их).
3. **Форма Meraki** — `meraki_api_key` (password) + опциональный
   `organization_id` (если пусто — после подключения резолвится первая
   доступная организация, и коннектор явно показывает, какую выбрал).
4. **После успеха (Umbrella)** — сводка: сколько destination lists, policies,
   идентичностей (networks/roaming computers) видно этому ключу.
5. **После успеха (Meraki)** — сводка: сколько networks в организации, сколько
   MX appliances online/offline.
6. **Частичное подключение** — если подключена только одна сторона (например
   только Meraki), вкладка другой стороны показывает `Empty` с точным
   объяснением "Umbrella/Secure Access не подключен" и кнопкой подключения —
   не пустой список без причины.
7. **Ошибка неверного ключа** — Cisco возвращает конкретный 401/403; коннектор
   обязан прокинуть текст ошибки, а не заменять generic "connection failed".

## 3. Разница с реализацией сейчас

См. `UI_COMPONENT_PLAN.md` §0.
