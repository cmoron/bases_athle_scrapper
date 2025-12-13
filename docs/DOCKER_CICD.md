# Docker CI/CD et Releases

Ce document décrit le processus automatisé de build, test et publication des images Docker du projet MyPacer Scraper.

## 📋 Table des matières

- [Architecture du CI/CD](#architecture-du-cicd)
- [Workflow Docker](#workflow-docker)
- [Créer une release](#créer-une-release)
- [Utiliser les images publiées](#utiliser-les-images-publiées)
- [Configuration GHCR](#configuration-ghcr)
- [Bonnes pratiques](#bonnes-pratiques)
- [Dépannage](#dépannage)

## Architecture du CI/CD

Le projet utilise GitHub Actions avec deux workflows principaux :

1. **`ci.yml`** : Tests, qualimétrie (Ruff, Black, MyPy) et SonarCloud
2. **`docker.yml`** : Build et publication des images Docker sur GHCR

### Déclencheurs

| Workflow | Déclenchement | Action |
|----------|---------------|--------|
| `ci.yml` | Push/PR vers `main` | Tests et analyse de code |
| `docker.yml` | Push vers `main` | Build et publication des images |
| `docker.yml` | Tag `v*` | Build, publication et création de release |
| `docker.yml` | Pull Request | Build uniquement (sans publication) |

## Workflow Docker

### Images buildées

Le workflow build **uniquement l'image de production** pour publication sur GHCR :

- **`prod`** : Image de production avec Supercronic pour le cron, publiée sur GHCR
- **`dev`** : Image de développement avec dépendances de test, **build local uniquement** via docker-compose

### Tags générés

Les images **de production uniquement** sont taggées automatiquement sur GHCR :

#### Sur push vers `main`
```
ghcr.io/cmoron/mypacer_scraper:main-prod
ghcr.io/cmoron/mypacer_scraper:latest-prod
ghcr.io/cmoron/mypacer_scraper:main-abc1234-prod   # SHA du commit
```

#### Sur tag `v1.2.3`
```
ghcr.io/cmoron/mypacer_scraper:1.2.3-prod
ghcr.io/cmoron/mypacer_scraper:1.2-prod
ghcr.io/cmoron/mypacer_scraper:1-prod
ghcr.io/cmoron/mypacer_scraper:latest-prod
```

> **Note** : L'image de développement n'est pas publiée sur GHCR. Elle est buildée localement via `docker-compose up --build`.

### Fonctionnalités avancées

- **Cache Docker** : Utilise GitHub Actions cache pour accélérer les builds
- **Build provenance** : Génère des attestations de build pour la sécurité
- **Multi-platform** : Build pour `linux/amd64` (extensible à ARM si nécessaire)

## Créer une release

### Processus de release

1. **Vérifier que `main` est stable**
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Créer un tag avec version sémantique**
   ```bash
   # Format: vMAJOR.MINOR.PATCH
   git tag -a v1.0.0 -m "Release version 1.0.0: Description des changements"
   ```

3. **Pousser le tag**
   ```bash
   git push origin v1.0.0
   ```

4. **Le workflow s'occupe du reste !**
   - Build des images `dev` et `prod`
   - Publication sur GHCR avec tous les tags
   - Génération du changelog
   - Création de la release GitHub
   - Ajout des instructions Docker dans la release

### Versioning sémantique

Suivre [Semantic Versioning 2.0.0](https://semver.org/) :

- **MAJOR** (`v2.0.0`) : Changements incompatibles
- **MINOR** (`v1.1.0`) : Nouvelles fonctionnalités rétrocompatibles
- **PATCH** (`v1.0.1`) : Corrections de bugs rétrocompatibles

### Exemples de messages de tag

```bash
# Release majeure
git tag -a v2.0.0 -m "Release v2.0.0: Refonte complète du scraper avec support PostgreSQL"

# Release mineure
git tag -a v1.1.0 -m "Release v1.1.0: Ajout du support Docker multi-stage"

# Patch
git tag -a v1.0.1 -m "Release v1.0.1: Correction du bug de parsing des dates"
```

## Utiliser les images publiées

### Production (GHCR)

```bash
# Dernière version stable
docker pull ghcr.io/cmoron/mypacer_scraper:latest-prod

# Version spécifique
docker pull ghcr.io/cmoron/mypacer_scraper:1.0.0-prod

# Lancer le container
docker run -d \
  --name mypacer-scraper \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/.env:/app/.env:ro \
  ghcr.io/cmoron/mypacer_scraper:latest-prod
```

**Déploiement avec docker-compose** : Créer un `docker-compose.prod.yml` :

```yaml
services:
  scraper:
    image: ghcr.io/cmoron/mypacer_scraper:latest-prod
    # ... reste de la configuration
```

### Développement (Local)

L'image de développement n'est **pas publiée sur GHCR**. Pour le développement local :

```bash
# Build et lancer avec docker-compose
docker-compose up --build

# Ou rebuild si nécessaire
docker-compose build --no-cache

# Accéder au container en mode interactif
docker-compose exec scraper bash
```

## Configuration GHCR

### Rendre le package public

Après le premier push, le package est privé par défaut :

1. Aller sur https://github.com/cmoron/mypacer_scraper/pkgs/container/mypacer_scraper
2. Cliquer sur **"Package settings"**
3. Dans la section **"Danger Zone"**, cliquer sur **"Change visibility"**
4. Sélectionner **"Public"**
5. Confirmer en tapant le nom du package

### S'authentifier localement

Pour pull les images privées localement :

```bash
# Créer un Personal Access Token (PAT) avec scope 'read:packages'
# https://github.com/settings/tokens

# Se connecter
echo $GITHUB_PAT | docker login ghcr.io -u USERNAME --password-stdin
```

### Permissions du workflow

Le workflow utilise `GITHUB_TOKEN` automatique avec ces permissions :

```yaml
permissions:
  contents: write   # Créer des releases
  packages: write   # Publier sur GHCR
  id-token: write   # Attestations de build
```

## Bonnes pratiques

### Avant de créer une release

✅ **Checklist**
- [ ] Tous les tests passent sur `main`
- [ ] SonarCloud quality gate passe
- [ ] Le changelog/commit messages sont clairs
- [ ] La version suit le semantic versioning
- [ ] Les breaking changes sont documentés

### Tags et branches

```bash
# ❌ Mauvais : tag sans annotation
git tag v1.0.0

# ✅ Bon : tag annoté avec message
git tag -a v1.0.0 -m "Release v1.0.0: Description"

# ❌ Mauvais : tag sur une branche de feature
git checkout feature/new-scraper
git tag v1.0.0

# ✅ Bon : tag uniquement sur main
git checkout main
git pull origin main
git tag -a v1.0.0 -m "Release v1.0.0"
```

### Gestion des erreurs de release

Si une release échoue ou contient une erreur :

```bash
# 1. Supprimer le tag local et distant
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0

# 2. Supprimer la release GitHub (si créée)
gh release delete v1.0.0

# 3. Corriger le problème dans main
git commit -m "fix: correction avant release"
git push origin main

# 4. Re-créer le tag
git tag -a v1.0.0 -m "Release v1.0.0: Description"
git push origin v1.0.0
```

### Images de développement vs Production

| Aspect | dev | prod |
|--------|-----|------|
| **Build** | Local (docker-compose) | CI/CD + GHCR |
| **Publication** | ❌ Non publiée | ✅ Publiée sur GHCR |
| **Taille** | ~600 MB | ~400 MB |
| **Dépendances** | requirements-dev.txt | requirements.txt |
| **Usage** | Tests, développement local | Déploiement production |
| **CMD** | `tail -f /dev/null` | `supercronic /app/crontab` |
| **Outils** | pytest, black, ruff, mypy | Scraper uniquement |

## Dépannage

### Le workflow Docker échoue

```bash
# Vérifier les logs du workflow
gh run list --workflow=docker.yml
gh run view <run-id> --log

# Tester le build localement
docker build --target prod -t test:latest .
docker build --target dev -t test:dev .
```

### L'image ne se publie pas sur GHCR

1. Vérifier que `GITHUB_TOKEN` a les bonnes permissions
2. Vérifier que le workflow a les permissions nécessaires
3. S'assurer que l'événement n'est pas un Pull Request (pas de push sur PR)

### La release n'est pas créée

1. Vérifier que le tag suit le format `v*` (ex: `v1.0.0`)
2. Vérifier que le tag est annoté : `git tag -a v1.0.0 -m "message"`
3. Vérifier les permissions `contents: write` dans le workflow

### Problèmes de cache

Si le cache GitHub Actions pose problème :

```bash
# Dans le workflow, ajouter ces paramètres au build
cache-from: type=gha
cache-to: type=gha,mode=max

# Ou désactiver temporairement le cache
# Commenter les lignes cache-from et cache-to
```

## Ressources

- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Docker Metadata Action](https://github.com/docker/metadata-action)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Semantic Versioning](https://semver.org/)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)

## Voir aussi

- [DOCKER_CRON.md](./DOCKER_CRON.md) - Configuration Docker et Cron
- [SETUP_SONARCLOUD.md](./SETUP_SONARCLOUD.md) - Configuration SonarCloud
- [REFACTORING.md](./REFACTORING.md) - Historique du refactoring
