# SpectraCam-AIO - Przewodnik dla Początkujących

Witaj w SpectraCam-AIO! Ten plik pomoże Ci zrozumieć, czym jest ta aplikacja i jak z niej korzystać, nawet jeśli nie jesteś programistą.

## Co to jest SpectraCam-AIO?

SpectraCam-AIO to Twoje prywatne centrum do **zbierania i analizowania publicznie dostępnych informacji** o modelkach i osobach publicznych w internecie. Jest to narzędzie typu OSINT (biały wywiad), które pozwala na:
- **Wyszukiwanie profili** w Twojej prywatnej bazie danych oraz w internecie.
- **Automatyczne pobieranie (scrapowanie)** danych z profili na stronach takich jak OnlyFans, Fansly, Twitch, YouTube, Telegram itp.
- **Zarządzanie listą serwerów proxy**, aby chronić swoją prywatność.
- **Korzystanie z sieci Tor** do anonimowego przeglądania Telegrama.

Wszystko to z poziomu wygodnego interfejsu w przeglądarce internetowej.

## Pierwsze Uruchomienie i Instalacja

Zanim zaczniesz, upewnij się, że masz zainstalowane dwa darmowe programy:
1.  **Python** (wersja 3.8 lub nowsza) - [Pobierz tutaj](https://www.python.org/downloads/) (podczas instalacji zaznacz opcję "Add Python to PATH").
2.  **Node.js** (wersja 16 lub nowsza) - [Pobierz tutaj](https://nodejs.org/) (instalator sam skonfiguruje wszystko, co potrzebne).

Gdy masz już oba programy, wykonaj poniższe kroki:

1.  **Uruchom PowerShell**: Otwórz menu Start i wpisz "PowerShell", a następnie uruchom aplikację.
2.  **Przejdź do folderu projektu**: W oknie PowerShell wpisz `cd C:\SpectraCam-AIO` i naciśnij Enter.
3.  **Uruchom skrypt instalacyjny**: Wpisz `.\SpectraCam-AIO.ps1` i naciśnij Enter.

Skrypt automatycznie przygotuje całe środowisko, zainstaluje wszystkie potrzebne zależności zarówno dla backendu (silnika aplikacji), jak i frontendu (interfejsu użytkownika). **Ten krok wykonujesz tylko raz!**

## Jak Uruchomić Aplikację?

Aby uruchomić aplikację, musisz otworzyć **dwa okna PowerShell** w folderze `C:\SpectraCam-AIO`.

**Okno 1: Uruchomienie Backendu (Silnika)**
1.  W pierwszym oknie PowerShell wpisz `.\run_spectracam.ps1` i naciśnij Enter.
2.  Pojawi się nowe okno, w którym będzie pracował silnik aplikacji. **Nie zamykaj tego okna!** Możesz je zminimalizować.

**Okno 2: Uruchomienie Frontendu (Interfejsu Użytkownika)**
1.  W drugim oknie PowerShell przejdź do katalogu `frontend`, wpisując `cd frontend`.
2.  Następnie uruchom interfejs, wpisując `npm start`.
3.  Po chwili w Twojej domyślnej przeglądarce internetowej automatycznie otworzy się strona z interfejsem aplikacji (domyślnie `http://localhost:3000`).

Gratulacje! Aplikacja jest gotowa do pracy.

## Jak Korzystać z Aplikacji?

Interfejs aplikacji jest podzielony na kilka sekcji, dostępnych z górnego paska nawigacji.

### Strona Główna (Home)
-   Znajdziesz tu **Szybkie Linki** do najpopularniejszych stron. Możesz je kliknąć, aby szybko otworzyć daną witrynę w nowej karcie.

### Profile
-   Wyświetla listę wszystkich profili, które zostały już przez Ciebie zebrane i zapisane w lokalnej bazie danych.
-   Możesz przeszukiwać swoją bazę, wpisując frazę w polu wyszukiwania.

### Web Search
-   Twoje centrum dowodzenia. Wpisz zapytanie (np. nazwisko modelki), a aplikacja przeszuka zarówno Twoją lokalną bazę, jak i internet (za pomocą Google).
-   Wyniki z internetu pojawią się jako lista linków. Obok każdego linku znajdziesz przycisk **"+" (Scrapuj)**, który pozwoli Ci automatycznie pobrać dane z tego linku i zapisać je w swojej bazie.

### Scrape
-   Jeśli masz bezpośredni link do profilu, który chcesz dodać do bazy, możesz go tutaj wkleić i kliknąć "Start Scrape".

### Tor Control
-   Tutaj możesz zarządzać swoim połączeniem z siecią Tor dla zapytań do Telegrama.
    -   **Use Tor for Telegram**: Włącza lub wyłącza używanie Tora. Aby to działało, musisz mieć uruchomionego np. Tor Browser w tle.
    -   **Request New Tor Identity**: Jeśli chcesz zmienić swój adres IP w sieci Tor, kliknij ten przycisk.

### Proxies
-   Pozwala na zarządzanie listą Twoich serwerów proxy. Możesz dodawać nowe, usuwać stare i testować ich działanie.

## Konfiguracja Telegrama (Ważne!)

Aby móc przeszukiwać i pobierać dane z Telegrama, musisz podać swoje klucze API. Jest to darmowe i jednorazowe.

1.  Wejdź na stronę [my.telegram.org](https://my.telegram.org/auth) i zaloguj się na swoje konto Telegram.
2.  Przejdź do sekcji "API development tools".
3.  Wypełnij krótki formularz (nazwa aplikacji i krótka nazwa mogą być dowolne, np. "SpectraCam").
4.  Po utworzeniu aplikacji otrzymasz `api_id` i `api_hash`.
5.  Otwórz plik `C:\SpectraCam-AIO\backend\config.ini` w Notatniku.
6.  Wklej swoje klucze w odpowiednie miejsca, zastępując `YOUR_API_ID` i `YOUR_API_HASH`.
    ```ini
    [telegram]
    api_id = 12345678  ; Twój api_id
    api_hash = twojdlugihashodtelegrama1234567890
    ```
7.  Zapisz plik. Teraz aplikacja będzie mogła korzystać z API Telegrama.

Mam nadzieję, że ten przewodnik będzie pomocny. Miłego korzystania z aplikacji!
