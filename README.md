# Project Prima

Неофициальная русская локализация Final Fantasy XIV. Перевод показывается в игре
плагином [Harmonia](https://github.com/AngelicaProject/Harmonia) для Dalamud;
проект создается и поддерживается в [Aeria](https://github.com/AngelicaProject/Aeria).

Project Prima, Harmonia и Aeria находятся на ранних стадиях разработки и могут содержать ошибки.

`https://angelicaproject.github.io/ProjectPrima/harmonia/feed-v1.json`

## Установка

1. Установите [XIVLauncher](https://goatcorp.github.io/) с Dalamud.
2. В Dalamud: Settings → Experimental → Custom Plugin Repositories добавьте
   `https://raw.githubusercontent.com/AngelicaProject/Harmonia/main/repo.json`
   и установите плагин Harmonia.
3. В Harmonia добавьте перевод по ссылке:
   `https://angelicaproject.github.io/ProjectPrima/harmonia/feed-v1.json`
4. Установите [Penumbra](https://github.com/xivdev/Penumbra). В Dalamud: Settings → Experimental → Custom Plugin Repositories добавьте
   `https://raw.githubusercontent.com/xivdev/Penumbra/master/repo.json`
   и установите плагин Penumbra.
4. Включите перевод и перезапустите игру.

Для корректного отображения кириллицы требуется [Penumbra](https://github.com/xivdev/Penumbra).

## Состав репозитория

| Путь | Что это |
| --- | --- |
| `po/` | текст игры и его перевод: по PO-файлу на лист игры |
| `aeria-knowledge/style.md` | решения по стилю: обращение, имена, интерфейс |
| `aeria-knowledge/terms.csv` | термины проекта и запрещённые варианты |
| `aeria.json` | языки проекта и версия игры |
| `aeria-pack.json`, `aeria-fonts.json`, `fonts/` | настройки пакета и шрифты для букв, которых нет в игре |

## Участие

[Discord](https://discord.gg/B9T9qVhcxh) развития и поддержки проекта

Проект открыт и нуждается в людях для вычитки и правок.

Краткая информация по вкладу - [CONTRIBUTING.md](CONTRIBUTING.md).

## Лицензия

Переводы и материалы проекта распространяются по лицензии
[CC BY-NC-SA 4.0](LICENSE). Текст игры принадлежит Square Enix и под эту
лицензию не входит; шрифты в `fonts/` распространяются по лицензиям их
авторов.

FINAL FANTASY is a registered trademark of Square Enix Holdings Co., Ltd.
FINAL FANTASY XIV © SQUARE ENIX.
