# ModelDock GPU Finder – n8n workflow

Demonstracyjny workflow n8n połączony z API ModelDock.

## Co robi workflow

1. Wyświetla formularz z minimalną pamięcią VRAM i maksymalną ceną.
2. Pobiera aktualny katalog GPU z API ModelDock.
3. Filtruje oferty według wymagań użytkownika.
4. Sortuje wyniki według ceny.
5. Wyświetla najlepszą znalezioną kartę GPU.

## Przepływ

Formularz n8n → API ModelDock → filtrowanie JavaScript → ekran wyniku

## Wymagania

- n8n 2.x
- działający backend ModelDock
- endpoint `/cloud-gpus`
- połączenie sieciowe pomiędzy n8n i backendem

## Import

W n8n wybierz:

`Workflows → Import from File`

Następnie wskaż plik:

`modeldock-gpu-finder.json`

## Konfiguracja API

Workflow używa obecnie adresu:

`http://172.17.0.1:8000/cloud-gpus`

Po imporcie na inny serwer należy zmienić adres w nodzie `HTTP Request`.

## Bezpieczeństwo

Plik nie zawiera kluczy API, haseł ani danych uwierzytelniających.
