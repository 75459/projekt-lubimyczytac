  _  __ _____ _____ ______ _____          _____  _   _ _____          
 | |/ // ____|_   _|  ____/ ____|   /\   |  __ \| \ | |_   _|   /\    
 | ' /| (___   | | | |__ | |  __   /  \  | |__) |  \| | | |    /  \   
 |  <  \___ \  | | |  __|| | |_ | / /\ \ |  _  /| . ` | | |   / /\ \  
 | . \ ____) |_| |_| |___| |__| |/ ____ \| | \ \| |\  |_| |_ / ____ \ 
 |_|\_\_____/|_____|______\_____/_/    \_\_|  \_\_| \_|_____/_/    \_\
                                                                      
                                                                      


💻 O Projekcie
Nowoczesna, w pełni responsywna aplikacja webowa dedykowana do kompleksowego zarządzania zasobami bibliotecznymi oraz interakcjami zalogowanych czytelników. System realizuje pełen cykl zarządzania pozycjami książkowymi, dynamiczne wyszukiwanie w czasie rzeczywistym oraz spersonalizowany moduł asynchronicznych zakładek dla przeczytanych książek.

🚀 Stos Technologiczny (Tech Stack)
⚙️ Backend
Python 3.14.5 – Rdzeń aplikacji oraz logika biznesowa, wykorzystujący najnowsze optymalizacje wydajnościowe interpretera.

Flask Microframework – Architektura routingu MVC, bezpieczna kontrola sesji użytkowników oraz walidacja danych wejściowych po stronie serwera.

Rate Limiting (Dekoratory) – Natywna implementacja limitowania żądań zabezpieczająca punkty końcowe przed atakami typu DDoS / Brute Force.

🗄️ Baza Danych
PostgreSQL – Relacyjna baza danych zapewniająca pełną zgodność z zasadami transakcyjności (ACID) oraz integralność referencyjną.

SQLAlchemy (ORM) – Warstwa mapowania obiektowo-relacyjnego. Zapytania kompilowane są za pomocą bezpiecznych metod obiektowych, eliminując podatności typu SQL Injection.

Trzecia Postać Normalna (3NF) – Struktura tabel zaprojektowana zgodnie z regułami normalizacji. Relacja użytkownik ↔ przeczytana książka zaimplementowana została poprzez tabelę asocjacyjną (łączącą) obsługującą relację Wiele-do-Wielu (Many-to-Many), odrzucając antywzorce typu ciągi tekstowe rozdzielane przecinkami.

🎨 Frontend
HTML5 & Jinja2 Templates – Bezpieczne renderowanie widoków po stronie serwera z rygorystycznym podziałem na role użytkowników (ukrywanie paneli administratora na poziomie kodu serwera).

Tailwind CSS (CDN) – Framework utility-first. Stylizowanie bezpośrednio w klasach HTML pozwoliło na całkowite wyeliminowanie tradycyjnych zewnętrznych plików .css oraz optymalizację czasu renderowania drzewa DOM.

Asynchroniczny Vanilla JavaScript (ES6+) – Wykorzystanie natywnego Fetch API do asynchronicznej komunikacji z backendem. Pozwala na dynamiczną zmianę stanu bazy (dodawanie/usuwanie zakładek) oraz odświeżanie komponentów interfejsu bez konieczności przeładowywania całej strony (Single Page Interactivity).

🔒 Bezpieczeństwo i Architektura Kodu
Izolacja Środowiskowa (.env): Wszystkie dane wrażliwe (klucze kryptograficzne SECRET_KEY, parametry połączenia bazy DATABASE_URL) zostały odseparowane od kodu źródłowego.

Ochrona Repozytorium (.gitignore): Lokalny plik .env został trwale wykluczony ze śledzenia w systemie Git za pomocą reguł .gitignore. Zapobiega to przypadkowemu wyciekowi danych dostępowych do publicznych repozytoriów.

Kryptografia Haseł: System nie przechowuje haseł w formie jawnej. Dane przed zapisaniem w strukturach PostgreSQL podlegają jednostronnemu haszowaniu kryptograficznemu (PBKDF2/bcrypt).

Autoryzacja Żądań: Stan uwierzytelnienia sprawdzany jest bezwzględnie na backendzie. Próba dodania pozycji do przeczytanych przez anonimowego użytkownika wywołuje asynchroniczny modal (overlay) blokujący akcję z żądaniem logowania.


Jakub Kowalczyk
Index: 75459
Afib Vistula


       _       _          _       _  __                  _                _    
      | |     | |        | |     | |/ /                 | |              | |   
      | | __ _| | ___   _| |__   | ' / _____      ____ _| | ___ _____   _| | __
  _   | |/ _` | |/ / | | | '_ \  |  < / _ \ \ /\ / / _` | |/ __|_  / | | | |/ /
 | |__| | (_| |   <| |_| | |_) | | . \ (_) \ V  V / (_| | | (__ / /| |_| |   < 
  \____/ \__,_|_|\_\\__,_|_.__/  |_|\_\___/ \_/\_/ \__,_|_|\___/___|\__, |_|\_\
                                                                     __/ |     
                                                                    |___/      

  _____           _             ______ _____ _  _   _____ ___  
 |_   _|         | |           |____  | ____| || | | ____/ _ \ 
   | |  _ __   __| | _____  __     / /| |__ | || |_| |__| (_) |
   | | | '_ \ / _` |/ _ \ \/ /    / / |___ \|__   _|___ \\__, |
  _| |_| | | | (_| |  __/>  <    / /   ___) |  | |  ___) | / / 
 |_____|_| |_|\__,_|\___/_/\_\  /_/   |____/   |_| |____/ /_/  
                                                               
                                                                