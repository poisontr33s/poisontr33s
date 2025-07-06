# poisontr33s – Meta-Index & Portal

> SYSTEM STATUS: ROOT NODE INITIALIZED  
> AUTOMATION STATUS: REPOSITORY STRUCTURE FRAMEWORK ACTIVE

## Om
Dette arkivet fungerer som inngangsport og oversikt over det samlede landskapet. Her katalogiseres grunnstrukturer, verdensfrø og systemmutasjoner. Hver node og deres relasjon spores og loggføres.

**Ny funksjonalitet**: Automatisert repositoriestruktur med GitHub Copilot-drevet workflow for standardisering av prosjektorganisering.

## Strukturell Tektonikk
- Kunnskapsbase for alle modulariserte byggeblokker og omkodinger
- Meta-logg og harmoniseringspunkt for tilknyttede noder
- Inviterer til utvidelse, revisjon og fragmentering
- Sikrer kontinuitet og sammenheng mellom alle tilknyttede prosjekter
- **Automatisert repositoriestruktur** for konsistent prosjektorganisering

## 🏗️ Repository Structure Automation

### Oversikt
Dette systemet implementerer automatisert opprettelse av standardisert mappestruktur for GitHub-repositorier, med fokus på best practices og konsistens.

### 📁 Standardstruktur
```
📦 Repository
├── 📚 docs/           # Dokumentasjon og veiledninger
├── 🖼️ assets/         # Bilder og ressurser
├── 🔧 scripts/        # Automatiseringsskript
├── 💻 src/            # Kildekode
├── 🧪 tests/          # Testfiler
└── 📄 README.md       # Prosjektdokumentasjon
```

### 🚀 Bruk

#### Automatisk (GitHub Actions)
1. **Workflow trigger**: Kjører automatisk ved push til `main` eller manuelt via GitHub Actions
2. **Struktur-opprettelse**: Skaper mappestruktur hvis den ikke eksisterer
3. **Migrasjonsguide**: Flytter eksisterende `migration_guide.md` til `docs/` og oppretter mal hvis ingen eksisterer

#### Manuell kjøring
```bash
# Kjør setup-skript direkte
./scripts/setup-repo-structure.sh

# Eller test strukturen
./tests/validate-repo-structure.sh
```

### 📋 Komponenter

#### 🔧 Setup Script
- **Path**: `scripts/setup-repo-structure.sh`
- **Funksjon**: Oppretter mappestruktur og dokumentasjon
- **Idempotent**: Trygt å kjøre flere ganger

#### ⚙️ GitHub Actions Workflow  
- **Path**: `.github/workflows/repo-setup.yml`
- **Triggere**: Push til main, manuell kjøring
- **Funksjoner**: Automatisk struktur-setup, commit og push av endringer

#### 🧪 Validation Tests
- **Path**: `tests/validate-repo-structure.sh`
- **Funksjon**: Validerer at struktur-opprettelsen fungerer korrekt
- **Tester**: Mappeopprettelse, .gitkeep-filer, migrasjonsguide, idempotens

### 📚 Dokumentasjon
- **Migrasjonsguide**: `docs/migration_guide.md` - Omfattende mal for prosjekt-/systemmigrering
- **Mappestruktur**: Hver mappe inneholder `.gitkeep` med beskrivelse av formål og struktur

### 🔄 Gjenbruk i andre repositorier
1. Kopier `scripts/setup-repo-structure.sh` til nytt repo
2. Kopier `.github/workflows/repo-setup.yml` til nytt repo  
3. Kjør workflow eller script for å etablere struktur
4. Tilpass `docs/migration_guide.md` for spesifikt prosjekt

## Relasjoner
- [Konsept-node](https://github.com/poisontr33s/PsychoNoir-Kontrapunkt) - Utforskning av narrative strukturer og psykologiske dybder
- [Omstrukturerings-node](https://github.com/poisontr33s/Restructure-MCP-Orchestration) - Teknisk orkestrering og systemoptimalisering

## Meta-logg
Se `.github/copilot-session.md` for prosesslogg, valg og mutasjoner.

> Dette arkivet er et faresignal for det statiske.
