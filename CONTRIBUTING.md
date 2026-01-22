# Contributing to FastAPI Boilerplate

First off, thank you for considering contributing! It's people like you who make the open-source community such an amazing place.

## 🌟 How Can I Contribute?

### 🐛 Reporting Bugs
Before reporting, please check existing [GitHub Issues](https://github.com/gargashwani/fastapi_boilerplate/issues). If not found:
- Use the [Bug Report Template](https://github.com/gargashwani/fastapi_boilerplate/issues/new?template=bug_report.yml).
- Provide minimal reproduction steps.

### 💡 Suggesting Enhancements
- Use the [Feature Request Template](https://github.com/gargashwani/fastapi_boilerplate/issues/new?template=feature_request.yml).
- Discuss the idea first in [GitHub Discussions](https://github.com/gargashwani/fastapi_boilerplate/discussions).

### 🛠️ Pull Requests
1.  Fork the repository.
2.  Create a branch (`git checkout -b feature/amazing-feature`).
3.  Implement your changes.
4.  Run quality checks (see below).
5.  Open a Pull Request using our template.

---

## 💻 Development Setup

We use **uv** for dependency management.

```bash
# 1. Clone & Sync
git clone https://github.com/gargashwani/fastapi_boilerplate.git
cd fastapi_boilerplate
uv sync

# 2. Setup Environment
uv run python artisan install

# 3. Quality Checks (Mandatory)
uv run ruff check .
uv run mypy .
uv run pytest
```

---

## ✅ Coding Standards
- **Ruff**: Our primary linter and formatter.
- **Type Safety**: Mypy is enforced for all modules in `app/`.
- **Tests**: Every new feature or fix should include a corresponding test.
- **Commits**: Follow [Conventional Commits](https://www.conventionalcommits.org/).

## 🎯 Good First Issues
Look for the `good first issue` label in our issues list. These are well-defined tasks perfect for newcomers.

## ⚖️ License
By contributing, you agree that your contributions will be licensed under the MIT License.
