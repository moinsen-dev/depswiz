# Dart/Flutter Support

depswiz provides full support for Dart and Flutter projects using pub.

## Supported Files

### Manifest Files

| File | Description |
|------|-------------|
| `pubspec.yaml` | Pub package manifest |

### Lockfiles

| File | Description |
|------|-------------|
| `pubspec.lock` | Pub lockfile with resolved versions |

## Package Registry

depswiz queries [pub.dev](https://pub.dev) for package information:

```
GET https://pub.dev/api/packages/{package}
```

## Examples

### Check Dart/Flutter Dependencies

```bash
# Check current directory
depswiz check

# Check only Dart
depswiz check -l dart

# Check specific project
depswiz check /path/to/flutter/project
```

### Audit for Vulnerabilities

```bash
depswiz audit -l dart
```

Dart packages are checked against:
- [OSV](https://osv.dev/)
- [GitHub Advisory Database](https://github.com/advisories)

### Generate SBOM

```bash
depswiz sbom -l dart -o dart-sbom.json
```

## pubspec.yaml Format

### Basic Dependencies

```yaml
name: my_app
version: 1.0.0

environment:
  sdk: ">=3.0.0 <4.0.0"
  flutter: ">=3.16.0"

dependencies:
  flutter:
    sdk: flutter
  http: ^1.2.0
  provider: ^6.1.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  build_runner: ^2.4.0
```

### Dependency Types

```yaml
# Regular dependencies
dependencies:
  provider: ^6.1.0

# Development dependencies
dev_dependencies:
  build_runner: ^2.4.0

# Dependency overrides
dependency_overrides:
  http: ^1.2.0
```

### Version Constraints

| Constraint | Meaning |
|------------|---------|
| `^1.2.0` | >=1.2.0, <2.0.0 (caret syntax) |
| `>=1.2.0 <2.0.0` | Explicit range |
| `any` | Any version |
| `1.2.3` | Exact version |

## Flutter SDK Dependencies

depswiz correctly handles Flutter SDK dependencies:

```yaml
dependencies:
  flutter:
    sdk: flutter
  flutter_localizations:
    sdk: flutter
```

## Workspace Support

### Melos Workspaces

For monorepos using [Melos](https://melos.invertase.dev/):

```yaml
# melos.yaml
name: my_workspace

packages:
  - packages/*
  - apps/*
```

Scan all workspace members:

```bash
depswiz check --workspace
```

### Flutter Plugin Projects

depswiz handles federated plugins:

```yaml
# pubspec.yaml (plugin)
flutter:
  plugin:
    platforms:
      android:
        package: com.example.plugin
      ios:
        pluginClass: PluginClass
```

## Update Commands

depswiz generates pub update commands:

```bash
# Update specific package
dart pub upgrade package_name

# Update all packages
dart pub upgrade

# Flutter projects
flutter pub upgrade
```

## Common Issues

### SDK Version Constraints

Some updates require newer SDK versions:

```yaml
environment:
  sdk: ">=3.2.0 <4.0.0"  # Minimum SDK version
```

### Hosted Dependencies

For packages from custom servers:

```yaml
dependencies:
  my_package:
    hosted:
      name: my_package
      url: https://custom-pub-server.example.com
    version: ^1.0.0
```

### Git Dependencies

depswiz identifies git dependencies that may need updating:

```yaml
dependencies:
  my_package:
    git:
      url: https://github.com/user/repo.git
      ref: main
```

### Path Dependencies

Local path dependencies are identified but not checked against pub.dev:

```yaml
dependencies:
  my_local_package:
    path: ../my_local_package
```

## Flutter Version Checking

Use `depswiz tools` to check Flutter and Dart SDK versions:

```bash
depswiz tools -t dart -t flutter
```

Output:

```
┏━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ Tool      ┃ Installed  ┃ Latest     ┃ Status           ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ Dart      │ 3.2.0      │ 3.3.0      │ update available │
│ Flutter   │ 3.16.0     │ 3.19.0     │ update available │
└───────────┴────────────┴────────────┴──────────────────┘
```

## See Also

- [Commands Reference](../commands/index.md)
- [Configuration](../configuration.md)
- [pub.dev](https://pub.dev)
- [Dart Package Layout](https://dart.dev/tools/pub/package-layout)
- [Flutter Packages](https://docs.flutter.dev/packages-and-plugins/developing-packages)
