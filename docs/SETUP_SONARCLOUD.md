# Configuration de SonarCloud

Ce guide explique comment configurer SonarCloud pour obtenir une analyse de qualité de code et de couverture de tests pour votre projet.

## Qu'est-ce que SonarCloud ?

**SonarCloud** est la version cloud de SonarQube, gratuite pour les projets open source. Elle fournit :
- 📊 **Quality Gate** : Note globale (Passed/Failed) basée sur des seuils
- 🐛 **Bugs** : Détection de bugs potentiels
- 🔐 **Vulnerabilités** : Détection de failles de sécurité
- 👃 **Code Smells** : Problèmes de maintenabilité
- 📈 **Coverage** : Pourcentage de couverture de tests
- 🔄 **Duplication** : Détection de code dupliqué
- 📉 **Technical Debt** : Dette technique estimée

## Prérequis

- Un compte GitHub avec le repository `cmoron/bases_athle_scrapper`
- Accès administrateur au repository
- Le fichier `sonar-project.properties` déjà configuré ✅

## Étape 1 : Créer un compte SonarCloud

1. Rendez-vous sur [https://sonarcloud.io](https://sonarcloud.io)
2. Cliquez sur **"Log in"** puis **"Sign up with GitHub"**
3. Autorisez SonarCloud à accéder à votre compte GitHub
4. Choisissez **"Free plan"** pour les projets open source

## Étape 2 : Créer une organisation

Si c'est votre première utilisation de SonarCloud :

1. Cliquez sur **"+"** (en haut à droite) > **"Create new organization"**
2. Sélectionnez votre compte GitHub : `cmoron`
3. Choisissez le plan **"Free plan"** (pour open source)
4. Donnez un nom à votre organisation (suggestion : `cmoron`)
5. Cliquez sur **"Continue"**

## Étape 3 : Ajouter votre repository

1. Une fois l'organisation créée, cliquez sur **"Analyze new project"**
2. Sélectionnez le repository **`bases_athle_scrapper`**
3. Cliquez sur **"Set Up"**

### Configuration du projet

SonarCloud va détecter automatiquement :
- Le langage : **Python**
- Le fichier de configuration : `sonar-project.properties` ✅
- Le fichier de coverage : `coverage.xml`

## Étape 4 : Récupérer le SONAR_TOKEN

Pour que GitHub Actions puisse envoyer les résultats à SonarCloud :

1. Dans SonarCloud, allez sur votre projet `bases_athle_scrapper`
2. Cliquez sur **"Administration"** (en haut à droite) > **"Analysis Method"**
3. Sélectionnez **"GitHub Actions"**
4. SonarCloud va afficher :
   - ✅ Le `SONAR_TOKEN` (format : `sqp_...`)
   - Instructions pour GitHub Actions

5. **Copiez le SONAR_TOKEN** (il ne sera affiché qu'une fois !)

## Étape 5 : Configurer le secret GitHub

1. Allez sur GitHub : `https://github.com/cmoron/bases_athle_scrapper/settings/secrets/actions`
2. Cliquez sur **"New repository secret"**
3. Configurez le secret :
   - **Name** : `SONAR_TOKEN`
   - **Value** : Collez le token copié à l'étape 4 (commence par `sqp_`)
4. Cliquez sur **"Add secret"**

## Étape 6 : Vérifier la configuration

### Vérifier le fichier `sonar-project.properties`

Le fichier doit contenir (déjà configuré ✅) :

```properties
sonar.projectKey=cmoron_bases_athle_scrapper
sonar.organization=cmoron
```

⚠️ **Important** : Si votre organisation SonarCloud a un nom différent de `cmoron`, modifiez la ligne `sonar.organization`.

### Vérifier le workflow GitHub Actions

Le fichier `.github/workflows/ci.yml` doit contenir (déjà configuré ✅) :

```yaml
- name: SonarCloud Scan
  uses: SonarSource/sonarcloud-github-action@master
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```

## Étape 7 : Lancer la première analyse

1. Faites un commit et push :
   ```bash
   git add .
   git commit -m "Configure SonarCloud analysis"
   git push
   ```

2. Vérifiez que la CI s'exécute correctement sur GitHub Actions :
   - Allez sur `https://github.com/cmoron/bases_athle_scrapper/actions`
   - Vérifiez que l'étape **"SonarCloud Scan"** passe avec succès

3. Une fois la CI terminée, retournez sur SonarCloud :
   - Vous devriez voir les premiers résultats d'analyse
   - Vérifiez le **Quality Gate** (Passed/Failed)
   - Consultez les **Bugs**, **Code Smells**, et **Coverage**

## Étape 8 : Vérifier les badges

Les badges dans le README devraient maintenant s'afficher correctement :

- [![Quality Gate](https://sonarcloud.io/api/project_badges/measure?project=cmoron_bases_athle_scrapper&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=cmoron_bases_athle_scrapper) **Quality Gate** : Passed/Failed
- [![Coverage](https://sonarcloud.io/api/project_badges/measure?project=cmoron_bases_athle_scrapper&metric=coverage)](https://sonarcloud.io/summary/new_code?id=cmoron_bases_athle_scrapper) **Coverage** : Pourcentage
- [![Code Smells](https://sonarcloud.io/api/project_badges/measure?project=cmoron_bases_athle_scrapper&metric=code_smells)](https://sonarcloud.io/summary/new_code?id=cmoron_bases_athle_scrapper) **Code Smells** : Nombre

## Métriques SonarCloud

### Quality Gate (Portail de Qualité)

Le Quality Gate détermine si votre code est **"production-ready"**. Par défaut, il vérifie :

- ✅ **Coverage** : >= 80% sur le nouveau code
- ✅ **Duplications** : < 3% sur le nouveau code
- ✅ **Maintainability Rating** : >= A
- ✅ **Reliability Rating** : >= A
- ✅ **Security Rating** : >= A

### Ratings (Notes A-E)

- **A** : Excellent (0 issues)
- **B** : Bon (issues mineures)
- **C** : Moyen (issues à surveiller)
- **D** : Mauvais (issues importantes)
- **E** : Critique (issues bloquantes)

### Code Smells (Mauvaises odeurs)

Problèmes de maintenabilité détectés :
- Fonctions trop complexes
- Code dupliqué
- Variables non utilisées
- Fonctions trop longues
- Trop de paramètres

## Dépannage

### Le coverage n'est pas uploadé

**Vérifiez :**
1. Le fichier `coverage.xml` est bien généré par pytest
2. Le secret `SONAR_TOKEN` est correctement configuré
3. Les logs GitHub Actions pour l'étape "SonarCloud Scan"

**Solution :**
```bash
# Vérifier localement que coverage.xml est généré
pytest --cov --cov-report=xml
ls -la coverage.xml
```

### Les badges ne s'affichent pas

**Causes possibles :**
- L'organisation ou le projectKey ne correspondent pas
- La première analyse n'est pas encore terminée
- Le repository est privé (SonarCloud gratuit = public uniquement)

**Solution :**
Vérifiez dans `sonar-project.properties` :
```properties
sonar.projectKey=cmoron_bases_athle_scrapper  # Doit correspondre exactement
sonar.organization=cmoron                      # Doit correspondre à votre org
```

### Erreur "Could not find a default branch"

SonarCloud ne trouve pas la branche principale.

**Solution :**
1. Dans SonarCloud, allez dans **Administration** > **Branches**
2. Configurez `main` comme branche principale
3. Relancez l'analyse

### Quality Gate échoue

C'est **normal au début** ! SonarCloud est exigeant.

**Problèmes courants :**
- Coverage < 80% → Ajouter plus de tests
- Code Smells → Simplifier le code complexe
- Duplications → Factoriser le code dupliqué

**Voir les détails :**
1. Cliquez sur le badge **Quality Gate**
2. Consultez les **New Code** issues
3. Corrigez les problèmes un par un

## Améliorer la note

### 1. Augmenter la couverture de tests

```bash
# Voir les parties non couvertes
make coverage
open htmlcov/index.html
```

**Objectif** : Passer de ~54% à 80%+

### 2. Réduire les Code Smells

```bash
# Voir les problèmes localement
make lint

# Problèmes courants :
# - Fonctions trop complexes → Découper
# - Code dupliqué → Factoriser
# - Variables non utilisées → Nettoyer
```

### 3. Simplifier la complexité

SonarCloud détecte la **complexité cyclomatique** :
- **1-10** : Simple ✅
- **11-20** : Modéré ⚠️
- **20+** : Complexe ❌

**Solution :**
- Découper les grosses fonctions
- Réduire les niveaux d'imbrication
- Extraire des fonctions helper

## Analyse locale (optionnel)

Vous pouvez installer SonarScanner localement pour analyser avant de push :

```bash
# Installer sonar-scanner
brew install sonar-scanner  # macOS
# ou télécharger depuis https://docs.sonarcloud.io/advanced-setup/ci-based-analysis/sonarscanner-cli/

# Analyser localement
sonar-scanner \
  -Dsonar.login=$SONAR_TOKEN

# Résultats disponibles sur SonarCloud après quelques secondes
```

## Ressources

- 📚 [Documentation SonarCloud](https://docs.sonarcloud.io/)
- 🐍 [Analyse Python](https://docs.sonarcloud.io/enriching-your-analysis/languages/python/)
- 🎯 [Quality Gates](https://docs.sonarcloud.io/improving-your-code-quality/quality-gates/)
- 🔧 [Configuration](https://docs.sonarcloud.io/advanced-setup/analysis-parameters/)
- 💬 [Community](https://community.sonarsource.com/)

## Comparaison avec d'autres outils

| Outil | Gratuit OS | Note globale | Couverture | Complexité | Sécurité | Learning curve |
|-------|------------|--------------|------------|------------|----------|----------------|
| **SonarCloud** | ✅ | Quality Gate | ✅ | ✅ | ✅ | Moyenne |
| CodeClimate | ✅ | A-F | ✅ | ✅ | ❌ | Simple |
| Codecov | ✅ | ❌ | ✅ | ❌ | ❌ | Simple |
| Codacy | ✅ | A-F | ✅ | ✅ | ⚠️ | Simple |

**Avantages de SonarCloud** :
- ✅ Analyse la plus complète (bugs, vulnérabilités, smells)
- ✅ Calcul de dette technique précis
- ✅ Interface puissante pour explorer les issues
- ✅ Utilisé par des millions de projets (standard de l'industrie)
- ✅ Excellent pour monter en compétence sur la qualité de code

## Support

En cas de problème :
1. Consultez les logs GitHub Actions
2. Vérifiez la configuration dans `sonar-project.properties`
3. Consultez la [documentation SonarCloud](https://docs.sonarcloud.io/)
4. Ouvrez une issue sur le repository

Bon scanning ! 🚀
