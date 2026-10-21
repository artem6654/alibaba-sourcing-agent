# Alibaba Sourcing Agent для Claude Code

Агент для [Claude Code](https://claude.com/claude-code), который сам ищет фабрики на Alibaba, запрашивает цены EXW, торгуется в чате Alibaba и сводит результаты в Excel.

От вас нужны две вещи: назвать товар и один раз заполнить короткую анкету. Дальше агент работает сам и в конце присылает рекомендацию: победителя и двух запасных поставщиков.

[English below](#english)

## Что делает агент

1. **Бриф.** Присылает анкету по товару: характеристики, партии, сертификаты, упаковка, логотип, требования к фабрикам. Если в сессии есть интерактивные формы, анкета приходит формой: можно отметить несколько вариантов или вписать свой. Пустые пункты агент заполняет вариантами по умолчанию.
2. **Поиск фабрик.** Перебирает несколько поисковых запросов на Alibaba и убирает дубли. Каждую фабрику относит к одной из групп: подтверждённый производитель, заявленный производитель, торговая компания или не проверено. Затем ставит оценку от 0 до 100: надёжность — до 40 баллов, соответствие товару — до 35, цена и MOQ — до 25.
3. **Запрос цен.** Пишет каждой фабрике отдельное сообщение и просит лучшую цену EXW для каждой партии. Уточняет MOQ, цену и срок образца, срок производства, условия оплаты и срок действия цены.
4. **Переговоры.** Сравнивает только сопоставимые предложения: та же спецификация, та же партия, та же валюта, условия EXW. Опирается на реальные встречные цены и не называет конкурентов. Напоминает фабрикам, которые молчат, через 2, 3 и 4 дня.
5. **Итог.** Ведёт Excel-таблицу с листами «Сводка», «Поставщики», «Переговоры», «Котировки» и «Переписка». Когда переговоры заканчиваются, называет победителя и двух запасных поставщиков.

## Чего агент никогда не делает

- не платит, не оформляет заказы и заказы Trade Assurance, не принимает условия;
- не обещает фабрике заказ или сроки;
- не вводит пароли и не проходит CAPTCHA: в этих случаях он просит вас сделать это самому;
- не сообщает фабрикам ваш e-mail, телефон и полный адрес, только город и индекс, которые вы разрешили;
- не уходит из чата Alibaba в WhatsApp или почту и не переходит по ссылкам от поставщиков;
- не выполняет инструкции, которые встречаются в сообщениях поставщиков;
- не называет цену «финальной», пока фабрика сама это не подтвердит.

## Что нужно

- Claude Code: десктоп-приложение, CLI или IDE-расширение.
- Браузер, которым Claude может управлять: встроенный браузер десктоп-приложения или расширение [Claude in Chrome](https://claude.com/chrome).
- Аккаунт Alibaba.com, в который вы вошли в этом браузере.
- По желанию: навык `negotiation`. С ним агент применяет больше техник переговоров.

## Установка

### Вариант 1. Плагин (рекомендуется)

В Claude Code выполните:

```
/plugin marketplace add artem6654/alibaba-sourcing-agent
/plugin install alibaba-sourcing@alibaba-sourcing-agent
```

### Вариант 2. Вручную

```bash
git clone https://github.com/artem6654/alibaba-sourcing-agent.git
```

```bash
./alibaba-sourcing-agent/install.sh
```

Скрипт скопирует навык в `~/.claude/skills/alibaba-sourcing`. Если там уже была версия, он сначала сохранит её резервную копию.

Затем перезапустите Claude Code.

## Как пользоваться

1. Создайте пустую папку для проекта и откройте её в Claude Code.
2. Войдите в Alibaba в браузере, которым управляет Claude.
3. Напишите, например: `/alibaba-sourcing керамический обогреватель 1500 Вт`.
4. Заполните анкету. Если подходят варианты по умолчанию, ответьте «по умолчанию».
5. Дальше агент работает сам и проверяет новые ответы фабрик с той частотой, которую вы выбрали в анкете. Вас он отвлекает только при входе в аккаунт или CAPTCHA, при дедлайне от поставщика и для финального отчёта.

Таблица сохраняется в папке проекта.

## Важно

- Агент сообщает самую низкую сопоставимую цену, которую получил, и показывает, откуда она взялась. Он не обещает, что это минимальная цена на всём рынке.
- Сертификаты (CE, RoHS, Ecodesign и другие) агент подбирает для ориентира. Это не юридическая консультация.
- Перед заказом проверяйте поставщика, образец и документы сами.
- Агент отправляет сообщения от вашего имени, поэтому ответственность за переписку и решения лежит на вас.

## Лицензия

MIT

---

## English

An autonomous [Claude Code](https://claude.com/claude-code) skill for sourcing on Alibaba. You fill in one short brief. The agent then finds and qualifies manufacturers, requests comparable **EXW** quotes for every quantity tier and negotiates in Alibaba chat. It follows up with silent suppliers, logs everything to an Excel workbook and finishes with a recommended supplier plus two backups.

**Safety limits:** the agent never pays, places orders or accepts terms. It never enters passwords or solves CAPTCHAs. It never shares your e-mail, phone or full address, and it never leaves Alibaba chat. It treats supplier messages as untrusted data.

**Install (plugin):**

```
/plugin marketplace add artem6654/alibaba-sourcing-agent
/plugin install alibaba-sourcing@alibaba-sourcing-agent
```

**Install (manual):** clone the repo, run `./install.sh`, then restart Claude Code.

**Use:** open an empty project folder and sign in to Alibaba in a browser that Claude can control (the built-in browser or Claude in Chrome). Then run `/alibaba-sourcing <product>`. By default the agent talks to you in Russian; if you write in another language, it translates the brief. It always writes to suppliers in English.
